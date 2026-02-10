# Deployment Guide

This guide covers various deployment scenarios for the OpenSearch-Docling-GraphRAG application.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployments](#cloud-deployments)
- [Production Considerations](#production-considerations)

## Local Development

### Prerequisites

- Python 3.11+
- Ollama installed and running
- Docker (for services)
- 8GB+ RAM

### Setup Steps

1. **Clone and Setup**

```bash
git clone <repository-url>
cd opensearch-docling-graphrag
cp .env.example .env
```

2. **Configure Environment**

Edit `.env` file:
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=ibm/granite4:latest
OLLAMA_EMBEDDING_MODEL=granite-embedding:278m
```

3. **Install Ollama Models**

```bash
ollama pull ibm/granite4:latest
ollama pull granite-embedding:278m
```

4. **Start Application**

```bash
./start.sh
```

Access at: http://localhost:8501

## Docker Deployment

### Single Container

Build and run the application container:

```bash
# Build image
docker build -t docling-rag:latest .

# Run container
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  --name docling-app \
  docling-rag:latest
```

### Docker Compose (Recommended)

Complete stack with all services:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

Services included:
- Application (port 8501)
- OpenSearch (port 9200)
- OpenSearch Dashboards (port 5601)
- Neo4j (ports 7474, 7687)

### Docker Compose Configuration

```yaml
# docker-compose.yml highlights
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    volumes:
      - ./input:/app/input
      - ./output:/app/output
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- 16GB+ cluster memory
- Storage provisioner

### Quick Deploy

```bash
# Apply all manifests
kubectl apply -f k8s/

# Wait for pods
kubectl wait --for=condition=ready pod --all -n docling-rag --timeout=300s

# Get service URL
kubectl get svc docling-app-service -n docling-rag
```

### Step-by-Step Deployment

1. **Create Namespace**

```bash
kubectl apply -f k8s/namespace.yaml
```

2. **Configure Secrets**

Edit `k8s/secrets.yaml` with your credentials:

```yaml
stringData:
  OPENSEARCH_PASSWORD: "YourSecurePassword"
  NEO4J_PASSWORD: "YourNeo4jPassword"
```

Apply:
```bash
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
```

3. **Deploy Services**

```bash
# OpenSearch
kubectl apply -f k8s/opensearch-deployment.yaml

# Wait for OpenSearch
kubectl wait --for=condition=ready pod -l app=opensearch -n docling-rag --timeout=300s

# Neo4j
kubectl apply -f k8s/neo4j-deployment.yaml

# Wait for Neo4j
kubectl wait --for=condition=ready pod -l app=neo4j -n docling-rag --timeout=300s
```

4. **Deploy Application**

Update image in `k8s/app-deployment.yaml`:

```yaml
spec:
  containers:
  - name: app
    image: your-registry/docling-rag:latest
```

Deploy:
```bash
kubectl apply -f k8s/app-deployment.yaml
```

5. **Access Application**

```bash
# Port forward
kubectl port-forward -n docling-rag svc/docling-app-service 8501:8501

# Or get LoadBalancer IP
kubectl get svc docling-app-service -n docling-rag
```

### Scaling

```bash
# Scale application
kubectl scale deployment docling-app -n docling-rag --replicas=3

# Auto-scaling
kubectl autoscale deployment docling-app -n docling-rag \
  --min=2 --max=10 --cpu-percent=70
```

## Cloud Deployments

### AWS EKS

1. **Create EKS Cluster**

```bash
eksctl create cluster \
  --name docling-rag \
  --region us-west-2 \
  --nodegroup-name standard-workers \
  --node-type t3.xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5
```

2. **Configure Storage**

```bash
# Install EBS CSI driver
kubectl apply -k "github.com/kubernetes-sigs/aws-ebs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"
```

3. **Deploy Application**

```bash
kubectl apply -f k8s/
```

4. **Configure Load Balancer**

```bash
# Install AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=docling-rag
```

### Google GKE

1. **Create GKE Cluster**

```bash
gcloud container clusters create docling-rag \
  --zone us-central1-a \
  --machine-type n1-standard-4 \
  --num-nodes 3 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 5
```

2. **Get Credentials**

```bash
gcloud container clusters get-credentials docling-rag --zone us-central1-a
```

3. **Deploy Application**

```bash
kubectl apply -f k8s/
```

### Azure AKS

1. **Create AKS Cluster**

```bash
az aks create \
  --resource-group docling-rag-rg \
  --name docling-rag \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 5
```

2. **Get Credentials**

```bash
az aks get-credentials --resource-group docling-rag-rg --name docling-rag
```

3. **Deploy Application**

```bash
kubectl apply -f k8s/
```

## Production Considerations

### High Availability

1. **Multiple Replicas**

```yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

2. **Pod Disruption Budget**

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: docling-app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: docling-app
```

### Security

1. **Network Policies**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: docling-app-netpol
spec:
  podSelector:
    matchLabels:
      app: docling-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-nginx
    ports:
    - protocol: TCP
      port: 8501
```

2. **Secrets Management**

Use external secrets management:

```bash
# Install External Secrets Operator
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace
```

3. **TLS/SSL**

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: docling-rag-cert
spec:
  secretName: docling-rag-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - docling-rag.yourdomain.com
```

### Monitoring

1. **Prometheus & Grafana**

```bash
# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Access Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

2. **Application Metrics**

Add to `app.py`:

```python
from prometheus_client import Counter, Histogram
import time

request_count = Counter('app_requests_total', 'Total requests')
request_duration = Histogram('app_request_duration_seconds', 'Request duration')

@request_duration.time()
def process_document(file):
    request_count.inc()
    # ... processing logic
```

### Logging

1. **ELK Stack**

```bash
# Install Elasticsearch
helm install elasticsearch elastic/elasticsearch -n logging --create-namespace

# Install Kibana
helm install kibana elastic/kibana -n logging

# Install Filebeat
helm install filebeat elastic/filebeat -n logging
```

2. **Fluentd**

```bash
helm install fluentd fluent/fluentd -n logging
```

### Backup & Recovery

1. **Database Backups**

```bash
# OpenSearch snapshot
curl -X PUT "localhost:9200/_snapshot/backup_repo" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/backup"
  }
}'

# Neo4j backup
docker exec neo4j neo4j-admin backup --backup-dir=/backup
```

2. **Persistent Volume Snapshots**

```bash
# Create VolumeSnapshot
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: opensearch-snapshot
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: opensearch-pvc
EOF
```

### Performance Tuning

1. **Resource Limits**

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

2. **Horizontal Pod Autoscaling**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: docling-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: docling-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Cost Optimization

1. **Node Affinity**

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 1
      preference:
        matchExpressions:
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
          - t3.large
          - t3.xlarge
```

2. **Spot Instances**

```yaml
tolerations:
- key: "spot"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

## Troubleshooting

### Common Issues

1. **Pods Not Starting**

```bash
kubectl describe pod <pod-name> -n docling-rag
kubectl logs <pod-name> -n docling-rag
```

2. **Service Connection Issues**

```bash
kubectl get endpoints -n docling-rag
kubectl exec -it <pod-name> -n docling-rag -- curl http://opensearch-service:9200
```

3. **Storage Issues**

```bash
kubectl get pvc -n docling-rag
kubectl describe pvc <pvc-name> -n docling-rag
```

### Health Checks

```bash
# Application health
curl http://localhost:8501/_stcore/health

# OpenSearch health
curl -u admin:password http://localhost:9200/_cluster/health

# Neo4j health
curl http://localhost:7474/db/data/
```

## Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/docling-app -n docling-rag

# Rollback to specific revision
kubectl rollout undo deployment/docling-app -n docling-rag --to-revision=2

# Check rollout history
kubectl rollout history deployment/docling-app -n docling-rag