# NGRS API - Quick Reference Card

## 🚀 Start Server

```bash
# Development
./run_api_server.sh dev

# Production  
./run_api_server.sh prod

# Docker
docker-compose up -d
```

## 📍 Endpoints

### Health Check
```bash
curl http://localhost:8080/health
# → {"status": "ok"}
```

### Get Version
```bash
curl http://localhost:8080/version
# → {"apiVersion": "0.1.0", "solverVersion": "optfold-py-0.4.2", ...}
```

### Solve Problem
```bash
# Via file upload
curl -X POST -F "file=@input.json" \
  http://localhost:8080/solve

# Via JSON body
curl -X POST -H "Content-Type: application/json" \
  -d '{"input_json": {...}}' \
  http://localhost:8080/solve

# With time limit
curl -X POST -F "file=@input.json" \
  "http://localhost:8080/solve?time_limit=30"
```

## 📊 Response Format

```json
{
  "solverRun": {
    "status": "OPTIMAL",
    "solveTimeMs": 12345,
    "feasible": true
  },
  "score": {
    "hard": 0,
    "soft": 457.8
  },
  "assignments": [{
    "personId": "P001",
    "slotId": "S001"
  }],
  "violations": [],
  "meta": {
    "requestId": "uuid",
    "processingTimeMs": 12500
  }
}
```

## 🔧 Configuration

| Env Var | Default | Example |
|---------|---------|---------|
| `PORT` | 8080 | `export PORT=9000` |
| `CORS_ORIGINS` | localhost | `export CORS_ORIGINS="http://localhost:3000"` |

## 📚 Documentation

- **Full API Docs**: [API_DOCUMENTATION.md](./implementation_docs/API_DOCUMENTATION.md)
- **Docker Guide**: [DOCKER_DEPLOYMENT.md](./implementation_docs/DOCKER_DEPLOYMENT.md)
- **Integration**: [FASTAPI_INTEGRATION.md](./implementation_docs/FASTAPI_INTEGRATION.md)

## 🌐 Interactive Docs

Once server is running:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 📦 Docker Commands

```bash
# Build
docker build -t ngrs-solver-api .

# Run
docker run -p 8080:8080 ngrs-solver-api

# Compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

## ⚙️ Query Parameters

| Param | Default | Range | Purpose |
|-------|---------|-------|---------|
| `time_limit` | 15 | 1-120 | Solve time in seconds |
| `strict` | 0 | 0-1 | Error if input provided twice |
| `validate` | 0 | 0-1 | Validate against schema |

## 🐍 Python Client

```python
import requests

response = requests.post(
    'http://localhost:8080/solve',
    files={'file': open('input.json', 'rb')},
    params={'time_limit': 30},
    timeout=60
)

result = response.json()
print(f"Status: {result['solverRun']['status']}")
print(f"Score: {result['score']['total']}")
```

## 🎯 Status Codes

| Code | Meaning |
|------|---------|
| 200 | Solution found (any solver status) |
| 400 | Bad request (missing input) |
| 422 | Invalid JSON |
| 500 | Server error |

## 🔍 Error Example

```bash
# Missing input
curl http://localhost:8080/solve

# Response
{"detail": "Provide either input_json in request body or upload a JSON file."}
```

## 🧪 Test Command

```bash
# Full solve test
curl -X POST \
  -F "file=@input/input_realistic.json" \
  "http://localhost:8080/solve?time_limit=30" | jq '.'
```

## 🛠️ Troubleshooting

```bash
# Port in use?
lsof -i :8080

# Check logs
docker logs ngrs-solver-api

# Health check
curl -v http://localhost:8080/health

# View API schema
curl http://localhost:8080/openapi.json | jq '.'
```

## 📋 File Locations

| Item | Location |
|------|----------|
| API Server | `src/api_server.py` |
| Models | `src/models.py` |
| Output Builder | `src/output_builder.py` |
| Dockerfile | `Dockerfile` |
| Docker Compose | `docker-compose.yml` |
| API Docs | `implementation_docs/API_DOCUMENTATION.md` |
| Startup Script | `run_api_server.sh` |

## ⏱️ Performance Tips

- **Time Limit**: 15-30 sec for typical problems
- **HTTP Timeout**: Set 2x solver timeout
- **Workers**: Use `--workers 4` for production
- **Memory**: Reserve 1-2GB per worker

## 🎁 Sample Input File

Use any of these to test:
- `input/input_realistic.json`
- `input/input_monthly_ot_test.json`
- `input/input_enhanced.json`

All are in the workspace root.

---

**For detailed information, see documentation in `implementation_docs/`** 📖
