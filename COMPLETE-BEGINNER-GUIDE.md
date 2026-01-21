# Complete Beginner's Guide to Your Hospital Management System
## Understanding Everything We Built Today

> **This guide explains every component, file, command, and how they all connect together**

---

## 🎯 THE BIG PICTURE - What Did We Build?

Imagine you're building a house with security cameras, electricity monitoring, and a management system. Here's what we built:

1. **Your Applications** (The House) - Patient API, Appointment API, Frontend
2. **Kubernetes** (The Neighborhood) - Where your applications live
3. **Monitoring Tools** (Electricity Meters & Cameras):
   - **Prometheus** - Collects numbers (CPU, memory usage)
   - **Grafana** - Shows pretty graphs of those numbers
   - **Elasticsearch** - Stores application logs (text messages from apps)
   - **Kibana** - Lets you search and read those logs
4. **ArgoCD** (The Automated Manager) - Watches GitHub and auto-deploys changes
5. **Ingress Controller** (The Front Door) - Routes external traffic to services

---

## 📁 DIRECTORY STRUCTURE - What's Where and Why

```
/home/emmanuel/Desktop/hospitalmanagement/
│
├── patient-api/                    ← YOUR APPLICATION CODE (Level 1)
│   ├── app.py                      ← Python code for patient API
│   ├── Dockerfile                  ← Instructions to build Docker image
│   └── requirements.txt            ← Python dependencies
│
├── appointment-api/                ← YOUR APPLICATION CODE (Level 1)
│   ├── app.py                      ← Python code for appointment API
│   ├── Dockerfile                  ← Instructions to build Docker image
│   └── requirements.txt            ← Python dependencies
│
├── hospital-frontend/              ← YOUR FRONTEND APPLICATION (Level 1)
│   ├── src/                        ← Angular application code
│   ├── Dockerfile                  ← Instructions to build frontend image
│   └── package.json                ← JavaScript dependencies
│
├── hpm/                            ← KUBERNETES DEPLOYMENT CONFIGS (Level 2)
│   ├── Chart.yaml                  ← Helm chart metadata
│   ├── values-patient.yaml         ← Patient API configuration
│   ├── values-appointment.yaml     ← Appointment API configuration
│   ├── values-ui.yaml              ← Frontend configuration
│   └── templates/                  ← Kubernetes template files
│       ├── deployment.yaml         ← How to run your app in K8s
│       ├── service.yaml            ← How to access your app
│       ├── ingress.yaml            ← External access rules
│       └── sqlserver.yaml          ← Database deployment
│
├── k8s-manifests/                  ← MONITORING INFRASTRUCTURE (Level 3)
│   ├── monitoring-ingress.yaml     ← External access for Grafana/Prometheus
│   └── filebeat-values.yaml        ← Log shipping configuration
│
├── pulumi/                         ← CLOUD INFRASTRUCTURE CODE (Level 0)
│   ├── __main__.py                 ← Creates GCP cluster, networking
│   ├── apps.py                     ← Deploys apps to cluster
│   └── monitoring.py               ← Deploys monitoring stack
│
├── argocd-app.yaml                 ← GITOPS CONFIGURATION (Level 4)
│
└── Scripts (for automation):
    ├── setup-gcp-pulumi.sh         ← Install Pulumi and setup GCP
    ├── deploy-to-gcp.sh            ← Deploy everything to GCP
    ├── build-and-load-images.sh    ← Build Docker images locally
    └── import-grafana-dashboards.sh ← Load monitoring dashboards
```

### **Why These Levels?**

- **Level 0 (pulumi/)**: Creates the foundation - the cloud, network, cluster
- **Level 1 (app directories)**: Your actual application code
- **Level 2 (hpm/)**: Instructions on HOW to deploy your apps in Kubernetes
- **Level 3 (k8s-manifests/)**: Monitoring infrastructure configuration
- **Level 4 (argocd-app.yaml)**: Automated deployment management

---

## 🔍 UNDERSTANDING YOUR APPLICATION CODE

### **patient-api/app.py** - The Patient API

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import pyodbc
import os

app = Flask(__name__)
CORS(app)
```

**What this does:**
- `Flask` - A Python web framework (like a waiter taking orders)
- `CORS` - Allows frontend (Angular) to talk to this API from different domain
- `pyodbc` - Connects to SQL Server database
- `os` - Reads environment variables (configuration)

```python
DB_CONFIG = {
    'server': os.environ.get('DB_SERVER', 'sqlserver'),
    'database': 'hospital',
    'username': 'sa',
    'password': 'YourStrong!Passw0rd',
    'driver': '{ODBC Driver 18 for SQL Server}'
}
```

**What this does:**
- `os.environ.get('DB_SERVER', 'sqlserver')` - Reads database server name from environment variable
- If `DB_SERVER` variable exists, use that; otherwise use `'sqlserver'`
- In Kubernetes, we SET this variable in `values-patient.yaml`

```python
@app.route('/patients', methods=['GET'])
def get_patients():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patients")
        patients = cursor.fetchall()
        result = [{'id': row[0], 'name': row[1], 'age': row[2]} for row in patients]
    return jsonify(result)
```

**What this does:**
- `@app.route('/patients')` - When someone visits `http://your-api/patients`, run this function
- Connects to database, gets all patients, converts to JSON, returns it

```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200
```

**What this does:**
- Kubernetes asks "Are you alive?" by calling `/health`
- If it gets `{"status": "healthy"}`, it knows the app is working
- If it doesn't respond, Kubernetes restarts the pod

---

## 🐳 UNDERSTANDING DOCKER

### **patient-api/Dockerfile**

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y curl gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["python", "app.py"]
```

**What this does (line by line):**

1. `FROM python:3.9-slim` - Start with a lightweight Python environment
2. `WORKDIR /app` - Create and enter `/app` directory inside container
3. `COPY requirements.txt .` - Copy your dependencies list into container
4. `RUN apt-get install... msodbcsql18` - Install Microsoft SQL Server driver
5. `RUN pip install -r requirements.txt` - Install Python packages (Flask, pyodbc)
6. `COPY . .` - Copy all your application code into container
7. `EXPOSE 3000` - Tell Docker this app listens on port 3000
8. `CMD ["python", "app.py"]` - When container starts, run `python app.py`

**The Build Command We Ran:**
```bash
docker build -t gcr.io/charged-thought-485008-q7/patient-api:v3 .
```

- `docker build` - Build an image
- `-t gcr.io/.../patient-api:v3` - Tag it with this name
- `gcr.io` - Google Container Registry
- `v3` - Version 3 (we had v1, v2 earlier with bugs)
- `.` - Use Dockerfile in current directory

**The Push Command We Ran:**
```bash
docker push gcr.io/charged-thought-485008-q7/patient-api:v3
```

- Uploads the image to Google's container registry
- Now Kubernetes can download and run it

---

## ☸️ UNDERSTANDING KUBERNETES (K8S)

### **What is Kubernetes?**

Think of Kubernetes as a smart robot manager:
- You tell it: "I want 3 copies of patient-api running"
- It makes sure 3 are always running
- If one crashes, it automatically starts a new one
- If you update your code, it smoothly replaces old ones with new ones

### **Key Kubernetes Concepts:**

#### **1. Pod** 
A pod is like a box containing your Docker container
```
┌─────────────┐
│    POD      │
│ ┌─────────┐ │
│ │Container│ │  ← Your patient-api running here
│ │patient- │ │
│ │api:v3   │ │
│ └─────────┘ │
└─────────────┘
```

#### **2. Deployment**
Manages multiple pods
```
Deployment: "I want 2 patient-api pods"
    ↓
┌─────────────┐  ┌─────────────┐
│  Pod #1     │  │  Pod #2     │
│  patient-api│  │  patient-api│
└─────────────┘  └─────────────┘
```

#### **3. Service**
Gives a stable address to access pods
```
User → Service (hospital-patient-hpm:3000)
           ↓
       Load balances to:
       ↓              ↓
    Pod #1        Pod #2
```

#### **4. Namespace**
Like folders to organize things
```
Kubernetes Cluster
├── hospital (namespace)      ← Your apps live here
│   ├── patient-api pods
│   ├── appointment-api pods
│   └── sqlserver pod
├── monitoring (namespace)    ← Monitoring tools here
│   ├── prometheus pod
│   └── grafana pod
├── logging (namespace)       ← Logging tools here
│   ├── elasticsearch pod
│   └── kibana pod
└── argocd (namespace)        ← GitOps tool here
    └── argocd pods
```

---

## 📊 HELM - The Kubernetes Package Manager

### **What is Helm?**

Instead of writing 10 different YAML files for one app, Helm lets you use templates.

### **hpm/values-patient.yaml** - Configuration

```yaml
image:
  repository: gcr.io/charged-thought-485008-q7/patient-api
  tag: v3
  pullPolicy: IfNotPresent
```

**What this means:**
- Use Docker image from Google Container Registry
- Use version `v3`
- `IfNotPresent` - Only download if not already on the server (saves bandwidth)

```yaml
service:
  port: 3000
  type: ClusterIP
```

**What this means:**
- Your app listens on port 3000
- `ClusterIP` - Only accessible from INSIDE the Kubernetes cluster
- Not exposed to the internet directly (we use Ingress for that)

```yaml
env:
  - name: DB_SERVER
    value: hospital-ui-hpm-sqlserver
```

**What this means:**
- Set environment variable `DB_SERVER=hospital-ui-hpm-sqlserver`
- Remember in `app.py`: `os.environ.get('DB_SERVER', 'sqlserver')`
- This tells patient-api where the database is!
- `hospital-ui-hpm-sqlserver` is the Kubernetes Service name for SQL Server

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 30
  periodSeconds: 10
```

**What this means:**
- Every 10 seconds, Kubernetes calls `http://patient-api:3000/health`
- If it fails 3 times, Kubernetes kills and restarts the pod
- Wait 30 seconds after pod starts before checking (gives app time to initialize)

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 3000
  initialDelaySeconds: 10
  periodSeconds: 5
```

**What this means:**
- Every 5 seconds, check if app is ready to receive traffic
- If `/health` fails, Kubernetes stops sending traffic to this pod
- Once it passes again, traffic resumes

### **hpm/templates/deployment.yaml** - Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "hpm.fullname" . }}
```

**What this means:**
- `{{ include "hpm.fullname" . }}` - This is a Helm template variable
- Gets replaced with actual name when you install
- Example: becomes `hospital-patient-hpm`

```yaml
spec:
  replicas: {{ .Values.replicaCount }}
```

**What this means:**
- `{{ .Values.replicaCount }}` - Reads from `values-patient.yaml`
- If `replicaCount: 1`, creates 1 pod
- If `replicaCount: 3`, creates 3 pods

```yaml
containers:
  - name: {{ .Chart.Name }}
    image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
```

**What this means:**
- `{{ .Values.image.repository }}` → `gcr.io/.../patient-api`
- `{{ .Values.image.tag }}` → `v3`
- Final: `gcr.io/.../patient-api:v3`

**Command We Ran to Deploy:**
```bash
helm install hospital-patient hpm/ -f hpm/values-patient.yaml -n hospital
```

- `helm install` - Install a Helm chart
- `hospital-patient` - Name this release "hospital-patient"
- `hpm/` - Use templates from `hpm/` folder
- `-f hpm/values-patient.yaml` - Use these values
- `-n hospital` - Install in "hospital" namespace

---

## 🌐 INGRESS - The Front Door

### **What is Ingress?**

Imagine your Kubernetes cluster is an apartment building:
- Each service is an apartment
- Ingress is the front desk that routes visitors

```
Internet User types: http://grafana.34.173.19.139.nip.io
                              ↓
                      ┌───────────────┐
                      │ Nginx Ingress │ ← Front desk
                      │  Controller   │
                      └───────────────┘
                              ↓
              "You want grafana? Go to apartment 'prometheus-grafana' door 80"
                              ↓
                      ┌───────────────┐
                      │Service:       │
                      │prometheus-    │
                      │grafana        │
                      │Port: 80       │
                      └───────────────┘
                              ↓
                      ┌───────────────┐
                      │  Grafana Pod  │
                      └───────────────┘
```

### **k8s-manifests/monitoring-ingress.yaml**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana
  namespace: monitoring
```

**What this means:**
- Create an Ingress resource named "grafana"
- Put it in the "monitoring" namespace (same as Grafana service)

```yaml
spec:
  ingressClassName: nginx
  rules:
  - host: grafana.34.173.19.139.nip.io
```

**What this means:**
- Use the nginx ingress controller
- When someone visits `grafana.34.173.19.139.nip.io`, apply these rules
- `34.173.19.139` was our LoadBalancer's external IP
- `nip.io` is a free wildcard DNS service that resolves to the IP

```yaml
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prometheus-grafana
            port:
              number: 80
```

**What this means:**
- For ANY path starting with `/` (so everything)
- Send traffic to service named `prometheus-grafana`
- On port `80`

**Command We Ran:**
```bash
kubectl apply -f k8s-manifests/monitoring-ingress.yaml
```

- `kubectl apply` - Create or update resources
- `-f monitoring-ingress.yaml` - From this file

---

## 📈 MONITORING STACK - Understanding the Flow

### **The Complete Monitoring Flow:**

```
┌──────────────────────────────────────────────────────────────┐
│                    YOUR APPLICATIONS                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Patient API  │  │Appointment   │  │  Frontend    │      │
│  │    Pod       │  │   API Pod    │  │    Pod       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         │ Exposes          │ Exposes          │ Exposes      │
│         ↓ Metrics          ↓ Metrics          ↓ Metrics      │
│    /metrics endpoint  /metrics endpoint  /metrics endpoint   │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          │    ┌─────────────┴──────────────────┘
          │    │
          ↓    ↓
    ┌─────────────────┐
    │   PROMETHEUS    │ ← Scrapes (collects) metrics every 15s
    │   (Collector)   │
    └─────────────────┘
            │
            │ Stores metrics in time-series database
            ↓
    ┌─────────────────┐
    │   PROMETHEUS    │
    │    Database     │
    └─────────────────┘
            │
            │ Queried by
            ↓
    ┌─────────────────┐
    │    GRAFANA      │ ← You view graphs here!
    │  (Visualization)│
    └─────────────────┘
```

### **Prometheus - The Metrics Collector**

**What Prometheus Does:**

1. **Discovers targets** - Finds all pods with annotation:
   ```yaml
   podAnnotations:
     prometheus.io/scrape: "true"
     prometheus.io/port: "3000"
     prometheus.io/path: "/metrics"
   ```

2. **Scrapes metrics** - Every 15 seconds, calls `http://pod-ip:3000/metrics`

3. **Stores metrics** - Keeps time-series data (values over time)
   ```
   cpu_usage{pod="patient-api"} 45% at 10:00:00
   cpu_usage{pod="patient-api"} 47% at 10:00:15
   cpu_usage{pod="patient-api"} 43% at 10:00:30
   ```

**Command We Ran to Install:**
```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

**What each part means:**
- `helm install prometheus` - Install and name it "prometheus"
- `prometheus-community/kube-prometheus-stack` - Use this Helm chart
- `--namespace monitoring` - Put it in "monitoring" namespace
- `--create-namespace` - Create namespace if it doesn't exist
- `--set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false` - Find ALL ServiceMonitors, not just ones with specific labels

**What it installed:**
- Prometheus server (collects metrics)
- Grafana (visualizes metrics)
- AlertManager (sends alerts)
- Node Exporter (collects server metrics)
- Kube State Metrics (collects Kubernetes object metrics)

### **Grafana - The Dashboard**

**What Grafana Does:**

1. **Connects to Prometheus** - Uses it as a data source
2. **Queries data** - Example query:
   ```
   rate(http_requests_total[5m])
   ```
   Means: "Show me HTTP requests per second over last 5 minutes"

3. **Displays graphs** - Beautiful visualizations

**How to Query in Grafana:**

When you're in Grafana dashboard, you write PromQL (Prometheus Query Language):

```promql
# CPU usage of patient-api pods
container_cpu_usage_seconds_total{pod=~"hospital-patient.*"}

# Memory usage
container_memory_usage_bytes{pod=~"hospital-patient.*"}

# Number of running pods
count(kube_pod_info{namespace="hospital"})
```

**Accessing Grafana:**
```
http://grafana.34.173.19.139.nip.io
```

Flow:
```
Your Browser → Ingress Controller → Grafana Service → Grafana Pod
```

**Command to Get Password:**
```bash
kubectl get secret prometheus-grafana \
  -n monitoring \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

**What this does:**
- `kubectl get secret` - Retrieve a secret (encrypted config)
- `prometheus-grafana` - Name of the secret
- `-o jsonpath="{.data.admin-password}"` - Extract just the password field
- `| base64 --decode` - Decode from Base64 encoding

---

## 📝 LOGGING STACK - Understanding the Flow

### **The Complete Logging Flow:**

```
┌──────────────────────────────────────────────────────────────┐
│                    YOUR APPLICATIONS                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Patient API  │  │Appointment   │  │  Frontend    │      │
│  │    Pod       │  │   API Pod    │  │    Pod       │      │
│  │              │  │              │  │              │      │
│  │  Writes to   │  │  Writes to   │  │  Writes to   │      │
│  │  stdout/     │  │  stdout/     │  │  stdout/     │      │
│  │  stderr      │  │  stderr      │  │  stderr      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          │   Container logs stored by Kubernetes in:
          │   /var/log/containers/*.log
          │                  │                  │
          └──────────┬───────┴──────────────────┘
                     │
                     ↓
              ┌─────────────┐
              │  FILEBEAT   │ ← Reads log files
              │ (Shipper)   │
              └─────────────┘
                     │
                     │ Ships logs to
                     ↓
              ┌─────────────┐
              │ELASTICSEARCH│ ← Stores & indexes logs
              │ (Database)  │
              └─────────────┘
                     │
                     │ Queried by
                     ↓
              ┌─────────────┐
              │   KIBANA    │ ← You search logs here!
              │ (Web UI)    │
              └─────────────┘
```

### **Elasticsearch - The Log Database**

**What Elasticsearch Does:**

1. **Receives logs** from Filebeat
2. **Indexes them** - Creates searchable index
3. **Stores them** - Keeps logs for searching

**Example Log Document:**
```json
{
  "timestamp": "2026-01-21T10:30:45.123Z",
  "kubernetes": {
    "namespace": "hospital",
    "pod": "hospital-patient-hpm-7d8f9c-xyz",
    "container": "patient-api"
  },
  "message": "GET /patients - 200 OK",
  "level": "info"
}
```

**Command We Ran:**
```bash
helm install elasticsearch elastic/elasticsearch \
  --namespace logging \
  --create-namespace \
  --set replicas=1 \
  --set persistence.enabled=false
```

**What this means:**
- `--set replicas=1` - Run 1 copy (normally you'd run 3 for production)
- `--set persistence.enabled=false` - Don't save data permanently (for demo)

### **Filebeat - The Log Shipper**

**What Filebeat Does:**

1. **Finds log files** - Scans `/var/log/containers/`
2. **Reads new lines** - Tails files like `tail -f`
3. **Parses logs** - Adds Kubernetes metadata (pod name, namespace)
4. **Ships to Elasticsearch** - Sends logs via HTTPS

**k8s-manifests/filebeat-values.yaml:**

```yaml
daemonSet:
  enabled: true
```

**What this means:**
- `DaemonSet` - Run one Filebeat pod on EVERY node in cluster
- If you have 3 nodes, you get 3 Filebeat pods
- Each monitors logs on its node

```yaml
filebeatConfig:
  filebeat.yml: |
    filebeat.inputs:
    - type: container
      paths:
        - /var/log/containers/*.log
```

**What this means:**
- `type: container` - Read container logs
- `paths: /var/log/containers/*.log` - Read all `.log` files in this directory

```yaml
    processors:
    - add_kubernetes_metadata:
        host: ${NODE_NAME}
        matchers:
        - logs_path:
            logs_path: "/var/log/containers/"
```

**What this means:**
- `add_kubernetes_metadata` - Add pod name, namespace, labels to each log
- Makes logs searchable by pod/namespace in Kibana

```yaml
    output.elasticsearch:
      host: '${NODE_NAME}'
      hosts: '["https://elasticsearch-master:9200"]'
      protocol: "https"
      ssl.verification_mode: none
```

**What this means:**
- Send logs to `https://elasticsearch-master:9200`
- `elasticsearch-master` is the Kubernetes Service name
- `ssl.verification_mode: none` - Don't verify SSL certificate (for demo)

**Command We Ran:**
```bash
helm install filebeat elastic/filebeat \
  --namespace logging \
  -f k8s-manifests/filebeat-values.yaml
```

### **Kibana - The Log Search UI**

**What Kibana Does:**

1. **Connects to Elasticsearch** - Reads from it
2. **Provides search** - Like Google for your logs
3. **Shows visualizations** - Charts and graphs

**How to Search in Kibana:**

1. Go to `http://kibana.34.173.19.139.nip.io`
2. Click "Discover"
3. Search examples:
   ```
   kubernetes.namespace: "hospital"
   kubernetes.pod: "hospital-patient-*"
   message: "error"
   message: "GET /patients"
   ```

**Accessing Kibana:**
```
Your Browser → Ingress Controller → Kibana Service (port 5601) → Kibana Pod
```

---

## 🔄 ARGOCD - GitOps (Automated Deployment)

### **What is GitOps?**

Imagine you have a robot that:
1. Watches your GitHub repository
2. Sees when you push new code
3. Automatically deploys it to Kubernetes

That's ArgoCD!

### **Traditional Deployment:**
```
You: Run helm install manually
You: Run kubectl apply manually
You: Run docker build and push manually
```

### **GitOps Deployment:**
```
You: Push code to GitHub
ArgoCD: "I see new code! Let me deploy it automatically"
ArgoCD: Builds, deploys, monitors
```

### **argocd-app.yaml - The Configuration**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: hospital-patient-api
  namespace: argocd
```

**What this means:**
- Create an ArgoCD Application
- Name it `hospital-patient-api`
- Must be in `argocd` namespace (that's where ArgoCD lives)

```yaml
spec:
  project: default
  source:
    repoURL: https://github.com/emmanuelokpatuma/hospitalmanagement
    targetRevision: main
    path: hpm
```

**What this means:**
- Watch GitHub repository: `https://github.com/emmanuelokpatuma/hospitalmanagement`
- Watch the `main` branch
- Look for Helm chart in the `hpm/` directory

```yaml
    helm:
      releaseName: hospital-patient
      valueFiles:
      - values-patient.yaml
```

**What this means:**
- Install using Helm
- Name the release `hospital-patient`
- Use `values-patient.yaml` for configuration

```yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: hospital
```

**What this means:**
- Deploy to this Kubernetes cluster (`kubernetes.default.svc` = current cluster)
- Put it in `hospital` namespace

```yaml
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**What this means:**
- `automated` - Auto-deploy when GitHub changes
- `prune: true` - Delete resources that are removed from Git
- `selfHeal: true` - If someone manually changes something in Kubernetes, change it back to match Git

**The Flow:**

```
1. You push to GitHub
   ↓
2. ArgoCD polls GitHub every 3 minutes
   ↓
3. "New commit detected!"
   ↓
4. ArgoCD runs: helm install hospital-patient hpm/ -f values-patient.yaml
   ↓
5. New pods are deployed
   ↓
6. Old pods are terminated
   ↓
7. Your app is updated! No manual work!
```

**Command We Ran:**
```bash
kubectl apply -f argocd-app.yaml
```

This tells ArgoCD: "Start watching this repository and auto-deploy!"

**Accessing ArgoCD:**
```
http://argocd.34.173.19.139.nip.io
```

**Getting ArgoCD Password:**
```bash
kubectl get secret argocd-initial-admin-secret \
  -n argocd \
  -o jsonpath="{.data.password}" | base64 --decode
```

---

## 🗂️ COMPLETE COMMAND TIMELINE - Everything We Ran Today

### **Phase 1: Setup GCP and Pulumi (Infrastructure Foundation)**

```bash
# 1. Install Pulumi
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin
```
**Why:** Pulumi is Infrastructure as Code - lets you create cloud resources with Python

```bash
# 2. Configure GCP project
gcloud config set project charged-thought-485008-q7
```
**Why:** Tell Google Cloud which project to use

```bash
# 3. Initialize Pulumi project
cd pulumi/
pulumi login --local
pulumi stack init dev
```
**Why:** Create a Pulumi "stack" (environment) named "dev"

```bash
# 4. Deploy GKE cluster
pulumi up --yes
```
**Why:** Creates:
- VPC network (virtual private cloud)
- Subnet (network segment)
- GKE cluster with 3 nodes
- Takes ~10 minutes!

**What happened:** Google Cloud now has a Kubernetes cluster running!

---

### **Phase 2: Build and Push Docker Images**

```bash
# 5. Configure Docker for GCR
gcloud auth configure-docker gcr.io
```
**Why:** Lets Docker push images to Google Container Registry

```bash
# 6. Build patient-api image
cd /home/emmanuel/Desktop/hospitalmanagement/patient-api
docker build -t gcr.io/charged-thought-485008-q7/patient-api:v3 .
```
**Why:** Creates a Docker image with all dependencies and your Python code

```bash
# 7. Push patient-api image
docker push gcr.io/charged-thought-485008-q7/patient-api:v3
```
**Why:** Uploads image to Google so Kubernetes can download it

```bash
# 8-9. Same for appointment-api
docker build -t gcr.io/charged-thought-485008-q7/appointment-api:v3 .
docker push gcr.io/charged-thought-485008-q7/appointment-api:v3
```

```bash
# 10-11. Same for frontend
docker build -t gcr.io/charged-thought-485008-q7/hospital-frontend:latest .
docker push gcr.io/charged-thought-485008-q7/hospital-frontend:latest
```

**What happened:** All 3 application images are now in Google Container Registry!

---

### **Phase 3: Setup Kubernetes Access**

```bash
# 12. Get cluster credentials
gcloud container clusters get-credentials hospital-gke \
  --zone us-central1-a
```
**Why:** Downloads credentials so `kubectl` can talk to your cluster

```bash
# 13. Verify connection
kubectl get nodes
```
**Why:** Check that cluster has 3 nodes running

**Output you saw:**
```
NAME                                        STATUS   ROLES    AGE
gke-hospital-gke-hospital-pool-123-abc      Ready    <none>   10m
gke-hospital-gke-hospital-pool-123-def      Ready    <none>   10m
gke-hospital-gke-hospital-pool-123-ghi      Ready    <none>   10m
```

---

### **Phase 4: Deploy Applications**

```bash
# 14. Create hospital namespace
kubectl create namespace hospital
```
**Why:** Logical grouping for your apps

```bash
# 15. Deploy patient API
helm install hospital-patient hpm/ \
  -f hpm/values-patient.yaml \
  -n hospital
```
**Why:** Deploys patient-api pods, service, and creates SQL Server

```bash
# 16. Deploy appointment API
helm install hospital-appointment hpm/ \
  -f hpm/values-appointment.yaml \
  -n hospital
```

```bash
# 17. Deploy frontend
helm install hospital-ui hpm/ \
  -f hpm/values-ui.yaml \
  -n hospital
```

**What happened:** Your 3 applications + SQL Server are now running in Kubernetes!

```bash
# 18. Check pods
kubectl get pods -n hospital
```

**Output:**
```
NAME                                    READY   STATUS    RESTARTS
hospital-patient-hpm-7d8f9c-xyz         1/1     Running   0
hospital-appointment-hpm-8e9g0d-abc     1/1     Running   0
hospital-ui-hpm-9f0h1e-def              1/1     Running   0
hospital-ui-hpm-sqlserver-0             1/1     Running   0
```

---

### **Phase 5: Create Database**

```bash
# 19. Connect to SQL Server pod
kubectl exec -it hospital-ui-hpm-sqlserver-0 -n hospital -- /bin/bash
```
**Why:** Open a terminal inside the SQL Server container

```bash
# 20. Create database (inside the pod)
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YourStrong!Passw0rd' -C -Q "CREATE DATABASE hospital"
```
**Why:** Your apps need a database named "hospital"

```bash
# 21. Verify database exists
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YourStrong!Passw0rd' -C -Q "SELECT name FROM sys.databases"
```

**What happened:** Database is created, apps can now store data!

---

### **Phase 6: Install Ingress Controller**

```bash
# 22. Install nginx ingress
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```
**Why:** This creates a public IP address that routes traffic to your apps

```bash
# 23. Wait for external IP
kubectl get svc -n ingress-nginx ingress-nginx-controller -w
```

**Output after ~2 minutes:**
```
NAME                       TYPE           EXTERNAL-IP      PORT(S)
ingress-nginx-controller   LoadBalancer   34.173.19.139    80:30123/TCP,443:30456/TCP
```

**What happened:** Google Cloud created a LoadBalancer with IP `34.173.19.139`!

---

### **Phase 7: Install Monitoring (Prometheus + Grafana)**

```bash
# 24. Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```
**Why:** Download the prometheus helm chart

```bash
# 25. Install Prometheus + Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```
**Why:** Deploys complete monitoring stack

**What it installed:**
- Prometheus (metrics collector)
- Grafana (visualization)
- AlertManager (alerting)
- Node Exporter (server metrics)
- Kube State Metrics (Kubernetes metrics)

```bash
# 26. Check monitoring pods
kubectl get pods -n monitoring
```

**Output:**
```
NAME                                                   READY   STATUS
prometheus-kube-prometheus-operator-7b8c9d-xyz         1/1     Running
prometheus-prometheus-kube-prometheus-prometheus-0     2/2     Running
prometheus-grafana-8d7f6c-abc                         3/3     Running
prometheus-kube-state-metrics-9e8g7f-def              1/1     Running
```

```bash
# 27. Get Grafana password
kubectl get secret prometheus-grafana \
  -n monitoring \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

**Output:** `prom-operator` (the admin password)

---

### **Phase 8: Install Logging (Elasticsearch + Kibana)**

```bash
# 28. Add Elastic Helm repository
helm repo add elastic https://helm.elastic.co
helm repo update
```

```bash
# 29. Install Elasticsearch
helm install elasticsearch elastic/elasticsearch \
  --namespace logging \
  --create-namespace \
  --set replicas=1 \
  --set persistence.enabled=false
```
**Why:** Creates the log storage database

```bash
# 30. Install Kibana
helm install kibana elastic/kibana \
  --namespace logging \
  --set service.type=ClusterIP
```
**Why:** Creates the web UI for searching logs

```bash
# 31. Install Filebeat
helm install filebeat elastic/filebeat \
  --namespace logging \
  -f k8s-manifests/filebeat-values.yaml
```
**Why:** Ships logs from all pods to Elasticsearch

```bash
# 32. Check logging pods
kubectl get pods -n logging
```

**Output:**
```
NAME                             READY   STATUS    RESTARTS
elasticsearch-master-0           1/1     Running   0
kibana-kibana-7c8d9e-xyz        1/1     Running   0
filebeat-nq9mr                   1/1     Running   0
filebeat-p8xks                   1/1     Running   0
filebeat-r7ylm                   1/1     Running   0
```
*(3 filebeat pods = 1 per node)*

---

### **Phase 9: Install ArgoCD**

```bash
# 33. Create ArgoCD namespace
kubectl create namespace argocd
```

```bash
# 34. Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```
**Why:** Installs ArgoCD for GitOps

```bash
# 35. Configure ArgoCD for HTTP (not HTTPS)
kubectl patch configmap argocd-cmd-params-cm -n argocd \
  --type merge \
  -p '{"data":{"server.insecure":"true"}}'
```
**Why:** Makes ArgoCD work with our nginx ingress

```bash
# 36. Get ArgoCD password
kubectl get secret argocd-initial-admin-secret \
  -n argocd \
  -o jsonpath="{.data.password}" | base64 --decode
```

```bash
# 37. Deploy ArgoCD applications
kubectl apply -f argocd-app.yaml
```
**Why:** Tells ArgoCD to watch your GitHub repo and auto-deploy!

---

### **Phase 10: Create Ingress Routes**

```bash
# 38. Apply ingress routes
kubectl apply -f k8s-manifests/monitoring-ingress.yaml
```
**Why:** Makes Grafana, Prometheus, Kibana, ArgoCD accessible from internet

**What this created:**
- `http://grafana.34.173.19.139.nip.io` → Grafana
- `http://prometheus.34.173.19.139.nip.io` → Prometheus
- `http://kibana.34.173.19.139.nip.io` → Kibana
- `http://argocd.34.173.19.139.nip.io` → ArgoCD
- `http://hospital.34.173.19.139.nip.io` → Your frontend app

---

### **Phase 11: Verification**

```bash
# 39. Check all pods across all namespaces
kubectl get pods --all-namespaces
```

```bash
# 40. Test health endpoint
kubectl run curl --image=curlimages/curl -it --rm -- \
  curl http://hospital-patient-hpm:3000/health
```

**Output:** `{"status":"healthy"}`

```bash
# 41. Check logs in Elasticsearch
kubectl port-forward svc/kibana-kibana 5601:5601 -n logging
```
Then visit `http://localhost:5601` and search for logs

---

### **Phase 12: Cleanup**

```bash
# 42. Delete GKE cluster
gcloud container clusters delete hospital-gke --zone=us-central1-a --quiet
```
**Why:** Remove the cluster (was protected, so manual deletion needed)

```bash
# 43. Refresh Pulumi state
pulumi refresh --yes
```
**Why:** Sync Pulumi with actual cloud resources

```bash
# 44. Destroy remaining resources
pulumi destroy --yes
```
**Why:** Delete VPC, subnet, services

```bash
# 45. Delete container images
for image in appointment-api hospital-frontend patient-api; do
  gcloud container images delete gcr.io/charged-thought-485008-q7/$image --quiet
done
```
**Why:** Remove images to avoid storage charges

```bash
# 46. Remove Pulumi stack
pulumi stack rm dev --yes
```
**Why:** Clean up Pulumi metadata

---

## 🎯 HOW EVERYTHING CONNECTS - The Complete Picture

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
              ┌──────────────────────┐
              │  LoadBalancer        │
              │  34.173.19.139       │
              └──────────────────────┘
                         │
                         ↓
              ┌──────────────────────┐
              │  Nginx Ingress       │ ← Routes by hostname
              │  Controller          │
              └──────────────────────┘
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
         ↓               ↓               ↓               ↓
    ┌────────┐    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │Grafana │    │Prometheus│   │ Kibana   │   │ ArgoCD   │
    │Service │    │Service   │   │ Service  │   │ Service  │
    └────────┘    └──────────┘   └──────────┘   └──────────┘
         │               │               │               │
         ↓               ↓               ↓               ↓
    ┌────────┐    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │Grafana │    │Prometheus│   │ Kibana   │   │ ArgoCD   │
    │  Pod   │    │   Pod    │   │   Pod    │   │   Pod    │
    └────────┘    └──────────┘   └──────────┘   └──────────┘
         │               │               │               │
         │               ↓               ↑               │
         │         Scrapes metrics       │               │
         │               │          Ships logs           │
         │               │               │               │
         │         ┌─────┴───────────────┴──────┐        │
         │         │                             │        │
         │         ↓                             ↑        │
         │  ┌──────────────────────────────────────┐     │
         │  │     YOUR APPLICATIONS (hospital)     │     │
         │  │                                      │     │
         │  │  ┌────────────┐  ┌────────────┐     │     │
         │  │  │Patient API │  │Appointment │     │     │
         │  │  │   Pod      │  │  API Pod   │     │     │
         │  │  └─────┬──────┘  └──────┬─────┘     │     │
         │  │        │                │           │     │
         │  │        └────────┬───────┘           │     │
         │  │                 ↓                   │     │
         │  │          ┌─────────────┐            │     │
         │  │          │ SQL Server  │            │     │
         │  │          │     Pod     │            │     │
         │  │          └─────────────┘            │     │
         │  └──────────────────────────────────────┘     │
         │                                               │
         │  ← Queries data to show dashboards            │
         └────────────────── Watches GitHub & deploys ───┘
```

### **The Data Flows:**

1. **User Request Flow:**
   ```
   User types: http://hospital.34.173.19.139.nip.io
   → LoadBalancer (34.173.19.139)
   → Nginx Ingress
   → hospital-ui-hpm Service
   → Frontend Pod
   → Makes API call to patient-api
   → Patient API Pod
   → Queries SQL Server
   → Returns data
   ```

2. **Metrics Flow (Monitoring):**
   ```
   Patient API exposes /metrics
   ← Prometheus scrapes every 15s
   → Stores in Prometheus database
   ← Grafana queries Prometheus
   → Shows graphs in dashboard
   → You view in browser
   ```

3. **Logs Flow (Logging):**
   ```
   Patient API prints to stdout
   → Kubernetes writes to /var/log/containers/
   → Filebeat reads log files
   → Ships to Elasticsearch
   → Indexes and stores
   ← Kibana queries Elasticsearch
   → Shows logs in UI
   → You search in browser
   ```

4. **Deployment Flow (GitOps):**
   ```
   You: git push to GitHub
   → GitHub updates repository
   ← ArgoCD polls every 3 minutes
   → "New commit detected!"
   → Pulls new Helm values
   → Runs helm upgrade
   → Kubernetes updates pods
   → Rolling deployment (zero downtime)
   → New version running!
   ```

---

## 🎓 KEY CONCEPTS SUMMARY

### **1. Separation of Concerns**

Each tool has ONE job:

| Tool | Job | Analogy |
|------|-----|---------|
| **Kubernetes** | Run containers | Apartment building manager |
| **Helm** | Package apps | Moving company with templates |
| **Prometheus** | Collect metrics | Electricity meter reader |
| **Grafana** | Show graphs | Dashboard display |
| **Elasticsearch** | Store logs | Library |
| **Kibana** | Search logs | Library search system |
| **Filebeat** | Ship logs | Mail carrier |
| **ArgoCD** | Auto-deploy | Automated robot deployer |
| **Ingress** | Route traffic | Front desk receptionist |

### **2. Why These Levels Exist**

- **Application Code** (`patient-api/`) - What your app does
- **Docker** (`Dockerfile`) - How to package it
- **Helm** (`hpm/`) - How to configure it for Kubernetes
- **Kubernetes** - Where it runs
- **Ingress** - How users access it
- **Monitoring** - How you observe it
- **GitOps** - How you update it

### **3. Services Point To:**

```yaml
# In values-patient.yaml:
env:
  - name: DB_SERVER
    value: hospital-ui-hpm-sqlserver
```
↓
This points to a **Kubernetes Service** named `hospital-ui-hpm-sqlserver`
↓
Which routes to **SQL Server Pod**

### **4. Metrics Endpoints:**

```yaml
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "3000"
  prometheus.io/path: "/metrics"
```
↓
Tells Prometheus: "Scrape `http://pod-ip:3000/metrics`"

### **5. Health Endpoints:**

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 3000
```
↓
Kubernetes calls: `http://pod-ip:3000/health`
↓
If it fails, restart pod

### **6. Log Annotations:**

```yaml
annotations:
  co.elastic.logs/enabled: "true"
```
↓
Filebeat sees this and says: "Send this pod's logs to Elasticsearch"

---

## 🚀 WHAT YOU CAN DO NOW

### **View Metrics:**
1. Go to Grafana: `http://grafana.34.173.19.139.nip.io`
2. Login: `admin` / `prom-operator`
3. Click "Dashboards" → "Kubernetes / Compute Resources / Namespace (Pods)"
4. Select namespace: `hospital`
5. See CPU, memory, network graphs!

### **Search Logs:**
1. Go to Kibana: `http://kibana.34.173.19.139.nip.io`
2. Click "Discover"
3. Search: `kubernetes.namespace: "hospital"`
4. See all logs from your apps!

### **Watch Deployments:**
1. Go to ArgoCD: `http://argocd.34.173.19.139.nip.io`
2. Login with password from `kubectl get secret`
3. See visual diagram of your apps
4. Push to GitHub and watch auto-deployment!

### **Query Prometheus Directly:**
1. Go to: `http://prometheus.34.173.19.139.nip.io`
2. Try queries:
   ```
   container_cpu_usage_seconds_total{namespace="hospital"}
   container_memory_usage_bytes{namespace="hospital"}
   kube_pod_status_ready{namespace="hospital"}
   ```

---

## 📚 NEXT STEPS FOR LEARNING

1. **Experiment:** Change `replicaCount: 2` in values file, push to GitHub, watch ArgoCD deploy
2. **Break things:** Delete a pod manually (`kubectl delete pod...`), watch it auto-restart
3. **Add metrics:** Add Prometheus client to your Python code to expose custom metrics
4. **Create dashboards:** Build custom Grafana dashboard for your app
5. **Set alerts:** Configure AlertManager to email you when CPU is high

---

I hope this explains everything! Feel free to ask about any specific part you want to understand deeper! 🎉
