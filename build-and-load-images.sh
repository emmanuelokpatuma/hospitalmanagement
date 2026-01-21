#!/bin/bash

set -e

echo "=========================================="
echo "Building and Loading Docker Images to kind"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Build patient-api
echo -e "${YELLOW}Building patient-api...${NC}"
cd patient-api
docker build -t patient-api:latest .
kind load docker-image patient-api:latest --name hpm-cluster
echo -e "${GREEN}patient-api loaded to kind${NC}"
cd ..

# Build appointment-api
echo -e "${YELLOW}Building appointment-api...${NC}"
cd appointment-api
docker build -t appointment-api:latest .
kind load docker-image appointment-api:latest --name hpm-cluster
echo -e "${GREEN}appointment-api loaded to kind${NC}"
cd ..

# Build hospital-frontend
echo -e "${YELLOW}Building hospital-frontend...${NC}"
cd hospital-frontend
docker build -t hospital-frontend:latest .
kind load docker-image hospital-frontend:latest --name hpm-cluster
echo -e "${GREEN}hospital-frontend loaded to kind${NC}"
cd ..

echo ""
echo -e "${GREEN}All images built and loaded successfully!${NC}"
echo ""
