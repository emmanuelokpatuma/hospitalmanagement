# Hospital Management - GCP Deployment with Pulumi

Deploy the complete Hospital Management system to Google Cloud Platform (GCP) using Pulumi Infrastructure as Code.

## 🏗️ What Gets Deployed

### Infrastructure
- **GKE Cluster** (Google Kubernetes Engine)
  - 3 worker nodes (e2-standard-2)
  - VPC with custom subnets
  - Workload Identity enabled
  - Auto-scaling and auto-repair enabled

### Applications
- **Patient API** (2 replicas)
- **Appointment API** (2 replicas)  
- **Frontend** (2 replicas)
- **SQL Server** (database)

### Monitoring & Observability
- **Prometheus** - Metrics collection
- **Grafana** - Dashboards and visualization
- **Elasticsearch** - Log storage
- **Kibana** - Log visualization
- **Filebeat** - Log shipping
- **ArgoCD** - GitOps continuous delivery

### Networking
- **LoadBalancers** for public access
- **ClusterIP** for internal services
- GCP managed SSL certificates (optional)

## 💰 Estimated GCP Costs

**Approximate monthly cost: $200-300 USD**

Breakdown:
- GKE cluster: ~$75/month
- 3 x e2-standard-2 nodes: ~$90/month
- Load Balancers: ~$20/month
- Persistent disks: ~$30/month
- Networking: ~$10/month
- Monitoring data: ~$20/month

> **Note**: Use the free tier and always run `pulumi destroy` when done to avoid charges!

## 📋 Prerequisites

1. **GCP Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Docker** installed
4. **Python 3.8+** and pip
5. **Active terminal** with bash

## 🚀 Quick Start

### Step 1: Setup and Install Pulumi

Run the automated setup script:

```bash
chmod +x setup-gcp-pulumi.sh
./setup-gcp-pulumi.sh
```

This will:
- ✅ Check prerequisites
- ✅ Install Pulumi
- ✅ Install Python dependencies
- ✅ Login to GCP
- ✅ Configure your GCP project
- ✅ Build and push Docker images to Google Container Registry (GCR)

**Expected duration**: 5-10 minutes

### Step 2: Deploy to GCP

```bash
chmod +x deploy-to-gcp.sh
./deploy-to-gcp.sh
```

This will:
- Preview all resources to be created
- Ask for confirmation
- Deploy GKE cluster (takes ~10 minutes)
- Deploy all applications and monitoring tools
- Display access URLs

**Expected duration**: 15-20 minutes

### Step 3: Access Your Services

After deployment completes, you'll get LoadBalancer IPs for:

- **Frontend**: `http://<FRONTEND-IP>`
- **Grafana**: `http://<GRAFANA-IP>` (admin / admin123)
- **Prometheus**: `http://<PROMETHEUS-IP>:9090`
- **Kibana**: `http://<KIBANA-IP>:5601`
- **ArgoCD**: `http://<ARGOCD-IP>` (admin / [get password below])

Get ArgoCD password:
```bash
export KUBECONFIG=$PWD/pulumi/kubeconfig.yaml
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## 🔧 Manual Deployment (Alternative)

If you prefer step-by-step manual deployment:

### 1. Install Pulumi

```bash
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin
```

### 2. Login to Pulumi

```bash
pulumi login  # Use local backend or pulumi.com
```

### 3. Install Dependencies

```bash
cd pulumi
pip3 install -r requirements.txt
```

### 4. Configure GCP

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID

pulumi config set gcp:project YOUR_PROJECT_ID
pulumi config set gcp:region us-central1
```

### 5. Build and Push Images

```bash
PROJECT_ID=$(gcloud config get-value project)

# Enable Container Registry
gcloud services enable containerregistry.googleapis.com

# Configure Docker
gcloud auth configure-docker

# Build and push
cd ../patient-api
docker build -t gcr.io/$PROJECT_ID/patient-api:latest .
docker push gcr.io/$PROJECT_ID/patient-api:latest

cd ../appointment-api
docker build -t gcr.io/$PROJECT_ID/appointment-api:latest .
docker push gcr.io/$PROJECT_ID/appointment-api:latest

cd ../hospital-frontend
docker build -t gcr.io/$PROJECT_ID/hospital-frontend:latest .
docker push gcr.io/$PROJECT_ID/hospital-frontend:latest
```

### 6. Update Image References

Update [pulumi/apps.py](pulumi/apps.py) to use GCR images:

```python
"image": {
    "repository": f"gcr.io/{project_id}/patient-api",
    "tag": "latest",
}
```

### 7. Deploy Infrastructure

```bash
cd ../pulumi

# Preview changes
pulumi preview

# Deploy
pulumi up
```

### 8. Get kubeconfig

```bash
pulumi stack output kubeconfig > kubeconfig.yaml
export KUBECONFIG=$PWD/kubeconfig.yaml
kubectl get nodes
```

## 📊 Monitoring & Observability

### Prometheus Queries

Access Prometheus and try these queries:

```promql
# Request rate
sum(rate(http_requests_total[5m])) by (service)

# CPU usage
sum(rate(container_cpu_usage_seconds_total{namespace="hospital"}[5m])) by (pod)

# Memory usage
sum(container_memory_usage_bytes{namespace="hospital"}) by (pod)
```

### Grafana Dashboards

Pre-installed dashboards:
1. Kubernetes / Compute Resources / Namespace
2. Kubernetes / Compute Resources / Pod
3. Node Exporter / Nodes

### Kibana Log Analysis

1. Open Kibana URL
2. Create index patterns: `filebeat-*`
3. Navigate to Discover
4. Filter by namespace: `kubernetes.namespace: hospital`

## 🔄 Updating the Application

### Method 1: Pulumi Update

1. Make code changes
2. Rebuild images and push to GCR
3. Update version tags in `apps.py`
4. Run `pulumi up`

### Method 2: kubectl (Quick)

```bash
kubectl set image deployment/hospital-patient-hpm hospital-patient=gcr.io/PROJECT_ID/patient-api:v2 -n hospital
```

### Method 3: ArgoCD (GitOps)

1. Push changes to GitHub
2. ArgoCD automatically syncs
3. Monitor in ArgoCD UI

## 🛠️ Useful Commands

### Pulumi Operations

```bash
# View current stack
pulumi stack

# List all outputs
pulumi stack output

# View specific output
pulumi stack output cluster_endpoint

# Refresh state
pulumi refresh

# Destroy everything
pulumi destroy
```

### Kubernetes Operations

```bash
# Get all resources
kubectl get all -A

# Hospital app pods
kubectl get pods -n hospital

# Logs
kubectl logs -f -n hospital <pod-name>

# Port forwarding
kubectl port-forward -n hospital svc/hospital-frontend-hpm 8080:80

# Scale deployment
kubectl scale deployment hospital-patient-hpm --replicas=3 -n hospital
```

### GCP Operations

```bash
# View cluster
gcloud container clusters list

# Get cluster credentials
gcloud container clusters get-credentials hospital-gke --zone us-central1-a

# View GCR images
gcloud container images list

# SSH to node
gcloud compute ssh <node-name>
```

## 🔍 Troubleshooting

### Images Not Pulling

Check if images are in GCR:
```bash
gcloud container images list --repository=gcr.io/$(gcloud config get-value project)
```

Fix: Update image repository in `apps.py` to use full GCR path.

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n hospital
kubectl logs <pod-name> -n hospital
```

Common issues:
- Image pull errors → Check GCR permissions
- CrashLoopBackOff → Check application logs
- Pending → Check node resources

### LoadBalancer Pending

```bash
kubectl get svc -n hospital hospital-frontend-hpm
```

If stuck in "Pending", check:
```bash
kubectl describe svc hospital-frontend-hpm -n hospital
```

May take 2-5 minutes for GCP to provision load balancer.

### Out of Resources

```bash
kubectl top nodes
kubectl top pods -A
```

Scale down or increase node pool size:
```bash
pulumi config set hospital-management-gcp:node-count 5
pulumi up
```

## 💾 Backup and Restore

### Backup Kubernetes Resources

```bash
# Install Velero
kubectl apply -f https://raw.githubusercontent.com/vmware-tanzu/velero/main/examples/minio/00-minio-deployment.yaml

# Create backup
velero backup create hospital-backup --include-namespaces hospital
```

### Export Pulumi State

```bash
pulumi stack export > hospital-stack-backup.json
```

## 🧹 Cleanup

### Destroy Everything

```bash
cd pulumi
pulumi destroy
```

This will delete:
- ✅ All Kubernetes resources
- ✅ GKE cluster
- ✅ VPC and subnets
- ✅ Load balancers
- ✅ Persistent disks

**Important**: This does NOT delete:
- Docker images in GCR (delete manually)
- Pulumi state (delete stack with `pulumi stack rm`)

### Delete GCR Images

```bash
gcloud container images delete gcr.io/$(gcloud config get-value project)/patient-api:latest
gcloud container images delete gcr.io/$(gcloud config get-value project)/appointment-api:latest
gcloud container images delete gcr.io/$(gcloud config get-value project)/hospital-frontend:latest
```

### Remove Pulumi Stack

```bash
pulumi stack rm dev
```

## 📈 Cost Optimization Tips

1. **Use Preemptible Nodes** (70% cheaper)
   ```bash
   pulumi config set hospital-management-gcp:preemptible true
   ```

2. **Reduce Node Count**
   ```bash
   pulumi config set hospital-management-gcp:node-count 2
   ```

3. **Scale Down After Hours**
   ```bash
   kubectl scale deployment --all --replicas=0 -n hospital
   ```

4. **Use Smaller Machine Types**
   ```bash
   pulumi config set hospital-management-gcp:machine-type e2-small
   ```

5. **Set Up Auto-Shutdown**
   Schedule GKE cluster shutdown with Cloud Scheduler

## 🎯 Production Checklist

Before going to production:

- [ ] Enable Cloud Armor (DDoS protection)
- [ ] Set up Cloud CDN
- [ ] Configure SSL certificates
- [ ] Enable Binary Authorization
- [ ] Set up Cloud SQL instead of in-cluster database
- [ ] Configure Secret Manager for credentials
- [ ] Set up VPC Service Controls
- [ ] Enable GKE audit logging
- [ ] Configure backup policies
- [ ] Set up alerting and on-call
- [ ] Implement RBAC policies
- [ ] Enable Network Policies
- [ ] Configure Pod Security Policies
- [ ] Set up disaster recovery plan

## 📚 Learn More

- [Pulumi GCP Docs](https://www.pulumi.com/docs/clouds/gcp/)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Kubernetes Patterns](https://kubernetes.io/docs/concepts/)

## 🤝 Support

If you encounter issues:
1. Check `pulumi logs`
2. Review GCP Console → Kubernetes Engine
3. Check pod logs: `kubectl logs -n hospital <pod>`
4. Review Pulumi state: `pulumi stack`

---

**Happy Deploying! 🚀**

Remember to destroy resources when done to avoid charges: `pulumi destroy`
