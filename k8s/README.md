# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the OpenSearch-Docling-GraphRAG application.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Sufficient cluster resources (minimum 8GB RAM, 4 CPU cores)
- Storage provisioner for PersistentVolumes
- (Optional) Ingress controller (nginx)
- (Optional) cert-manager for TLS certificates

## Deployment Steps

### 1. Create Namespace

```bash
kubectl apply -f namespace.yaml
```

### 2. Create ConfigMap and Secrets

**Important:** Update `secrets.yaml` with your actual credentials before applying.

```bash
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml
```

### 3. Deploy OpenSearch

```bash
kubectl apply -f opensearch-deployment.yaml
```

Wait for OpenSearch to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=opensearch -n docling-rag --timeout=300s
```

### 4. Deploy Neo4j

```bash
kubectl apply -f neo4j-deployment.yaml
```

Wait for Neo4j to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=neo4j -n docling-rag --timeout=300s
```

### 5. Deploy Application

**Important:** Update the image in `app-deployment.yaml` with your container registry.

```bash
# Build and push your Docker image first
docker build -t your-registry/docling-rag:latest .
docker push your-registry/docling-rag:latest

# Deploy the application
kubectl apply -f app-deployment.yaml
```

### 6. Verify Deployment

```bash
# Check all pods
kubectl get pods -n docling-rag

# Check services
kubectl get svc -n docling-rag

# Check ingress (if configured)
kubectl get ingress -n docling-rag
```

## Accessing the Application

### Using LoadBalancer

If your cluster supports LoadBalancer services:

```bash
kubectl get svc docling-app-service -n docling-rag
```

Access the application at the EXTERNAL-IP on port 8501.

### Using Port Forward

For local testing:

```bash
kubectl port-forward -n docling-rag svc/docling-app-service 8501:8501
```

Then access: http://localhost:8501

### Using Ingress

If you configured the Ingress:

1. Update the host in `app-deployment.yaml` with your domain
2. Ensure your DNS points to the Ingress controller
3. Access: https://docling-rag.yourdomain.com

## Scaling

Scale the application:

```bash
kubectl scale deployment docling-app -n docling-rag --replicas=3
```

## Monitoring

View logs:

```bash
# Application logs
kubectl logs -f -l app=docling-app -n docling-rag

# OpenSearch logs
kubectl logs -f -l app=opensearch -n docling-rag

# Neo4j logs
kubectl logs -f -l app=neo4j -n docling-rag
```

## Updating

Update the application:

```bash
# Build and push new image
docker build -t your-registry/docling-rag:v2 .
docker push your-registry/docling-rag:v2

# Update deployment
kubectl set image deployment/docling-app docling-app=your-registry/docling-rag:v2 -n docling-rag

# Or apply updated manifest
kubectl apply -f app-deployment.yaml
```

## Cleanup

Remove all resources:

```bash
kubectl delete namespace docling-rag
```

Or remove individual components:

```bash
kubectl delete -f app-deployment.yaml
kubectl delete -f neo4j-deployment.yaml
kubectl delete -f opensearch-deployment.yaml
kubectl delete -f configmap.yaml
kubectl delete -f secrets.yaml
kubectl delete -f namespace.yaml
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n docling-rag
kubectl logs <pod-name> -n docling-rag
```

### Storage issues

Check PVC status:
```bash
kubectl get pvc -n docling-rag
```

### Network issues

Check services and endpoints:
```bash
kubectl get svc -n docling-rag
kubectl get endpoints -n docling-rag
```

## Resource Requirements

Minimum cluster resources:

- **OpenSearch**: 1Gi RAM, 500m CPU
- **Neo4j**: 1Gi RAM, 500m CPU
- **Application**: 2Gi RAM, 1000m CPU (per replica)
- **Storage**: ~30Gi total

## Notes

- The application requires Ollama to be running separately (not included in these manifests)
- Update the `OLLAMA_BASE_URL` in secrets.yaml to point to your Ollama instance
- For production, use proper secrets management (e.g., Sealed Secrets, External Secrets Operator)
- Configure resource limits based on your workload
- Enable monitoring and logging for production deployments