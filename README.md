# DevOps Full Stack - Ambiente de Observabilidade

Stack completa para testes de observabilidade, monitoramento e APIs com aplicação real instrumentada.

## 🚀 Componentes da Stack

- **Demo API**: Aplicação REST em Python/Flask totalmente instrumentada
- **OpenTelemetry Collector**: Coleta centralizada de telemetria (traces, metrics, logs)
- **Prometheus**: Sistema de monitoramento e métricas
- **Grafana**: Plataforma de visualização e dashboards
- **Loki**: Sistema de agregação de logs
- **Jaeger**: Sistema de distributed tracing

## 📋 Pré-requisitos

- Docker
- Docker Compose
- Pelo menos 4GB de RAM disponível

## 🏃 Como Executar

### 1. Subir toda a stack

```bash
docker-compose up -d
```

### 2. Verificar se todos os serviços estão rodando

```bash
docker-compose ps
```

### 3. Acessar os serviços

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Demo API** | http://localhost:5000 | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger UI** | http://localhost:16686 | - |
| **Loki** | http://localhost:3100 | - |

## 🔧 Testando a API

### Endpoints Disponíveis

```bash
# Health check
curl http://localhost:5000/health

# Listar usuários
curl http://localhost:5000/api/users

# Obter usuário específico
curl http://localhost:5000/api/users/1

# Listar produtos
curl http://localhost:5000/api/products

# Obter produto específico
curl http://localhost:5000/api/products/1

# Criar pedido (POST)
curl -X POST http://localhost:5000/api/order \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "product_ids": [1, 2, 3]
  }'

# Endpoint lento (para testar performance)
curl http://localhost:5000/api/slow

# Endpoint com erro (para testar alertas)
curl http://localhost:5000/api/error
```

### Script de Teste de Carga

Crie um arquivo `load-test.sh` para gerar tráfego:

```bash
#!/bin/bash

echo "Gerando tráfego para a API..."

for i in {1..100}; do
  # Requisições normais
  curl -s http://localhost:5000/health > /dev/null &
  curl -s http://localhost:5000/api/users > /dev/null &
  curl -s http://localhost:5000/api/products > /dev/null &

  # Requisições com parâmetros
  USER_ID=$((1 + RANDOM % 3))
  curl -s http://localhost:5000/api/users/$USER_ID > /dev/null &

  PRODUCT_ID=$((1 + RANDOM % 3))
  curl -s http://localhost:5000/api/products/$PRODUCT_ID > /dev/null &

  # Criar pedidos
  curl -s -X POST http://localhost:5000/api/order \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": $USER_ID, \"product_ids\": [1, 2]}" > /dev/null &

  # Algumas requisições lentas
  if [ $((i % 10)) -eq 0 ]; then
    curl -s http://localhost:5000/api/slow > /dev/null &
  fi

  # Algumas requisições com erro
  if [ $((i % 20)) -eq 0 ]; then
    curl -s http://localhost:5000/api/error > /dev/null &
  fi

  sleep 0.1
done

wait
echo "Teste de carga concluído!"
```

Execute:
```bash
chmod +x load-test.sh
./load-test.sh
```

## 📊 Visualizando Métricas e Logs

### Grafana

1. Acesse http://localhost:3000
2. Login: `admin` / `admin`
3. Navegue até **Dashboards** → **Demo API Dashboard**

O dashboard mostra:
- Taxa de requisições
- Tempo médio de resposta
- Total de requisições por endpoint
- Requisições por status code

### Prometheus

1. Acesse http://localhost:9090
2. Experimente queries como:
   ```promql
   # Taxa de requisições
   rate(flask_http_request_total[1m])

   # Latência média
   flask_http_request_duration_seconds_sum / flask_http_request_duration_seconds_count

   # Total de requisições por endpoint
   sum by (path) (flask_http_request_total)
   ```

### Jaeger (Distributed Tracing)

1. Acesse http://localhost:16686
2. Selecione o serviço **demo-api**
3. Clique em **Find Traces**
4. Explore os traces para ver:
   - Tempo de cada operação
   - Chamadas em cascata
   - Spans individuais
   - Tags e logs

### Loki (Logs no Grafana)

1. No Grafana, vá para **Explore**
2. Selecione **Loki** como datasource
3. Use queries como:
   ```logql
   {service_name="demo-api"}
   {service_name="demo-api"} |= "error"
   {service_name="demo-api"} |= "order"
   ```

## 🔍 Explorando Observabilidade

### Correlação entre Traces e Logs

1. No Jaeger, encontre um trace interessante
2. Copie o Trace ID
3. No Grafana/Loki, busque:
   ```logql
   {service_name="demo-api"} |= "trace_id_aqui"
   ```

### Criando Alertas no Grafana

1. No dashboard, clique em qualquer painel
2. **Edit** → **Alert**
3. Configure condições (ex: latência > 500ms)
4. Salve o alerta

### Métricas Customizadas

A aplicação já exporta métricas customizadas:
- `api_requests_total`: Total de requisições
- `api_errors_total`: Total de erros

Veja no Prometheus:
```promql
rate(api_requests_total[1m])
api_errors_total
```

## 🛠️ Estrutura do Projeto

```
.
├── app/
│   ├── app.py              # Aplicação Flask instrumentada
│   ├── requirements.txt    # Dependências Python
│   └── Dockerfile         # Imagem da aplicação
├── config/
│   ├── grafana/
│   │   └── provisioning/
│   │       ├── datasources/     # Datasources automáticos
│   │       └── dashboards/      # Dashboards pré-configurados
│   ├── prometheus/
│   │   └── prometheus.yml       # Configuração do Prometheus
│   ├── loki/
│   │   └── loki-config.yaml     # Configuração do Loki
│   └── otel-collector/
│       └── otel-collector-config.yaml  # Configuração do OTEL
└── docker-compose.yml      # Orquestração de todos os serviços
```

## 🧪 Casos de Uso para Testes

### 1. Testar Alertas de Latência
```bash
# Gerar requisições lentas
for i in {1..10}; do curl http://localhost:5000/api/slow; done
```
Observe no Grafana o aumento da latência.

### 2. Testar Rastreamento de Erros
```bash
# Gerar erros
for i in {1..5}; do curl http://localhost:5000/api/error; done
```
Verifique os traces no Jaeger e logs no Loki.

### 3. Testar Correlação de Dados
1. Faça uma requisição de pedido
2. Copie o Trace ID do Jaeger
3. Busque os logs correspondentes no Loki
4. Veja as métricas no Prometheus

### 4. Simular Carga e Monitorar
```bash
./load-test.sh
```
Acompanhe em tempo real no Grafana:
- Taxa de requisições
- Distribuição por endpoint
- Erros e sucessos
- Latência percentis

## 🐛 Troubleshooting

### Serviços não sobem
```bash
# Ver logs de todos os serviços
docker-compose logs

# Ver logs de um serviço específico
docker-compose logs demo-api
docker-compose logs otel-collector
```

### Resetar tudo
```bash
# Parar e remover tudo
docker-compose down -v

# Subir novamente
docker-compose up -d
```

### Problemas com o OpenTelemetry
```bash
# Verificar se o OTEL Collector está recebendo dados
docker-compose logs otel-collector | grep -i "exporting"
```

## 📚 Recursos Adicionais

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [Jaeger Docs](https://www.jaegertracing.io/docs/)
- [Loki Docs](https://grafana.com/docs/loki/)

## 🎯 Próximos Passos

1. Adicionar mais endpoints na API
2. Implementar rate limiting
3. Adicionar autenticação
4. Criar mais dashboards customizados
5. Configurar alertas no Alertmanager
6. Adicionar testes automatizados
7. Implementar Service Mesh (Istio)

## 📝 Licença

Este projeto é de código aberto para fins educacionais e de testes.
