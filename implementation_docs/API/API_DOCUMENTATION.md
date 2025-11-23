# NGRS Solver REST API Documentation

## Overview

The NGRS Solver REST API provides a simple interface to submit scheduling problems and receive optimized solutions. The API is built with [FastAPI](https://fastapi.tiangolo.com/) and follows REST conventions.

## Getting Started

### Start the Server

**Development:**
```bash
cd ngrssolver
python -m uvicorn src.api_server:app --reload --port 8080
```

Or use the convenience script:
```bash
./run_api_server.sh dev 8080
```

**Production:**
```bash
./run_api_server.sh prod 8080
```

This will:
- Start the API on `http://localhost:8080`
- Serve interactive API docs at `http://localhost:8080/docs` (Swagger UI)
- Serve alternative docs at `http://localhost:8080/redoc` (ReDoc)

### Quick Test

```bash
# Health check
curl http://localhost:8080/health

# Get version info
curl http://localhost:8080/version

# Solve with a JSON file
curl -X POST \
  -F "file=@input/input_realistic.json" \
  http://localhost:8080/solve
```

## Core Endpoints

### 1. Health Check
```http
GET /health
```

Returns server status.

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

### 2. Version Information
```http
GET /version
```

Get API and solver version information.

**Response (200 OK):**
```json
{
  "apiVersion": "0.1.0",
  "solverVersion": "optfold-py-0.4.2",
  "schemaVersion": "0.43",
  "timestamp": "2025-01-12T14:30:45.123456"
}
```

---

### 3. Solve Scheduling Problem
```http
POST /solve
```

Submit a scheduling problem and receive an optimized solution.

#### Input Methods

**Option A: JSON in Request Body**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"input_json": {...}}' \
  http://localhost:8080/solve
```

**Option B: File Upload**
```bash
curl -X POST \
  -F "file=@input/input_realistic.json" \
  http://localhost:8080/solve
```

**Option C: File + Query Parameters**
```bash
curl -X POST \
  -F "file=@input/input_realistic.json" \
  "http://localhost:8080/solve?time_limit=30&strict=0&validate=1"
```

#### Query Parameters

| Parameter   | Type | Default | Range      | Description |
|-------------|------|---------|-----------|-------------|
| `time_limit` | int  | 15      | 1-120     | Maximum solver time in seconds |
| `strict`     | int  | 0       | 0-1       | If 1, error if both body and file provided |
| `validate`   | int  | 0       | 0-1       | If 1, validate input against schema |

#### Request Headers (Optional)

| Header           | Description |
|------------------|-------------|
| `X-Request-ID`   | Request ID for tracing (auto-generated if not provided) |
| `Content-Type`   | application/json (for body) or multipart/form-data (for file) |

#### Response

**Status: 200 OK** (Always for valid requests, regardless of solver status)

```json
{
  "solverRun": {
    "status": "OPTIMAL",
    "objectiveValue": 9542.0,
    "solveTimeMs": 12345,
    "timedOut": false,
    "feasible": true,
    "infeasibilityMessage": null
  },
  "score": {
    "hard": 0,
    "soft": 457.8,
    "total": 457.8
  },
  "assignments": [
    {
      "personId": "P001",
      "slotId": "S001",
      "confidence": 0.95
    }
  ],
  "violations": [
    {
      "type": "C2_max_daily_assignments",
      "personId": "P001",
      "date": "2025-01-12",
      "severity": "SOFT",
      "message": "Soft violation example"
    }
  ],
  "stats": {
    "totalPeople": 150,
    "totalSlots": 850,
    "assignedSlots": 798,
    "unassignedSlots": 52,
    "satisfactionRate": 0.94
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-12T14:30:45.123456",
    "processingTimeMs": 12500,
    "warnings": []
  }
}
```

**Status: 400 Bad Request**
```json
{
  "detail": "Provide either input_json in request body or upload a JSON file."
}
```

**Status: 422 Unprocessable Entity**
```json
{
  "detail": "Unable to parse uploaded file as JSON: Expecting value: line 1 column 1"
}
```

**Status: 500 Internal Server Error**
```json
{
  "detail": "Internal error: <error message>"
}
```

---

### 4. Get JSON Schemas
```http
GET /schema
```

Retrieve JSON schemas for input and output validation.

**Response (200 OK):**
```json
{
  "inputSchema": {
    "description": "NGRS input schema (v0.43)"
  },
  "outputSchema": {
    "description": "NGRS output schema (v0.43)"
  }
}
```

---

## Response Schema Details

### SolverRun Object
```json
{
  "status": "OPTIMAL|FEASIBLE|TIMEOUT|INFEASIBLE|ERROR",
  "objectiveValue": 9542.0,
  "solveTimeMs": 12345,
  "timedOut": false,
  "feasible": true,
  "infeasibilityMessage": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Solver completion status |
| `objectiveValue` | float | Objective value if solved |
| `solveTimeMs` | int | Actual solve time in milliseconds |
| `timedOut` | bool | Whether solver timed out |
| `feasible` | bool | Whether solution is feasible |
| `infeasibilityMessage` | string \| null | Reason for infeasibility if any |

### Score Object
```json
{
  "hard": 0,
  "soft": 457.8,
  "total": 457.8
}
```

| Field | Type | Description |
|-------|------|-------------|
| `hard` | int | Total hard constraint violations |
| `soft` | float | Total soft constraint penalty |
| `total` | float | Combined score |

### Assignment Object
```json
{
  "personId": "P001",
  "slotId": "S001",
  "confidence": 0.95
}
```

| Field | Type | Description |
|-------|------|-------------|
| `personId` | string | Person identifier |
| `slotId` | string | Slot identifier |
| `confidence` | float | Assignment confidence score (0-1) |

### Violation Object
```json
{
  "type": "C2_max_daily_assignments",
  "personId": "P001",
  "date": "2025-01-12",
  "severity": "SOFT",
  "message": "Soft violation example"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Constraint identifier |
| `personId` | string | Person involved |
| `date` | string | Date (ISO format) |
| `severity` | "HARD" \| "SOFT" | Violation severity |
| `message` | string | Human-readable description |

### Meta Object
```json
{
  "requestId": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-01-12T14:30:45.123456",
  "processingTimeMs": 12500,
  "warnings": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `requestId` | string | UUID for request tracing |
| `timestamp` | string | ISO 8601 timestamp |
| `processingTimeMs` | int | Total API processing time |
| `warnings` | string[] | Non-fatal warnings |

---

## Examples

### Example 1: Basic Solve Request

**Request:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d @input.json \
  http://localhost:8080/solve
```

Where `input.json` contains:
```json
{
  "input_json": {
    "people": [...],
    "slots": [...],
    "constraints": [...]
  }
}
```

**Response:**
```json
{
  "solverRun": {
    "status": "OPTIMAL",
    "objectiveValue": 9542.0,
    "solveTimeMs": 5234,
    "timedOut": false,
    "feasible": true,
    "infeasibilityMessage": null
  },
  "score": {
    "hard": 0,
    "soft": 457.8,
    "total": 457.8
  },
  "assignments": [...],
  "violations": [],
  "stats": {...},
  "meta": {...}
}
```

### Example 2: Upload File with Custom Time Limit

```bash
curl -X POST \
  -F "file=@input/input_realistic.json" \
  "http://localhost:8080/solve?time_limit=30"
```

### Example 3: With Request Tracking

```bash
curl -X POST \
  -H "X-Request-ID: my-request-123" \
  -F "file=@input/input_realistic.json" \
  http://localhost:8080/solve

# Response will include:
# X-Request-ID: my-request-123 (in headers)
# "requestId": "my-request-123" (in body)
```

### Example 4: Python Client

```python
import requests
import json

# Load input
with open('input/input_realistic.json') as f:
    data = json.load(f)

# Submit solve request
response = requests.post(
    'http://localhost:8080/solve',
    json={'input_json': data},
    params={'time_limit': 30}
)

# Check result
if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['solverRun']['status']}")
    print(f"Score: {result['score']['total']}")
    print(f"Assignments: {len(result['assignments'])}")
else:
    print(f"Error: {response.text}")
```

### Example 5: JavaScript/Node.js Client

```javascript
const fs = require('fs');
const FormData = require('form-data');
const axios = require('axios');

// Load input file
const form = new FormData();
form.append('file', fs.createReadStream('input/input_realistic.json'));

// Submit solve request
axios.post(
    'http://localhost:8080/solve?time_limit=30',
    form,
    { headers: form.getHeaders() }
)
.then(response => {
    const result = response.data;
    console.log(`Status: ${result.solverRun.status}`);
    console.log(`Score: ${result.score.total}`);
    console.log(`Assignments: ${result.assignments.length}`);
})
.catch(error => {
    console.error('Error:', error.response?.data || error.message);
});
```

---

## Error Handling

### Common Error Scenarios

**1. Missing Input**
```
Status: 400 Bad Request
Detail: "Provide either input_json in request body or upload a JSON file."
```

**2. Invalid JSON**
```
Status: 422 Unprocessable Entity
Detail: "Unable to parse uploaded file as JSON: Expecting value..."
```

**3. Strict Mode Violation**
```
Status: 400 Bad Request
Detail: "Provide either input_json or file, not both (strict mode enabled)."
```

**4. Server Error**
```
Status: 500 Internal Server Error
Detail: "Internal error: [error message]"
```

Response headers will include:
- `X-Request-ID`: UUID for tracing the error in server logs

---

## Performance Considerations

### Time Limits

- Minimum: 1 second
- Maximum: 120 seconds (2 minutes)
- Recommended: 15-30 seconds for typical problems

The solver will return the best solution found when time expires.

### Request Timeout

Set your HTTP client timeout higher than `time_limit`:
- If `time_limit=30`, set HTTP timeout to 45-60 seconds

### Concurrency

The API is designed to handle multiple concurrent requests. In production:
- Use `--workers 2+` for multi-process scaling
- Place behind a reverse proxy (nginx, Traefik) for load balancing
- Monitor memory usage (solver can require 500MB-1GB per complex problem)

---

## Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

Both provide interactive request/response testing.

---

## Logging and Debugging

### View Server Logs

```bash
# Development
python -m uvicorn src.api_server:app --reload --log-level debug

# Check for errors with request ID
grep "requestId=550e8400-e29b-41d4-a716-446655440000" <logfile>
```

### Request Tracing

All responses include a `requestId` header and field:
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

Use this ID to correlate API calls with server logs.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8080 | API server port |
| `CORS_ORIGINS` | localhost | Comma-separated CORS allowed origins |

**Example:**
```bash
export PORT=9000
export CORS_ORIGINS="http://localhost:3000,http://app.example.com"
python -m uvicorn src.api_server:app --port 9000
```

---

## Next Steps

1. **Start the server**: `./run_api_server.sh dev`
2. **Test with sample data**: `curl -F "file=@input/input_realistic.json" http://localhost:8080/solve`
3. **Check the Swagger UI**: http://localhost:8080/docs
4. **Integrate with your application**: Use the `/solve` endpoint

For more details on input format, see [../QUICKSTART.md](../QUICKSTART.md)
