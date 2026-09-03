#!/bin/bash

# Kubernetes deployment script for Library Management Platform
# This script deploys all resources in the correct order

set -e

NAMESPACE="library"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "Library Management Platform - K8s Deployment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

kubectl cluster-info > /dev/null 2>&1 || {
    echo "Error: Cannot connect to Kubernetes cluster"
    exit 1
}
echo -e "${GREEN}✓ kubectl is installed and connected${NC}"
echo ""

# Step 1: Create namespace
echo -e "${BLUE}Step 1: Creating namespace...${NC}"
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
echo -e "${GREEN}✓ Namespace created${NC}"
sleep 2
echo ""

# Step 2: Deploy PostgreSQL
echo -e "${BLUE}Step 2: Deploying PostgreSQL...${NC}"
kubectl apply -f "$SCRIPT_DIR/postgres/secret.yaml"
kubectl apply -f "$SCRIPT_DIR/postgres/configmap.yaml"
kubectl apply -f "$SCRIPT_DIR/postgres/init-configmap.yaml"
kubectl apply -f "$SCRIPT_DIR/postgres/statefulset.yaml"
kubectl apply -f "$SCRIPT_DIR/postgres/service.yaml"
echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s
echo -e "${GREEN}✓ PostgreSQL deployed and ready${NC}"
sleep 2
echo ""

# Step 3: Deploy Redis
echo -e "${BLUE}Step 3: Deploying Redis...${NC}"
kubectl apply -f "$SCRIPT_DIR/redis/pvc.yaml"
kubectl apply -f "$SCRIPT_DIR/redis/deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/redis/service.yaml"
echo "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=300s
echo -e "${GREEN}✓ Redis deployed and ready${NC}"
sleep 2
echo ""

# Step 4: Deploy User Service
echo -e "${BLUE}Step 4: Deploying User Service...${NC}"
kubectl apply -f "$SCRIPT_DIR/services/user-service/"
echo "Waiting for User Service to be ready..."
kubectl wait --for=condition=ready pod -l app=user-service -n "$NAMESPACE" --timeout=300s
echo -e "${GREEN}✓ User Service deployed and ready${NC}"
sleep 2
echo ""

# Step 5: Deploy Book Service
echo -e "${BLUE}Step 5: Deploying Book Service...${NC}"
kubectl apply -f "$SCRIPT_DIR/services/book-service/"
echo "Waiting for Book Service to be ready..."
kubectl wait --for=condition=ready pod -l app=book-service -n "$NAMESPACE" --timeout=300s
echo -e "${GREEN}✓ Book Service deployed and ready${NC}"
sleep 2
echo ""

# Step 6: Deploy Loan Service
echo -e "${BLUE}Step 6: Deploying Loan Service...${NC}"
kubectl apply -f "$SCRIPT_DIR/services/loan-service/"
echo "Waiting for Loan Service to be ready..."
kubectl wait --for=condition=ready pod -l app=loan-service -n "$NAMESPACE" --timeout=300s
echo -e "${GREEN}✓ Loan Service deployed and ready${NC}"
sleep 2
echo ""

# Step 7: Deploy Frontend
echo -e "${BLUE}Step 7: Deploying Frontend...${NC}"
kubectl apply -f "$SCRIPT_DIR/frontend-deployment.yaml"
kubectl wait --for=condition=ready pod -l app=frontend -n "$NAMESPACE" --timeout=300s

# Step 8: Deploy Ingress & Network Policies
echo -e "${BLUE}Step 8: Deploying Ingress and Network Policies...${NC}"
kubectl apply -f "$SCRIPT_DIR/ingress/"
echo -e "${GREEN}✓ Ingress and Network Policies deployed${NC}"
sleep 2
echo ""

# Summary
echo -e "${YELLOW}=========================================="
echo "Deployment Summary"
echo "==========================================${NC}"
echo ""

echo -e "${BLUE}Namespace:${NC}"
kubectl get namespace "$NAMESPACE"
echo ""

echo -e "${BLUE}Deployments:${NC}"
kubectl get deployments -n "$NAMESPACE"
echo ""

echo -e "${BLUE}StatefulSets:${NC}"
kubectl get statefulsets -n "$NAMESPACE"
echo ""

echo -e "${BLUE}Services:${NC}"
kubectl get services -n "$NAMESPACE"
echo ""

echo -e "${BLUE}Pods:${NC}"
kubectl get pods -n "$NAMESPACE"
echo ""

echo -e "${GREEN}=========================================="
echo "Deployment completed successfully!"
echo "==========================================${NC}"
echo ""

echo "Next steps:"
echo "1. Add to /etc/hosts: 127.0.0.1 api.library.local"
echo "2. View logs: kubectl logs -f -n library deployment/user-service"
echo "3. Port forward: kubectl port-forward -n library svc/user-service 8000:8000"
echo "4. Check ingress: kubectl get ingress -n library"
