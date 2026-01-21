#!/bin/bash

set -e

echo "=========================================="
echo "Hospital Management - K8s Stack Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "This script is designed for Linux. Adjustments may be needed for other OS."
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Install kubectl
echo -e "${YELLOW}[1/7] Installing kubectl...${NC}"
if command_exists kubectl; then
    echo "kubectl already installed: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
else
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x kubectl
    sudo mv kubectl /usr/local/bin/
    echo -e "${GREEN}kubectl installed successfully${NC}"
fi

# 2. Install kind (Kubernetes in Docker)
echo -e "${YELLOW}[2/7] Installing kind...${NC}"
if command_exists kind; then
    echo "kind already installed: $(kind version)"
else
    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
    chmod +x ./kind
    sudo mv ./kind /usr/local/bin/kind
    echo -e "${GREEN}kind installed successfully${NC}"
fi

# 3. Install Helm
echo -e "${YELLOW}[3/7] Installing Helm...${NC}"
if command_exists helm; then
    echo "Helm already installed: $(helm version --short)"
else
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    echo -e "${GREEN}Helm installed successfully${NC}"
fi

# 4. Create kind cluster
echo -e "${YELLOW}[4/7] Creating kind cluster...${NC}"
if kind get clusters | grep -q "hpm-cluster"; then
    echo "Cluster 'hpm-cluster' already exists"
else
    cat <<EOF | kind create cluster --name hpm-cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
  - containerPort: 30000
    hostPort: 30000
    protocol: TCP
  - containerPort: 30001
    hostPort: 30001
    protocol: TCP
  - containerPort: 30002
    hostPort: 30002
    protocol: TCP
EOF
    echo -e "${GREEN}Kind cluster created successfully${NC}"
fi

# Set kubectl context
kubectl cluster-info --context kind-hpm-cluster

# 5. Install ArgoCD
echo -e "${YELLOW}[5/7] Installing ArgoCD...${NC}"
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Expose ArgoCD server
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort", "ports": [{"port": 443, "nodePort": 30000, "targetPort": 8080}]}}'

echo -e "${GREEN}ArgoCD installed successfully${NC}"
echo "ArgoCD UI will be available at: https://localhost:30000"
echo "Initial admin password:"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""

# 6. Install Prometheus & Grafana
echo -e "${YELLOW}[6/7] Installing Prometheus & Grafana...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install kube-prometheus-stack (includes Prometheus, Grafana, and Alertmanager)
if helm list -n monitoring | grep -q "kube-prometheus-stack"; then
    echo "kube-prometheus-stack already installed"
else
    helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.service.type=NodePort \
        --set prometheus.service.nodePort=30001 \
        --set grafana.service.type=NodePort \
        --set grafana.service.nodePort=30002 \
        --set grafana.adminPassword=admin123 \
        --wait
    echo -e "${GREEN}Prometheus & Grafana installed successfully${NC}"
fi

# 7. Install Elastic Stack (Elasticsearch & Kibana)
echo -e "${YELLOW}[7/7] Installing Elastic Stack...${NC}"
helm repo add elastic https://helm.elastic.co
helm repo update

kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -

# Install Elasticsearch
if helm list -n logging | grep -q "elasticsearch"; then
    echo "Elasticsearch already installed"
else
    helm install elasticsearch elastic/elasticsearch \
        --namespace logging \
        --set replicas=1 \
        --set minimumMasterNodes=1 \
        --set resources.requests.memory=1Gi \
        --set resources.requests.cpu=500m \
        --wait --timeout=10m
    echo -e "${GREEN}Elasticsearch installed successfully${NC}"
fi

# Install Kibana
if helm list -n logging | grep -q "kibana"; then
    echo "Kibana already installed"
else
    helm install kibana elastic/kibana \
        --namespace logging \
        --set service.type=NodePort \
        --set service.nodePort=30003 \
        --wait
    echo -e "${GREEN}Kibana installed successfully${NC}"
fi

# Install Filebeat for log collection
if helm list -n logging | grep -q "filebeat"; then
    echo "Filebeat already installed"
else
    helm install filebeat elastic/filebeat \
        --namespace logging \
        --wait
    echo -e "${GREEN}Filebeat installed successfully${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Access your services:"
echo "  - ArgoCD:     https://localhost:30000 (admin / see password above)"
echo "  - Prometheus: http://localhost:30001"
echo "  - Grafana:    http://localhost:30002 (admin / admin123)"
echo "  - Kibana:     http://localhost:30003"
echo ""
echo "Next steps:"
echo "  1. Build and load Docker images: ./build-and-load-images.sh"
echo "  2. Deploy applications with Helm or ArgoCD"
echo "  3. Check the README-K8S-SETUP.md for detailed instructions"
echo ""
