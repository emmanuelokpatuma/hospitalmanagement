#!/bin/bash

set -e

echo "=========================================="
echo "Hospital Management - GCP Deployment Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

# Check for gcloud
if ! command_exists gcloud; then
    echo -e "${RED}Error: gcloud CLI is not installed${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check for Python 3
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check for pip
if ! command_exists pip3; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    exit 1
fi

# Check for Docker
if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"

echo ""
echo -e "${YELLOW}Step 2: Installing Pulumi...${NC}"

if ! command_exists pulumi; then
    curl -fsSL https://get.pulumi.com | sh
    export PATH=$PATH:$HOME/.pulumi/bin
    echo 'export PATH=$PATH:$HOME/.pulumi/bin' >> ~/.bashrc
    echo -e "${GREEN}✓ Pulumi installed${NC}"
else
    echo -e "${GREEN}✓ Pulumi already installed: $(pulumi version)${NC}"
fi

echo ""
echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"

cd pulumi
pip3 install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

echo ""
echo -e "${YELLOW}Step 4: Setting up GCP...${NC}"

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please login to GCP..."
    gcloud auth login
    gcloud auth application-default login
else
    echo -e "${GREEN}✓ Already logged in to GCP${NC}"
fi

# Get current project or prompt user
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$CURRENT_PROJECT" ]; then
    echo ""
    echo "Available GCP projects:"
    gcloud projects list --format="table(projectId,name)"
    echo ""
    read -p "Enter your GCP Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
else
    echo -e "${GREEN}✓ Current GCP project: $CURRENT_PROJECT${NC}"
    read -p "Use this project? (y/n): " USE_CURRENT
    if [[ $USE_CURRENT != "y" && $USE_CURRENT != "Y" ]]; then
        echo ""
        echo "Available GCP projects:"
        gcloud projects list --format="table(projectId,name)"
        echo ""
        read -p "Enter your GCP Project ID: " PROJECT_ID
        gcloud config set project $PROJECT_ID
    else
        PROJECT_ID=$CURRENT_PROJECT
    fi
fi

# Update Pulumi config
echo "Updating Pulumi configuration..."
pulumi config set gcp:project $PROJECT_ID

echo ""
echo -e "${YELLOW}Step 5: Enabling required GCP APIs...${NC}"

cd ..

# Enable required APIs
echo "Enabling Container Registry API..."
gcloud services enable containerregistry.googleapis.com --project=$PROJECT_ID

echo "Enabling Artifact Registry API..."
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID

echo "Enabling Kubernetes Engine API..."
gcloud services enable container.googleapis.com --project=$PROJECT_ID

echo "Enabling Compute Engine API..."
gcloud services enable compute.googleapis.com --project=$PROJECT_ID

echo "Waiting for APIs to be fully enabled..."
sleep 10

echo -e "${GREEN}✓ Required APIs enabled${NC}"

# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker --quiet

echo ""
echo -e "${YELLOW}Step 6: Building Docker images...${NC}"

# Build patient-api
echo "Building patient-api..."
cd patient-api
docker build -t gcr.io/$PROJECT_ID/patient-api:latest .
docker push gcr.io/$PROJECT_ID/patient-api:latest
cd ..

# Build appointment-api
echo "Building appointment-api..."
cd appointment-api
docker build -t gcr.io/$PROJECT_ID/appointment-api:latest .
docker push gcr.io/$PROJECT_ID/appointment-api:latest
cd ..

# Build hospital-frontend
echo "Building hospital-frontend..."
cd hospital-frontend
docker build -t gcr.io/$PROJECT_ID/hospital-frontend:latest .
docker push gcr.io/$PROJECT_ID/hospital-frontend:latest
cd ..

echo -e "${GREEN}✓ All images built and pushed to GCR${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Review Pulumi configuration:"
echo "   cd pulumi"
echo "   pulumi config"
echo ""
echo "2. Preview the deployment:"
echo "   pulumi preview"
echo ""
echo "3. Deploy to GCP:"
echo "   pulumi up"
echo ""
echo "4. After deployment, get access URLs:"
echo "   pulumi stack output"
echo ""
echo "5. Configure kubectl:"
echo "   pulumi stack output kubeconfig > kubeconfig.yaml"
echo "   export KUBECONFIG=\$PWD/kubeconfig.yaml"
echo ""
echo -e "${YELLOW}Note: GKE cluster and all services will incur GCP charges.${NC}"
echo -e "${YELLOW}Use 'pulumi destroy' to tear down everything when done.${NC}"
echo ""
