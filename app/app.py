from flask import Flask, jsonify, request
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from prometheus_flask_exporter import PrometheusMetrics
import logging
import time
import random
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurar OpenTelemetry
resource = Resource.create({
    "service.name": "demo-api",
    "service.version": "1.0.0",
    "deployment.environment": "local"
})

# Configurar Trace Provider
trace_provider = TracerProvider(resource=resource)
otlp_trace_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317"),
    insecure=True
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
trace.set_tracer_provider(trace_provider)
tracer = trace.get_tracer(__name__)

# Configurar Metrics Provider
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317"),
        insecure=True
    )
)
meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(meter_provider)
meter = metrics.get_meter(__name__)

# Criar métricas customizadas
request_counter = meter.create_counter(
    "api_requests_total",
    description="Total de requisições na API"
)

error_counter = meter.create_counter(
    "api_errors_total",
    description="Total de erros na API"
)

# Criar app Flask
app = Flask(__name__)

# Instrumentar Flask automaticamente
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Adicionar Prometheus metrics
prometheus_metrics = PrometheusMetrics(app)

# Simular um "banco de dados" em memória
users_db = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
]

products_db = [
    {"id": 1, "name": "Laptop", "price": 999.99},
    {"id": 2, "name": "Mouse", "price": 29.99},
    {"id": 3, "name": "Keyboard", "price": 79.99}
]


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    logger.info("Health check called")
    request_counter.add(1, {"endpoint": "/health", "method": "GET"})
    return jsonify({"status": "healthy", "service": "demo-api"}), 200


@app.route('/api/users', methods=['GET'])
def get_users():
    """Listar todos os usuários"""
    with tracer.start_as_current_span("get_users") as span:
        logger.info("Fetching all users")

        # Simular delay de processamento
        time.sleep(random.uniform(0.01, 0.1))

        span.set_attribute("user.count", len(users_db))
        request_counter.add(1, {"endpoint": "/api/users", "method": "GET"})

        return jsonify(users_db), 200


@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Obter usuário por ID"""
    with tracer.start_as_current_span("get_user") as span:
        logger.info(f"Fetching user with id: {user_id}")
        span.set_attribute("user.id", user_id)

        # Simular delay de processamento
        time.sleep(random.uniform(0.01, 0.05))

        user = next((u for u in users_db if u["id"] == user_id), None)

        if user:
            request_counter.add(1, {"endpoint": "/api/users/:id", "method": "GET", "status": "success"})
            return jsonify(user), 200
        else:
            logger.warning(f"User {user_id} not found")
            error_counter.add(1, {"endpoint": "/api/users/:id", "error": "not_found"})
            request_counter.add(1, {"endpoint": "/api/users/:id", "method": "GET", "status": "error"})
            return jsonify({"error": "User not found"}), 404


@app.route('/api/products', methods=['GET'])
def get_products():
    """Listar todos os produtos"""
    with tracer.start_as_current_span("get_products") as span:
        logger.info("Fetching all products")

        # Simular delay de processamento
        time.sleep(random.uniform(0.02, 0.15))

        span.set_attribute("product.count", len(products_db))
        request_counter.add(1, {"endpoint": "/api/products", "method": "GET"})

        return jsonify(products_db), 200


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Obter produto por ID"""
    with tracer.start_as_current_span("get_product") as span:
        logger.info(f"Fetching product with id: {product_id}")
        span.set_attribute("product.id", product_id)

        # Simular delay de processamento
        time.sleep(random.uniform(0.01, 0.05))

        product = next((p for p in products_db if p["id"] == product_id), None)

        if product:
            request_counter.add(1, {"endpoint": "/api/products/:id", "method": "GET", "status": "success"})
            return jsonify(product), 200
        else:
            logger.warning(f"Product {product_id} not found")
            error_counter.add(1, {"endpoint": "/api/products/:id", "error": "not_found"})
            request_counter.add(1, {"endpoint": "/api/products/:id", "method": "GET", "status": "error"})
            return jsonify({"error": "Product not found"}), 404


@app.route('/api/order', methods=['POST'])
def create_order():
    """Criar um novo pedido (endpoint mais complexo)"""
    with tracer.start_as_current_span("create_order") as span:
        data = request.get_json()
        logger.info(f"Creating order: {data}")

        if not data or 'user_id' not in data or 'product_ids' not in data:
            logger.error("Invalid order data")
            error_counter.add(1, {"endpoint": "/api/order", "error": "invalid_data"})
            return jsonify({"error": "Invalid order data"}), 400

        user_id = data['user_id']
        product_ids = data['product_ids']

        span.set_attribute("order.user_id", user_id)
        span.set_attribute("order.product_count", len(product_ids))

        # Verificar se o usuário existe
        with tracer.start_as_current_span("validate_user"):
            time.sleep(random.uniform(0.01, 0.03))
            user = next((u for u in users_db if u["id"] == user_id), None)
            if not user:
                logger.error(f"User {user_id} not found")
                error_counter.add(1, {"endpoint": "/api/order", "error": "user_not_found"})
                return jsonify({"error": "User not found"}), 404

        # Verificar produtos e calcular total
        with tracer.start_as_current_span("calculate_total"):
            time.sleep(random.uniform(0.02, 0.05))
            total = 0
            order_items = []
            for pid in product_ids:
                product = next((p for p in products_db if p["id"] == pid), None)
                if product:
                    total += product['price']
                    order_items.append(product)
                else:
                    logger.warning(f"Product {pid} not found")

        # Simular processamento de pagamento
        with tracer.start_as_current_span("process_payment") as payment_span:
            time.sleep(random.uniform(0.1, 0.3))
            payment_span.set_attribute("payment.amount", total)
            payment_span.set_attribute("payment.status", "success")

        order = {
            "order_id": random.randint(1000, 9999),
            "user": user,
            "items": order_items,
            "total": total,
            "status": "completed"
        }

        logger.info(f"Order created successfully: {order['order_id']}")
        request_counter.add(1, {"endpoint": "/api/order", "method": "POST", "status": "success"})

        return jsonify(order), 201


@app.route('/api/slow', methods=['GET'])
def slow_endpoint():
    """Endpoint lento para testar timeouts e performance"""
    with tracer.start_as_current_span("slow_endpoint") as span:
        logger.info("Slow endpoint called")
        delay = random.uniform(1, 3)
        span.set_attribute("delay.seconds", delay)
        time.sleep(delay)
        request_counter.add(1, {"endpoint": "/api/slow", "method": "GET"})
        return jsonify({"message": "This was slow!", "delay": delay}), 200


@app.route('/api/error', methods=['GET'])
def error_endpoint():
    """Endpoint que retorna erro 500 propositalmente"""
    logger.error("Error endpoint called - throwing exception")
    error_counter.add(1, {"endpoint": "/api/error", "error": "intentional"})
    raise Exception("This is an intentional error for testing!")


@app.errorhandler(Exception)
def handle_exception(e):
    """Handler global de exceções"""
    logger.exception("Unhandled exception occurred")
    error_counter.add(1, {"error": "unhandled_exception"})
    return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Demo API...")
    app.run(host='0.0.0.0', port=5000, debug=False)
