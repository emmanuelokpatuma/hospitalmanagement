# Python APIs - Add Prometheus Metrics Support

To enable Prometheus monitoring for your Python Flask/FastAPI services, add the following to your APIs:

## For Flask (Patient API & Appointment API)

### 1. Update requirements.txt

Add these lines to both `patient-api/requirements.txt` and `appointment-api/requirements.txt`:

```
prometheus-client==0.19.0
prometheus-flask-exporter==0.22.4
```

### 2. Update app.py

Add metrics support to your Flask application:

```python
from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)

# Add custom metrics (optional)
metrics.info('app_info', 'Application info', version='1.0.0')

# Your existing routes
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

@app.route('/metrics')
def metrics_endpoint():
    # This is automatically handled by PrometheusMetrics
    pass

# ... rest of your application code
```

### 3. Rebuild Images

After updating the code:

```bash
cd patient-api
docker build -t patient-api:latest .
kind load docker-image patient-api:latest --name hpm-cluster

cd ../appointment-api
docker build -t appointment-api:latest .
kind load docker-image appointment-api:latest --name hpm-cluster
```

## Available Metrics

The `prometheus-flask-exporter` automatically provides:

- `flask_http_request_duration_seconds` - Request latency
- `flask_http_request_total` - Total requests
- `flask_http_request_exceptions_total` - Failed requests
- `flask_exporter_info` - App info

## Testing Metrics

Once deployed, test the metrics endpoint:

```bash
# Port forward the service
kubectl port-forward -n hospital svc/hospital-patient-hpm 3000:3000

# Check metrics
curl http://localhost:3000/metrics
```

You should see Prometheus-formatted metrics like:

```
# HELP flask_http_request_duration_seconds Flask HTTP request duration in seconds
# TYPE flask_http_request_duration_seconds histogram
flask_http_request_duration_seconds_bucket{le="0.005",method="GET",path="/health",status="200"} 10.0
...
```
