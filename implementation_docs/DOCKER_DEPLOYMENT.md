# Docker Deployment Guide

## Quick Start with Docker Compose

### 1. Build and Run

```bash
# Build the Docker image and start the container
docker-compose up --build -d

# View logs
docker-compose logs -f ngrs-api

# Stop the container
docker-compose down
```

### 2. Test the API

```bash
# Health check
curl http://localhost:8080/health

# Get version
curl http://localhost:8080/version

# Solve with file
curl -X POST \
  -F "file=@input/input_realistic.json" \
  http://localhost:8080/solve
```

### 3. Access Interactive Docs

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

---

## Manual Docker Setup

### 1. Build Image

```bash
docker build -t ngrs-solver-api:latest .
```

### 2. Run Container

**Development:**
```bash
docker run -it --rm \
  -p 8080:8080 \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -e PORT=8080 \
  ngrs-solver-api:latest
```

**Production:**
```bash
docker run -d \
  --name ngrs-solver-api \
  -p 8080:8080 \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  -e CORS_ORIGINS="http://app.example.com" \
  --restart unless-stopped \
  --memory 2g \
  --cpus 2 \
  ngrs-solver-api:latest
```

### 3. Container Management

```bash
# View container logs
docker logs -f ngrs-solver-api

# Check container status
docker ps | grep ngrs-solver-api

# Stop container
docker stop ngrs-solver-api

# Remove container
docker rm ngrs-solver-api

# View container details
docker inspect ngrs-solver-api
```

---

## Configuration

### Environment Variables

Set these when running the container:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | API server port (don't change unless mapped) |
| `CORS_ORIGINS` | localhost | Comma-separated allowed CORS origins |

**Example:**
```bash
docker run -d \
  -p 8080:8080 \
  -e CORS_ORIGINS="https://app.example.com,https://api.example.com" \
  ngrs-solver-api:latest
```

### Volume Mounts

Mount directories for file I/O:

| Path | Type | Description |
|------|------|-------------|
| `/app/input` | ro (read-only) | Input JSON files |
| `/app/output` | rw (read-write) | Solution output files |

**Example:**
```bash
docker run -d \
  -p 8080:8080 \
  -v ~/scheduling/input:/app/input:ro \
  -v ~/scheduling/output:/app/output \
  ngrs-solver-api:latest
```

### Resource Limits

The docker-compose file limits resources:
- CPU: 2 cores limit, 1 core reserved
- Memory: 2GB limit, 1GB reserved

Adjust in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '4'          # Increase CPU limit
      memory: 4G         # Increase memory limit
    reservations:
      cpus: '2'
      memory: 2G
```

---

## Networking

### Port Mapping

Default: Container port 8080 → Host port 8080

Change with `-p` flag:
```bash
docker run -p 9000:8080 ngrs-solver-api:latest
# API available at http://localhost:9000
```

### Docker Compose Network

Containers in docker-compose use an internal network:
- Service name: `ngrs-api`
- Port: 8080 (internal)
- External access: http://localhost:8080

### CORS Configuration

For frontend access from different origin:

```bash
docker run -d \
  -p 8080:8080 \
  -e CORS_ORIGINS="http://localhost:3000,https://app.example.com" \
  ngrs-solver-api:latest
```

Update in `docker-compose.yml`:
```yaml
environment:
  - CORS_ORIGINS=http://localhost:3000,https://app.example.com
```

---

## Production Deployment

### 1. Push to Registry

```bash
# Tag for registry
docker tag ngrs-solver-api:latest myregistry.azurecr.io/ngrs-solver-api:v1.0.0

# Push
docker push myregistry.azurecr.io/ngrs-solver-api:v1.0.0
```

### 2. Deploy to Cloud

**Azure Container Instances:**
```bash
az container create \
  --resource-group mygroup \
  --name ngrs-solver-api \
  --image myregistry.azurecr.io/ngrs-solver-api:v1.0.0 \
  --cpu 2 \
  --memory 2 \
  --ports 8080 \
  --registry-login-server myregistry.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --environment-variables PORT=8080 CORS_ORIGINS="https://app.example.com"
```

**AWS ECS:**
1. Push to ECR
2. Create ECS task definition
3. Create ECS service
4. Set environment variables in task definition

**Kubernetes:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ngrs-solver-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ngrs-solver-api
  template:
    metadata:
      labels:
        app: ngrs-solver-api
    spec:
      containers:
      - name: api
        image: ngrs-solver-api:latest
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        - name: CORS_ORIGINS
          value: "https://app.example.com"
        resources:
          requests:
            memory: "1Gi"
            cpu: "1"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

### 3. Reverse Proxy (nginx)

Create `nginx.conf`:
```nginx
upstream ngrs_api {
    server ngrs-api:8080;
}

server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://ngrs_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running solves
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

Then in docker-compose, uncomment and configure the nginx service.

---

## Health Checks and Monitoring

### Built-in Health Check

```bash
curl -i http://localhost:8080/health
# Returns: {"status": "ok"}
```

The docker-compose file includes a health check that runs every 30 seconds.

### Monitoring Endpoints

```bash
# Get version
curl http://localhost:8080/version

# View API docs
curl http://localhost:8080/openapi.json
```

### Container Logs

```bash
# View all logs
docker logs ngrs-solver-api

# Follow logs in real-time
docker logs -f ngrs-solver-api

# Last 100 lines
docker logs --tail 100 ngrs-solver-api

# Logs from last 5 minutes
docker logs --since 5m ngrs-solver-api
```

### Check Container Health

```bash
# Using docker inspect
docker inspect --format='{{.State.Health.Status}}' ngrs-solver-api

# Expected output: healthy, unhealthy, or none
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs ngrs-solver-api

# Common issues:
# - Port 8080 already in use: docker run -p 9000:8080
# - Memory insufficient: Check `docker stats`
# - Missing dependencies: Check Dockerfile COPY commands
```

### High Memory Usage

```bash
# Monitor resource usage
docker stats ngrs-solver-api

# Reduce resource limits in docker-compose.yml
# Or increase available resources on host
```

### Connection Refused

```bash
# Verify container is running
docker ps | grep ngrs-solver-api

# Check port mapping
docker port ngrs-solver-api

# Test from inside container
docker exec ngrs-solver-api curl http://localhost:8080/health
```

### Solver Timeouts in Container

Increase timeout on host machine:
```bash
# In docker run/docker-compose
-e SOLVER_TIME_LIMIT=60
```

Then in API call:
```bash
curl -X POST \
  -F "file=@input.json" \
  "http://localhost:8080/solve?time_limit=60"
```

---

## Performance Tips

### 1. Multi-Process Worker Pool

The default CMD uses single process. For multiple workers:

```dockerfile
# In Dockerfile
CMD ["python", "-m", "uvicorn", "src.api_server:app", \
     "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

### 2. Reverse Proxy Load Balancing

Use nginx with multiple container instances:
```bash
docker-compose up --scale ngrs-api=3
```

### 3. Caching Layer

For development, mount volumes to avoid rebuilds:
```bash
docker-compose up --no-cache  # Force rebuild
docker-compose up             # Use cache
```

---

## Image Size Optimization

Current image: ~1GB (with dependencies)

To reduce:
1. Use Python 3.11-alpine instead of slim
2. Install only required system packages
3. Use multi-stage build

See advanced Dockerfile options in deployment docs.

---

## Clean Up

```bash
# Remove container
docker rm ngrs-solver-api

# Remove image
docker rmi ngrs-solver-api:latest

# Remove dangling images
docker image prune

# Remove all unused resources
docker system prune -a
```

---

## Next Steps

1. **Local Testing**: `docker-compose up -d`
2. **Push to Registry**: Build and push image to container registry
3. **Deploy**: Use cloud provider's container service or Kubernetes
4. **Monitor**: Set up logging, metrics, and alerting

For detailed API usage, see [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
