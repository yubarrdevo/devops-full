#!/bin/bash

echo "==================================="
echo "Teste de Carga - Demo API"
echo "==================================="
echo ""

API_URL=${API_URL:-http://localhost:5000}
REQUESTS=${REQUESTS:-100}

echo "Configuração:"
echo "  API URL: $API_URL"
echo "  Total de requisições: $REQUESTS"
echo ""
echo "Gerando tráfego..."
echo ""

for i in $(seq 1 $REQUESTS); do
  # Requisições normais
  curl -s $API_URL/health > /dev/null &
  curl -s $API_URL/api/users > /dev/null &
  curl -s $API_URL/api/products > /dev/null &

  # Requisições com parâmetros
  USER_ID=$((1 + RANDOM % 3))
  curl -s $API_URL/api/users/$USER_ID > /dev/null &

  PRODUCT_ID=$((1 + RANDOM % 3))
  curl -s $API_URL/api/products/$PRODUCT_ID > /dev/null &

  # Criar pedidos
  curl -s -X POST $API_URL/api/order \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": $USER_ID, \"product_ids\": [1, 2]}" > /dev/null &

  # Algumas requisições lentas
  if [ $((i % 10)) -eq 0 ]; then
    curl -s $API_URL/api/slow > /dev/null &
  fi

  # Algumas requisições com erro
  if [ $((i % 20)) -eq 0 ]; then
    curl -s $API_URL/api/error > /dev/null 2>&1 &
  fi

  # Progresso
  if [ $((i % 25)) -eq 0 ]; then
    echo "  Progresso: $i/$REQUESTS requisições enviadas..."
  fi

  sleep 0.1
done

wait

echo ""
echo "==================================="
echo "Teste de carga concluído!"
echo "==================================="
echo ""
echo "Acesse as UIs para visualizar os resultados:"
echo "  - Grafana: http://localhost:3000"
echo "  - Prometheus: http://localhost:9090"
echo "  - Jaeger: http://localhost:16686"
echo ""
