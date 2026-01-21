#!/bin/bash

set -e

echo "Deploying Hospital Management Apps with Helm..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create namespace
kubectl create namespace hospital --dry-run=client -o yaml | kubectl apply -f -

# Deploy SQL Server first
echo -e "${YELLOW}Deploying SQL Server...${NC}"
helm upgrade --install hospital-db ./hpm \
  -f hpm/values-ui.yaml \
  --set replicaCount=0 \
  --set sqlserver.enabled=true \
  --namespace hospital \
  --wait

# Wait for SQL Server to be ready
echo "Waiting for SQL Server to be ready..."
sleep 30

# Deploy Patient API
echo -e "${YELLOW}Deploying Patient API...${NC}"
helm upgrade --install hospital-patient ./hpm \
  -f hpm/values-patient.yaml \
  --namespace hospital \
  --wait

# Deploy Appointment API
echo -e "${YELLOW}Deploying Appointment API...${NC}"
helm upgrade --install hospital-appointment ./hpm \
  -f hpm/values-appointment.yaml \
  --namespace hospital \
  --wait

# Deploy Frontend
echo -e "${YELLOW}Deploying Frontend...${NC}"
helm upgrade --install hospital-ui ./hpm \
  -f hpm/values-ui.yaml \
  --set sqlserver.enabled=false \
  --namespace hospital \
  --wait

echo ""
echo -e "${GREEN}All applications deployed successfully!${NC}"
echo ""
echo "Access the application:"
echo "  Frontend: http://localhost:30080"
echo ""
echo "Check pod status:"
kubectl get pods -n hospital
