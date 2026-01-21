# Hospital Management - Kubernetes Multi-Service Setup

Complete observability and GitOps stack for the Hospital Management multi-service application.

## 🏗️ Architecture Overview

This setup includes:
- **3 Microservices**: Patient API, Appointment API, Frontend (Angular)
- **Database**: SQL Server
- **Orchestration**: Kubernetes (kind cluster)
- **Package Manager**: Helm
- **GitOps**: ArgoCD
- **Monitoring**: Prometheus + Grafana
- **Logging**: Elasticsearch + Kibana + Filebeat

## 📋 Prerequisites

- Docker installed and running
- Linux OS (Ubuntu/Debian recommended)
- At least 8GB RAM available
- Internet connection for downloading tools and images

## 🚀 Quick Start

### Step 1: Setup Kubernetes Cluster and Tools

Run the automated setup script to install all required tools:

```bash
chmod +x setup-k8s-stack.sh
./setup-k8s-stack.sh
```

This script will:
1. Install `kubectl` (Kubernetes CLI)
2. Install `kind` (Kubernetes in Docker)
3. Install `Helm` (Package Manager)
4. Create a kind cluster named `hpm-cluster`
5. Install ArgoCD
6. Install Prometheus & Grafana (kube-prometheus-stack)
7. Install Elasticsearch, Kibana & Filebeat

**Expected duration**: 10-15 minutes

### Step 2: Build and Load Docker Images

Build your application images and load them into the kind cluster:

```bash
chmod +x build-and-load-images.sh
./build-and-load-images.sh
```

This will:
- Build `patient-api:latest`
- Build `appointment-api:latest`
- Build `hospital-frontend:latest`
- Load all images into the kind cluster

### Step 3: Deploy Applications

Deploy all services using Helm:

```bash
chmod +x deploy-apps.sh
./deploy-apps.sh
```

This deploys:
- SQL Server (database)
- Patient API
- Appointment API
- Frontend UI

## 🌐 Access Your Services

After deployment, access the following services:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Hospital Frontend** | http://localhost:30080 | - |
| **ArgoCD** | https://localhost:30000 | admin / [see below] |
| **Prometheus** | http://localhost:30001 | - |
| **Grafana** | http://localhost:30002 | admin / admin123 |
| **Kibana** | http://localhost:30003 | - |

### Get ArgoCD Password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

## 📊 Monitoring Setup

### Prometheus Metrics

Your APIs are configured with Prometheus scraping annotations:
- Patient API: Scrapes metrics from port 3000 at `/metrics`
- Appointment API: Scrapes metrics from port 3001 at `/metrics`

View metrics in Prometheus UI:
1. Go to http://localhost:30001
2. Try queries like:
   - `http_requests_total`
   - `container_cpu_usage_seconds_total{namespace="hospital"}`
   - `container_memory_usage_bytes{namespace="hospital"}`

### Grafana Dashboards

Access Grafana at http://localhost:30002 (admin / admin123)

**Pre-configured dashboards:**
1. Kubernetes / Compute Resources / Namespace (Pods)
2. Kubernetes / Compute Resources / Cluster
3. Node Exporter / Nodes

**Add Prometheus datasource:**
- Already configured automatically
- URL: `http://kube-prometheus-stack-prometheus:9090`

**Custom Dashboard:**
Import the Hospital Management dashboard:
```bash
kubectl apply -f k8s-manifests/monitoring/grafana-dashboard.yaml
```

## 📝 Logging with ELK Stack

### View Logs in Kibana

1. Open http://localhost:30003
2. Go to **Management** > **Stack Management** > **Index Patterns**
3. Create index patterns:
   - `filebeat-patient-api-*`
   - `filebeat-appointment-api-*`
   - `filebeat-frontend-*`
4. Go to **Analytics** > **Discover** to view logs

### Log Structure

Logs are automatically collected from all pods and indexed by service:
- Patient API logs → `filebeat-patient-api-YYYY.MM.DD`
- Appointment API logs → `filebeat-appointment-api-YYYY.MM.DD`
- Frontend logs → `filebeat-frontend-YYYY.MM.DD`

## 🔄 GitOps with ArgoCD

### Deploy via ArgoCD

**Important**: Before using ArgoCD, update the repository URL in `argocd/applications.yaml`:

```yaml
repoURL: https://github.com/yourusername/hospitalmanagement.git
```

Then apply the ArgoCD applications:

```bash
# Create ArgoCD project
kubectl apply -f argocd/project.yaml

# Deploy applications
kubectl apply -f argocd/applications.yaml
```

### ArgoCD Features

- **Automated Sync**: Applications auto-sync when code changes
- **Self-Healing**: Automatically reverts manual changes
- **Multi-Service Management**: Manage all 3 services from one UI

Access ArgoCD UI at https://localhost:30000

## 🛠️ Useful Commands

### Check Pod Status

```bash
# All pods
kubectl get pods -A

# Hospital app pods
kubectl get pods -n hospital

# Monitoring pods
kubectl get pods -n monitoring

# Logging pods
kubectl get pods -n logging
```

### View Logs

```bash
# Patient API logs
kubectl logs -n hospital -l app=patient-api -f

# Appointment API logs
kubectl logs -n hospital -l app=appointment-api -f

# Frontend logs
kubectl logs -n hospital -l app=hospital-frontend -f
```

### Helm Operations

```bash
# List all releases
helm list -A

# Upgrade a release
helm upgrade hospital-patient ./hpm -f hpm/values-patient.yaml -n hospital

# Rollback a release
helm rollback hospital-patient -n hospital

# Uninstall a release
helm uninstall hospital-patient -n hospital
```

### Port Forwarding (Alternative Access)

```bash
# Forward Prometheus
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

# Forward Grafana
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80

# Forward Kibana
kubectl port-forward -n logging svc/kibana-kibana 5601:5601
```

## 🔍 Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n hospital

# Check pod logs
kubectl logs <pod-name> -n hospital
```

### Images Not Found

Make sure you've run the build script:
```bash
./build-and-load-images.sh
```

Verify images are loaded in kind:
```bash
docker exec -it hpm-cluster-control-plane crictl images
```

### Database Connection Issues

Check SQL Server is running:
```bash
kubectl get pods -n hospital | grep sqlserver
kubectl logs -n hospital <sqlserver-pod-name>
```

### Service Not Accessible

Check service and endpoints:
```bash
kubectl get svc -n hospital
kubectl get endpoints -n hospital
```

## 🧹 Cleanup

### Delete Applications Only

```bash
helm uninstall hospital-patient hospital-appointment hospital-ui hospital-db -n hospital
```

### Delete Entire Cluster

```bash
kind delete cluster --name hpm-cluster
```

### Uninstall Tools (Optional)

```bash
sudo rm /usr/local/bin/kubectl /usr/local/bin/helm /usr/local/bin/kind
```

## 📚 Learning Resources

### Explore the Stack

1. **Helm Charts**: Check `hpm/` directory for chart templates
2. **ArgoCD Apps**: See `argocd/` for application definitions
3. **Monitoring Config**: Check `k8s-manifests/monitoring/`
4. **Logging Config**: Check `k8s-manifests/logging/`

### Key Concepts to Learn

- **Helm**: Package manager for Kubernetes
  - Charts, values, templates
  - Release management
  
- **ArgoCD**: GitOps continuous delivery
  - Application sync
  - Automated deployment
  - Rollbacks

- **Prometheus**: Metrics collection
  - Service discovery
  - PromQL queries
  - Alerting

- **Grafana**: Visualization
  - Dashboard creation
  - Data sources
  - Alerting

- **ELK Stack**: Centralized logging
  - Log collection (Filebeat)
  - Log storage (Elasticsearch)
  - Log visualization (Kibana)

## 🎯 Next Steps

1. **Add Health Endpoints**: Implement `/health` and `/metrics` endpoints in your APIs
2. **Custom Dashboards**: Create custom Grafana dashboards for your metrics
3. **Alerting**: Configure Prometheus alerts for critical metrics
4. **CI/CD Pipeline**: Integrate with GitHub Actions or Jenkins
5. **Ingress Controller**: Add NGINX Ingress for production-like routing
6. **Security**: Add NetworkPolicies, RBAC, and Pod Security Policies

## 📖 Additional Notes

### Resource Requirements

Minimum resources for the full stack:
- CPU: 4 cores
- RAM: 8GB
- Disk: 20GB

### Persistent Storage

Currently using emptyDir volumes. For production, consider:
- PersistentVolumes (PV)
- PersistentVolumeClaims (PVC)
- StorageClasses

### Production Considerations

This setup is for **learning and development**. For production:
- Use managed Kubernetes (EKS, GKE, AKS)
- Implement proper secrets management (Vault, Sealed Secrets)
- Add backup and disaster recovery
- Implement proper RBAC and network policies
- Use production-grade storage solutions
- Add proper SSL/TLS certificates
- Implement rate limiting and API gateways

## 💡 Tips

- Use `kubectl get events -n hospital --sort-by='.lastTimestamp'` to debug issues
- Check resource usage: `kubectl top nodes` and `kubectl top pods -n hospital`
- Use `helm template` to preview manifests before applying
- ArgoCD can diff and show what will change before syncing
- Grafana has built-in Kubernetes dashboards - explore them!

## 🤝 Contributing

Feel free to extend this setup with:
- Additional microservices
- More advanced monitoring dashboards
- Custom alerts
- Service mesh (Istio/Linkerd)
- Distributed tracing (Jaeger)

---

**Happy Learning! 🚀**

For issues or questions, check the logs and Kubernetes events first. Most issues are related to resource constraints or image availability in the kind cluster.
