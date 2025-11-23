# AWS App Runner Deployment - Quick Reference Card

**Project**: NGRS Solver v0.7  
**Date**: November 13, 2025  
**Prepared for**: AWS Console Deployment  

---

## 📋 Files You'll Need

| File | Purpose | Location |
|------|---------|----------|
| `apprunner.yaml` | Complete configuration reference | Root directory |
| `Dockerfile.apprunner` | Optimized Docker image | Root directory |
| `aws-iam-policy.json` | IAM permissions needed | Root directory |
| `app-runner-env-template.txt` | Environment variables | Root directory |
| `AWS_APPRUNNER_CONSOLE_GUIDE.md` | Step-by-step console instructions | implementation_docs/ |
| `cloudformation-template.yaml` | Infrastructure as code option | Root directory |

---

## 🚀 Quick Start (30 minutes)

### 1️⃣ **Create S3 Bucket** (2 min)
```
AWS Console → S3 → Create bucket
Name: ngrs-solver-files
Region: us-east-1
Block public access: YES
Versioning: ENABLE
```

### 2️⃣ **Create IAM Role** (5 min)
```
AWS Console → IAM → Roles → Create role
Service: App Runner
Policy: Copy from aws-iam-policy.json
Name: ngrs-solver-app-runner-role
```

### 3️⃣ **Create GitHub Connection** (3 min)
```
AWS Console → App Runner → Connections
Type: GitHub
Authorize and copy the Connection ARN
```

### 4️⃣ **Create App Runner Service** (20 min)
```
AWS Console → App Runner → Create service

Repository: gloridas75/ngrssolver
Branch: dev
Connection: Your GitHub connection

Build Command:
  pip install --upgrade pip setuptools wheel
  pip install -e .
  pip install fastapi uvicorn starlette python-multipart orjson aiofiles boto3

Start Command:
  python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8080 --workers 2

Service Name: ngrs-solver-api
Port: 8080
vCPU: 1
Memory: 2048 MB
Min instances: 1
Max instances: 4
```

### 5️⃣ **Configure Environment Variables** (5 min)
```
PYTHONUNBUFFERED=1
PORT=8080
USE_S3_STORAGE=true
S3_BUCKET_NAME=ngrs-solver-files
S3_REGION=us-east-1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
SOLVER_TIME_LIMIT=15
ENVIRONMENT=production
```

### 6️⃣ **Deploy and Test** (5 min)
```
Wait for deployment to complete (5-10 min)
Test: https://xxxxx.us-east-1.apprunner.amazonaws.com/health
Docs: https://xxxxx.us-east-1.apprunner.amazonaws.com/docs
```

✅ **Done!**

---

## 🔑 Essential Configuration Values

### Build & Runtime
```
Runtime: PYTHON_3_11
Build time: ~2-3 minutes
Deployment time: 5-10 minutes (first), 2-3 min (subsequent)
```

### Instance Sizing (Recommended)
```
CPU: 1 vCPU
Memory: 2 GB (2048 MB)
Cost: ~$25/month + request charges
```

### Auto-Scaling
```
Min instances: 1
Max instances: 4
CPU threshold: 70%
Memory threshold: 80%
Max concurrency: 100 req/instance
```

### Health Check
```
Path: /health
Interval: 30s
Timeout: 10s
Healthy threshold: 1
Unhealthy threshold: 5
```

---

## 📊 Environment Variables (Copy & Paste)

```
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
PORT=8080
USE_S3_STORAGE=true
S3_BUCKET_NAME=ngrs-solver-files
S3_REGION=us-east-1
S3_INPUT_PREFIX=input/
S3_OUTPUT_PREFIX=output/
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173
SOLVER_TIME_LIMIT=15
LOG_LEVEL=INFO
ENVIRONMENT=production
ENABLE_SCHEMA_VALIDATION=false
ENABLE_METRICS=true
```

---

## 🔐 IAM Policy (Essential Permissions)

```json
S3 Access:
  - s3:ListBucket
  - s3:GetObject
  - s3:PutObject
  - s3:DeleteObject
  Resource: arn:aws:s3:::ngrs-solver-files/*

CloudWatch Logs:
  - logs:CreateLogGroup
  - logs:CreateLogStream
  - logs:PutLogEvents
  Resource: arn:aws:logs:*:*:/aws/apprunner/*

Secrets Manager (optional):
  - secretsmanager:GetSecretValue
  Resource: arn:aws:secretsmanager:*:*:secret:ngrs-solver/*
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Service status is **Running** (green)
- [ ] `/health` returns `{"status": "ok"}` (status 200)
- [ ] `/docs` shows Swagger UI
- [ ] `/version` returns version info
- [ ] `/solve` accepts POST requests
- [ ] S3 bucket created and accessible
- [ ] CloudWatch logs show no errors
- [ ] Metrics dashboard shows traffic

---

## 🌐 API Endpoints

Once deployed, access:

| Endpoint | URL | Purpose |
|----------|-----|---------|
| Health Check | `/health` | Verify service is running |
| Documentation | `/docs` | Interactive API docs (Swagger) |
| ReDoc | `/redoc` | Alternative documentation |
| OpenAPI Schema | `/openapi.json` | Machine-readable schema |
| Version Info | `/version` | API and solver versions |
| Solve | `/solve` (POST) | Main solving endpoint |

**Base URL**: `https://xxxxx.us-east-1.apprunner.amazonaws.com`

---

## 📈 Cost Estimation

### Monthly Costs (Baseline)

| Component | Cost |
|-----------|------|
| vCPU-hour | $0.026 × 720 hrs = $18.72 |
| GB-hour (2GB) | $0.0029 × 1440 hrs = $4.18 |
| Per request | $0.005 × 30k req = $150 |
| **Total** | ~**$173/month** |

*Note: Costs scale with usage. Idle service = minimal cost.*

### Scaling Scenarios

```
Light:   1000 req/day  → ~$26/month
Standard: 10k req/day  → ~$200/month  ← Recommended
Heavy:    50k req/day  → ~$900/month
```

---

## 🐛 Troubleshooting Quick Guide

| Issue | Cause | Solution |
|-------|-------|----------|
| Won't deploy | Build error | Check build command has all dependencies |
| Service unavailable | Health check failed | Check /health endpoint, review logs |
| 500 errors | App crashed | Check application logs, increase memory |
| Slow responses | High CPU/memory | Increase vCPU/memory or reduce time_limit |
| S3 access denied | IAM permissions | Verify S3 policy attached to role |
| GitHub connection expired | OAuth token | Reconnect GitHub in App Runner connections |

---

## 🔗 Important URLs

After deployment, bookmark:

```
Health Check:
https://xxxxx.us-east-1.apprunner.amazonaws.com/health

API Documentation:
https://xxxxx.us-east-1.apprunner.amazonaws.com/docs

AWS Console - Service:
https://console.aws.amazon.com/apprunner/home?region=us-east-1

AWS Console - Logs:
https://console.aws.amazon.com/logs/home?region=us-east-1#logStream:logGroupName=/aws/apprunner/ngrs-solver

S3 Bucket:
https://console.aws.amazon.com/s3/buckets/ngrs-solver-files
```

---

## 📞 Support Resources

- Full console guide: `AWS_APPRUNNER_CONSOLE_GUIDE.md`
- API documentation: `API_DOCUMENTATION.md`
- FastAPI integration: `FASTAPI_INTEGRATION.md`
- Configuration reference: `apprunner.yaml`
- CloudFormation alternative: `cloudformation-template.yaml`

---

## 💾 Next Steps After Deployment

1. **Test the API** using the `/docs` endpoint
2. **Upload test files** to S3 (input/ folder)
3. **Monitor CloudWatch logs** for any issues
4. **Set up custom domain** (Route 53)
5. **Create CloudWatch alarms** for production
6. **Share API URL** with users
7. **Enable API authentication** (API Gateway)

---

**Ready to deploy? Follow the step-by-step console guide in `AWS_APPRUNNER_CONSOLE_GUIDE.md`** ✨
