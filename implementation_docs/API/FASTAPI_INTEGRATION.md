# FastAPI Server Integration Guide

## Overview

The NGRS Solver now includes a production-ready FastAPI REST API server (`src/api_server.py`) that wraps the core solving engine and provides:

✅ RESTful endpoints for submitting and solving problems  
✅ Interactive Swagger UI documentation  
✅ Request/response validation with Pydantic  
✅ Request tracing with unique IDs  
✅ CORS support for web frontends  
✅ Docker containerization for easy deployment  
✅ Multi-process scaling for production use  

---

## Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI Application              │
│  src/api_server.py                      │
├─────────────────────────────────────────┤
│ • HTTP Request Handling                  │
│ • Input Validation (Pydantic)            │
│ • Request/Response Serialization         │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│      Data Loading & Processing           │
│  context/engine/data_loader.py          │
├─────────────────────────────────────────┤
│ • Parse JSON input                       │
│ • Validate domain constraints            │
│ • Build internal context                 │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│         Solver Engine                    │
│  context/engine/solver_engine.py        │
├─────────────────────────────────────────┤
│ • OptFold solver integration             │
│ • Constraint application                 │
│ • Solution optimization                  │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│      Solution Post-Processing            │
│  src/output_builder.py                  │
├─────────────────────────────────────────┤
│ • Violation detection                    │
│ • Score calculation                      │
│ • Result formatting                      │
└─────────────────────────────────────────┘
```

---

## Project Structure

```
ngrssolver/
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydantic models
│   ├── api_server.py          # FastAPI app
│   ├── output_builder.py      # Solution post-processing
│   └── config.py              # Configuration
├── context/
│   ├── engine/
│   │   ├── solver_engine.py   # Core solver
│   │   ├── data_loader.py     # Input loading
│   │   └── ...
│   ├── constraints/           # Constraint implementations
│   └── ...
├── Dockerfile                 # Container image definition
├── docker-compose.yml         # Multi-container orchestration
├── run_api_server.sh          # Convenience startup script
├── pyproject.toml             # Python dependencies
└── implementation_docs/
    ├── API_DOCUMENTATION.md   # API reference
    └── DOCKER_DEPLOYMENT.md   # Deployment guide
```

---

## Quick Start

### 1. Start the Server

**Development:**
```bash
cd ngrssolver
python -m uvicorn src.api_server:app --reload --port 8080
```

**Or use the convenience script:**
```bash
./run_api_server.sh dev 8080
```

**Production:**
```bash
./run_api_server.sh prod 8080
```

### 2. Access Interactive Docs

Open in browser:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### 3. Test with cURL

```bash
# Health check
curl http://localhost:8080/health

# Solve with file upload
curl -X POST \
  -F "file=@input/input_realistic.json" \
  http://localhost:8080/solve
```

### 4. Verify Output

Response includes:
- Solver status (OPTIMAL, FEASIBLE, TIMEOUT, etc.)
- Schedule assignments
- Violation details
- Quality metrics

---

## Core Features

### 1. Multiple Input Methods

**JSON Body:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"input_json": {...}}' \
  http://localhost:8080/solve
```

**File Upload:**
```bash
curl -X POST \
  -F "file=@input.json" \
  http://localhost:8080/solve
```

### 2. Request Tracking

Every request gets a unique ID for logging/debugging:
```bash
curl -X POST \
  -H "X-Request-ID: my-trace-123" \
  -F "file=@input.json" \
  http://localhost:8080/solve

# Response headers include:
# X-Request-ID: my-trace-123
```

### 3. Configurable Time Limits

```bash
# 30-second time limit
curl -X POST \
  -F "file=@input.json" \
  "http://localhost:8080/solve?time_limit=30"

# Default: 15 seconds
# Min: 1 second, Max: 120 seconds
```

### 4. CORS Support

API automatically allows requests from configured origins:
```bash
export CORS_ORIGINS="http://localhost:3000,https://app.example.com"
python -m uvicorn src.api_server:app --port 8080
```

### 5. Standardized Output

All responses follow consistent schema:
```json
{
  "solverRun": {...},     // Solver metadata
  "score": {...},         // Quality metrics
  "assignments": [...],   // Schedule assignments
  "violations": [...],    // Constraint violations
  "stats": {...},         // Summary statistics
  "meta": {...}           // Request metadata
}
```

---

## Endpoints Reference

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| GET | `/version` | Version info |
| POST | `/solve` | Solve problem |
| GET | `/schema` | JSON schemas |

See [API_DOCUMENTATION.md](./implementation_docs/API_DOCUMENTATION.md) for complete reference.

---

## Docker Deployment

### Quick Start

```bash
# Build and run with docker-compose
docker-compose up --build -d

# Test
curl http://localhost:8080/health

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Manual Docker Build

```bash
# Build image
docker build -t ngrs-solver-api:latest .

# Run container
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/input:/app/input:ro \
  -v $(pwd)/output:/app/output \
  ngrs-solver-api:latest
```

See [DOCKER_DEPLOYMENT.md](./implementation_docs/DOCKER_DEPLOYMENT.md) for full deployment guide.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | API server port |
| `CORS_ORIGINS` | localhost | Comma-separated CORS allowed origins |

### Startup Options

```bash
# Development with auto-reload
python -m uvicorn src.api_server:app --reload

# Production with multiple workers
python -m uvicorn src.api_server:app --workers 4

# Custom host/port
python -m uvicorn src.api_server:app --host 0.0.0.0 --port 9000

# Debug logging
python -m uvicorn src.api_server:app --log-level debug
```

---

## Integration Examples

### Python Client

```python
import requests
import json

# Load input
with open('input/input_realistic.json') as f:
    input_data = json.load(f)

# Submit request
response = requests.post(
    'http://localhost:8080/solve',
    json={'input_json': input_data},
    params={'time_limit': 30},
    timeout=60
)

# Check result
if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['solverRun']['status']}")
    print(f"Score: {result['score']['total']}")
    print(f"Assignments: {len(result['assignments'])}")
    print(f"Violations: {len(result['violations'])}")
else:
    print(f"Error: {response.text}")
```

### JavaScript/Node.js

```javascript
const fs = require('fs');
const FormData = require('form-data');
const axios = require('axios');

// Prepare file
const form = new FormData();
form.append('file', fs.createReadStream('input/input_realistic.json'));

// Submit request
axios.post(
    'http://localhost:8080/solve?time_limit=30',
    form,
    { headers: form.getHeaders(), timeout: 60000 }
)
.then(response => {
    const result = response.data;
    console.log(`Status: ${result.solverRun.status}`);
    console.log(`Assignments: ${result.assignments.length}`);
})
.catch(error => {
    console.error('Error:', error.response?.data || error.message);
});
```

### cURL Script

```bash
#!/bin/bash

# Submit solve request
RESPONSE=$(curl -s -X POST \
  -F "file=@input/input_realistic.json" \
  "http://localhost:8080/solve?time_limit=30")

# Parse response
STATUS=$(echo "$RESPONSE" | jq -r '.solverRun.status')
SCORE=$(echo "$RESPONSE" | jq -r '.score.total')
ASSIGNMENTS=$(echo "$RESPONSE" | jq -r '.assignments | length')

echo "Status: $STATUS"
echo "Score: $SCORE"
echo "Assignments: $ASSIGNMENTS"

# Save to file
echo "$RESPONSE" | jq . > output_$(date +%s).json
```

---

## Performance & Scaling

### Single Instance

- Typical solve time: 5-15 seconds
- Memory usage: 500MB-1GB per problem
- Throughput: 1 problem at a time

### Multi-Process (Production)

```bash
# Use 4 worker processes
python -m uvicorn src.api_server:app --workers 4 --port 8080
```

- Throughput: Up to 4 concurrent requests
- Each worker can solve independently

### Load Balancing

With Docker Compose:
```bash
docker-compose up --scale ngrs-api=3
```

Use nginx or cloud load balancer to distribute requests across containers.

### Resource Requirements

- **CPU**: 1-2 cores per worker
- **Memory**: 1-2GB per worker (solver can require ~1GB)
- **Disk**: 100MB for code, plus I/O for input/output files

---

## Monitoring & Logging

### Health Checks

```bash
# Endpoint health
curl http://localhost:8080/health

# Version info
curl http://localhost:8080/version

# Container health (docker)
docker inspect --format='{{.State.Health.Status}}' ngrs-solver-api
```

### View Logs

```bash
# Standard output (development)
# Logs appear in console

# Docker logs
docker logs -f ngrs-solver-api

# Grep by request ID
grep "requestId=550e8400-e29b-41d4-a716-446655440000" <logfile>
```

### Request Tracing

Every request is logged with:
- Request ID (UUID)
- Endpoint
- Solver status
- Score details
- Processing time

Example log:
```
2025-01-12 14:30:45.123 - ngrs.api - INFO - solve requestId=550e8400-e29b-41d4-a716-446655440000 status=OPTIMAL hard=0 soft=457.8 assignments=798 durMs=12500
```

---

## Error Handling

### Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| 400 | Missing input | Provide `input_json` or file |
| 422 | Invalid JSON | Check JSON syntax |
| 500 | Solver error | Check logs for details |

### Error Response Format

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

Check `meta.requestId` in response to trace in logs.

---

## Development

### Project Files

- **`src/models.py`**: Pydantic request/response models
- **`src/api_server.py`**: FastAPI application and endpoints
- **`src/output_builder.py`**: Solution post-processing
- **`src/config.py`**: Configuration and settings

### Adding New Endpoints

1. Add model in `src/models.py`
2. Add endpoint in `src/api_server.py`
3. Test via Swagger UI at `/docs`
4. Update `API_DOCUMENTATION.md`

### Testing

```bash
# Unit tests (if applicable)
pytest tests/

# Manual testing via Swagger UI
# Visit http://localhost:8080/docs

# cURL testing (see examples above)
```

---

## Production Deployment

### Checklist

- [ ] Install all dependencies: `pip install -r requirements.txt`
- [ ] Set environment variables (CORS_ORIGINS, PORT)
- [ ] Use multi-process workers (--workers 4+)
- [ ] Enable health checks
- [ ] Set up logging/monitoring
- [ ] Configure reverse proxy (nginx)
- [ ] Use HTTPS/TLS in production
- [ ] Implement rate limiting (if needed)
- [ ] Set resource limits (memory, CPU)
- [ ] Test with realistic problem sizes

### Deployment Options

1. **Local Development**
   ```bash
   ./run_api_server.sh dev
   ```

2. **Docker (Local/Cloud)**
   ```bash
   docker-compose up -d
   ```

3. **Cloud Platforms**
   - AWS: ECS, App Runner, Lambda
   - Azure: Container Instances, App Service
   - Google Cloud: Cloud Run, GKE
   - Heroku, Railway, etc.

See [DOCKER_DEPLOYMENT.md](./implementation_docs/DOCKER_DEPLOYMENT.md) for detailed guides.

---

## Troubleshooting

### Port Already in Use

```bash
# Use different port
python -m uvicorn src.api_server:app --port 9000

# Or kill process using port 8080
# (macOS)
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs kill
```

### Memory Errors

```bash
# Reduce concurrency or increase available memory
# Check solver complexity vs available resources
```

### Solver Timeout

```bash
# Increase time limit
curl -X POST \
  -F "file=@input.json" \
  "http://localhost:8080/solve?time_limit=60"
```

### CORS Errors

```bash
# Set correct CORS_ORIGINS
export CORS_ORIGINS="http://localhost:3000"
python -m uvicorn src.api_server:app --port 8080
```

---

## Next Steps

1. **Start Server**: `./run_api_server.sh dev`
2. **Test API**: Visit http://localhost:8080/docs
3. **Try Examples**: Use sample input files
4. **Integrate**: Connect frontend or application
5. **Deploy**: Use Docker for production

---

## Resources

- **API Reference**: [API_DOCUMENTATION.md](./implementation_docs/API_DOCUMENTATION.md)
- **Docker Guide**: [DOCKER_DEPLOYMENT.md](./implementation_docs/DOCKER_DEPLOYMENT.md)
- **Quick Start**: [QUICKSTART.md](./implementation_docs/QUICKSTART.md)
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Uvicorn Docs**: https://www.uvicorn.org/

---

## Support

For issues or questions:
1. Check logs: `docker logs -f ngrs-solver-api` or console output
2. Review API docs: http://localhost:8080/docs
3. Check request ID for correlation
4. See DOCKER_DEPLOYMENT.md troubleshooting section
