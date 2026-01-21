# 🔍 Monitoring & Observability Stack - Access Guide

All monitoring tools are now deployed and accessible via ingress with the external IP: **34.173.19.139**

## 📊 Access URLs

### 1. **Grafana** (Metrics Visualization & Dashboards)
- **URL**: http://grafana.34.173.19.139.nip.io
- **Username**: `admin`
- **Password**: `admin123`
- **Purpose**: Visualize metrics, create dashboards, set up alerts

### 2. **Prometheus** (Metrics Collection & Monitoring)
- **URL**: http://prometheus.34.173.19.139.nip.io
- **Authentication**: None (internal use)
- **Purpose**: Query metrics, check targets, explore PromQL

### 3. **Kibana** (Log Visualization & Analysis)
- **URL**: http://kibana.34.173.19.139.nip.io
- **Username**: `elastic`
- **Password**: `keB6DS2kLpFaoNB7`
- **Purpose**: Search logs, create visualizations, log analysis

### 4. **ArgoCD** (GitOps Continuous Deployment)
- **URL**: http://argocd.34.173.19.139.nip.io
- **Username**: `admin`
- **Password**: `CzQ3T2y0s5WdwQPQ`
- **Purpose**: Manage application deployments, sync with Git repos

### 5. **Hospital Application** (Your Main App)
- **URL**: http://hospital.34.173.19.139.nip.io
- **Patient API**: http://hospital.34.173.19.139.nip.io/api/patients/
- **Appointment API**: http://hospital.34.173.19.139.nip.io/api/appointments/

## 🔐 Credentials Summary

| Service | Username | Password | Namespace |
|---------|----------|----------|-----------|
| Grafana | admin | admin123 | monitoring |
| Kibana | elastic | keB6DS2kLpFaoNB7 | logging |
| ArgoCD | admin | CzQ3T2y0s5WdwQPQ | argocd |
| Elasticsearch | elastic | keB6DS2kLpFaoNB7 | logging |

## 📦 What's Deployed

### Monitoring Stack (namespace: monitoring)
- ✅ **Prometheus Operator** - Kubernetes-native monitoring
- ✅ **Prometheus Server** - Metrics collection and storage
- ✅ **Grafana** - Metrics visualization with dashboards
- ✅ **AlertManager** - Alert routing and management
- ✅ **Node Exporter** - Hardware and OS metrics
- ✅ **Kube State Metrics** - Kubernetes cluster metrics

### Logging Stack (namespace: logging)
- ✅ **Elasticsearch** - Log storage and search engine
- ✅ **Kibana** - Log visualization and exploration

### GitOps Stack (namespace: argocd)
- ✅ **ArgoCD Server** - GitOps controller
- ✅ **ArgoCD Repo Server** - Git repository connector
- ✅ **ArgoCD Application Controller** - K8s resource sync

## 🚀 Quick Start Guide

### Grafana
1. Open http://grafana.34.173.19.139.nip.io
2. Login with admin/admin123
3. Navigate to **Dashboards** → **Browse** to see pre-built dashboards
4. Explore: Kubernetes cluster monitoring, node metrics, pod metrics

### Prometheus
1. Open http://prometheus.34.173.19.139.nip.io
2. Go to **Status** → **Targets** to see all monitored services
3. Use **Graph** tab to run PromQL queries
4. Example query: `up` (shows all targets)

### Kibana
1. Open http://kibana.34.173.19.139.nip.io
2. Login with elastic/keB6DS2kLpFaoNB7
3. First time: Create an index pattern for logs
4. Go to **Discover** to explore logs

### ArgoCD
1. Open http://argocd.34.173.19.139.nip.io
2. Login with admin/CzQ3T2y0s5WdwQPQ
3. Click **+ New App** to create application from Git
4. Sync your applications with your GitHub repository

## 🔧 Useful Commands

### Check all monitoring pods
```bash
kubectl get pods -n monitoring
kubectl get pods -n logging
kubectl get pods -n argocd
```

### Check ingress resources
```bash
kubectl get ingress --all-namespaces
```

### Get service details
```bash
kubectl get svc -n monitoring
kubectl get svc -n logging
kubectl get svc -n argocd
```

### Retrieve passwords again
```bash
# ArgoCD password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Elasticsearch password
kubectl get secrets --namespace=logging elasticsearch-master-credentials -o jsonpath='{.data.password}' | base64 -d

# Grafana password (if needed)
kubectl get secret --namespace monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d
```

## 📈 Next Steps

1. **Configure Grafana Dashboards**: Import community dashboards for your stack
2. **Set up Log Shippers**: Deploy Filebeat/Fluentd to collect application logs
3. **Create ArgoCD Applications**: Connect your Git repository for GitOps
4. **Configure Alerts**: Set up Prometheus AlertManager rules
5. **Enable ServiceMonitors**: Enable metrics collection for your apps

## 🌐 All URLs at a Glance

```
Hospital App:    http://hospital.34.173.19.139.nip.io
Grafana:         http://grafana.34.173.19.139.nip.io
Prometheus:      http://prometheus.34.173.19.139.nip.io
Kibana:          http://kibana.34.173.19.139.nip.io
ArgoCD:          http://argocd.34.173.19.139.nip.io
```

---
**Note**: These URLs use nip.io which provides wildcard DNS resolution for any IP address.
The services are accessible from anywhere as long as the GKE cluster is running.
