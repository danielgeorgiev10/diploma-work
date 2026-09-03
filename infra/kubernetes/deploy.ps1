#!/bin/pwsh

# Kubernetes deployment script for Library Management Platform
# PowerShell version for Windows

$namespace = "library"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "=========================================="
Write-Host "Library Management Platform - K8s Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Cyan
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "Error: kubectl is not installed" -ForegroundColor Red
    exit 1
}

try {
    kubectl cluster-info | Out-Null
} catch {
    Write-Host "Error: Cannot connect to Kubernetes cluster" -ForegroundColor Red
    exit 1
}
Write-Host "✓ kubectl is installed and connected" -ForegroundColor Green
Write-Host ""

# Helper function to wait for pods
function Wait-ForPods {
    param(
        [string]$Label,
        [int]$TimeoutSeconds = 300
    )
    
    Write-Host "Waiting for pods ($Label) to be ready..."
    $timeout = (Get-Date).AddSeconds($TimeoutSeconds)
    
    while ((Get-Date) -lt $timeout) {
        $ready = kubectl get pods -n $namespace -l $Label -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>$null
        
        if ($ready -and $ready -notmatch "False") {
            Write-Host "✓ Pods are ready ($Label)" -ForegroundColor Green
            return $true
        }
        
        Start-Sleep -Seconds 5
    }
    
    Write-Host "⚠ Timeout waiting for pods ($Label)" -ForegroundColor Yellow
    return $false
}

# Step 1: Create namespace
Write-Host "Step 1: Creating namespace..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/namespace.yaml"
Start-Sleep -Seconds 2
Write-Host ""

# Step 2: Deploy PostgreSQL
Write-Host "Step 2: Deploying PostgreSQL..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/postgres/secret.yaml"
kubectl apply -f "$scriptDir/postgres/configmap.yaml"
kubectl apply -f "$scriptDir/postgres/init-configmap.yaml"
kubectl apply -f "$scriptDir/postgres/statefulset.yaml"
kubectl apply -f "$scriptDir/postgres/service.yaml"
Wait-ForPods "app=postgres"
Write-Host ""

# Step 3: Deploy Redis
Write-Host "Step 3: Deploying Redis..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/redis/pvc.yaml"
kubectl apply -f "$scriptDir/redis/deployment.yaml"
kubectl apply -f "$scriptDir/redis/service.yaml"
Wait-ForPods "app=redis"
Write-Host ""

# Step 4: Deploy User Service
Write-Host "Step 4: Deploying User Service..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/services/user-service/"
Wait-ForPods "app=user-service"
Write-Host ""

# Step 5: Deploy Book Service
Write-Host "Step 5: Deploying Book Service..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/services/book-service/"
Wait-ForPods "app=book-service"
Write-Host ""

# Step 6: Deploy Loan Service
Write-Host "Step 6: Deploying Loan Service..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/services/loan-service/"
Wait-ForPods "app=loan-service"
Write-Host ""

# Step 7: Deploy Frontend
Write-Host "Step 7: Deploying Frontend..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/frontend-deployment.yaml"
Wait-ForPods "app=frontend"

# Step 8: Deploy Ingress & Network Policies
Write-Host "Step 8: Deploying Ingress and Network Policies..." -ForegroundColor Cyan
kubectl apply -f "$scriptDir/ingress/"
Write-Host "✓ Ingress and Network Policies deployed" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host "Deployment Summary" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Yellow
Write-Host ""

Write-Host "Namespace:" -ForegroundColor Cyan
kubectl get namespace $namespace
Write-Host ""

Write-Host "Deployments:" -ForegroundColor Cyan
kubectl get deployments -n $namespace
Write-Host ""

Write-Host "StatefulSets:" -ForegroundColor Cyan
kubectl get statefulsets -n $namespace
Write-Host ""

Write-Host "Services:" -ForegroundColor Cyan
kubectl get services -n $namespace
Write-Host ""

Write-Host "Pods:" -ForegroundColor Cyan
kubectl get pods -n $namespace
Write-Host ""

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Add to hosts file: 127.0.0.1 api.library.local"
Write-Host "2. View logs: kubectl logs -f -n library deployment/user-service"
Write-Host "3. Port forward: kubectl port-forward -n library svc/user-service 8000:8000"
Write-Host "4. Check ingress: kubectl get ingress -n library"
