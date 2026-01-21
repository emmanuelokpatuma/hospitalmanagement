#!/bin/bash

set -e

echo "=========================================="
echo "Deploying Hospital Management to GCP"
echo "=========================================="
echo ""

cd pulumi

# Preview changes
echo "Previewing changes..."
pulumi preview

echo ""
read -p "Deploy these resources? (yes/no): " CONFIRM

if [[ $CONFIRM != "yes" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Deploy
echo ""
echo "Deploying to GCP... This will take 10-15 minutes."
pulumi up --yes

# Get outputs
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

echo "Cluster Information:"
pulumi stack output cluster_name
pulumi stack output cluster_endpoint

echo ""
echo "Setting up kubectl..."
pulumi stack output kubeconfig > kubeconfig.yaml
export KUBECONFIG=$PWD/kubeconfig.yaml

echo ""
echo "Getting service endpoints..."
kubectl get svc -A

echo ""
echo "Access your services:"
echo ""
echo "Frontend LoadBalancer IP:"
kubectl get svc -n hospital hospital-frontend-hpm -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""
echo ""
echo "Grafana LoadBalancer IP:"
kubectl get svc -n monitoring kube-prometheus-stack-grafana -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""
echo ""
echo "Prometheus LoadBalancer IP:"
kubectl get svc -n monitoring kube-prometheus-stack-prometheus -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""
echo ""
echo "Kibana LoadBalancer IP:"
kubectl get svc -n logging kibana-kibana -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""
echo ""
echo "ArgoCD LoadBalancer IP:"
kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
echo ""

echo ""
echo "Get ArgoCD admin password:"
echo "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d"
echo ""

echo "=========================================="
echo "Setup complete! Your application is running on GCP."
echo "=========================================="
