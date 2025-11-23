# AWS App Runner Deployment Guide - AWS Console Instructions

**Date**: November 13, 2025  
**Project**: NGRS Solver v0.7  
**Region**: us-east-1 (configurable)  

---

## 🎯 Overview

This guide provides step-by-step instructions to deploy NGRS Solver on AWS App Runner using the AWS Console (no CLI needed).

**Estimated Time**: 20-30 minutes  
**Estimated Cost**: ~$175/month (production config)

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] AWS Account with admin access
- [ ] GitHub account with access to ngrssolver repo
- [ ] Preferred AWS region (default: us-east-1)
- [ ] S3 bucket name: `ngrs-solver-files` (or custom)
- [ ] CORS origins configured (frontend URLs)

---

## 🚀 Step 1: Create S3 Bucket for File Storage

### 1.1 Open S3 Console

1. Go to **AWS Console** → Search for **S3**
2. Click **S3** service
3. Click **Create bucket** button

### 1.2 Configure Bucket

| Field | Value |
|-------|-------|
| **Bucket name** | `ngrs-solver-files` |
| **Region** | `us-east-1` (or your preferred) |
| **Object Ownership** | BucketOwnerEnforced |
| **Block Public Access** | ✅ Keep all blocked |
| **Versioning** | Enable |
| **Encryption** | Default (AES-256) |

### 1.3 Click Create Bucket

✅ S3 bucket created!

### 1.4 Create Folders (Optional)

In the bucket, create folders:
- `input/` - for input JSON files
- `output/` - for solver output files
- `logs/` - for application logs

---

## 🔐 Step 2: Create IAM Role for App Runner

### 2.1 Open IAM Console

1. Go to **AWS Console** → Search for **IAM**
2. Click **IAM** service
3. Click **Roles** in left menu
4. Click **Create role**

### 2.2 Select Role Type

1. Under "Trusted entity type", select **AWS service**
2. Under "Use case", select **App Runner**
3. Click **Next**

### 2.3 Add Permissions

1. Click **Create policy** (new tab will open)
2. In the new tab, select **JSON** tab
3. Copy-paste the content from `aws-iam-policy.json` (see file below)
4. Click **Next**
5. Name: `ngrs-solver-apprunner-policy`
6. Click **Create policy**

### 2.4 Attach Policy to Role

1. Back in the first tab, refresh the policies
2. Search for `ngrs-solver-apprunner-policy`
3. Check the box next to it
4. Click **Next**

### 2.5 Name and Create Role

1. **Role name**: `ngrs-solver-app-runner-role`
2. **Description**: "Role for NGRS Solver App Runner service"
3. Click **Create role**

✅ IAM role created!

---

## 🔑 Step 3: Create GitHub Connection

### 3.1 Open App Runner Console

1. Go to **AWS Console** → Search for **App Runner**
2. Click **App Runner** service
3. Click **Connections** in left menu
4. Click **Create connection**

### 3.2 Configure Connection

1. Under "Source type", select **GitHub**
2. Click **Connect**
3. You'll be redirected to GitHub OAuth page
4. Click **Authorize aws-apprunner** button
5. You'll return to AWS with connection created

### 3.3 Copy Connection ARN

1. Your connection will be listed
2. Click on it to view details
3. Copy the **Connection ARN** (format: `arn:aws:apprunner:region:account:connection/name`)
4. **Save this ARN** - you'll need it in Step 4

✅ GitHub connection created!

---

## 📦 Step 4: Create App Runner Service

### 4.1 Open App Runner Services

1. Go to **AWS Console** → **App Runner**
2. Click **Services** in left menu (if not already there)
3. Click **Create service**

### 4.2 Configure Repository

**Source section:**

| Field | Value |
|-------|-------|
| **Repository type** | GitHub |
| **Connection** | Select the connection you just created |
| **Repository** | `gloridas75/ngrssolver` |
| **Branch** | `dev` |
| **Deployment trigger** | Automatic (or manual) |

✅ Click **Next**

### 4.3 Configure Build

**Build settings:**

| Field | Value |
|-------|-------|
| **Build command** | `pip install --upgrade pip setuptools wheel && pip install -e . && pip install fastapi uvicorn starlette python-multipart orjson aiofiles boto3` |
| **Start command** | `python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8080 --workers 2` |

**Runtime:**

| Field | Value |
|-------|-------|
| **Runtime** | Python 3.11 |
| **Base image** | (Leave empty) |

✅ Click **Next**

### 4.4 Configure Service

**Basic configuration:**

| Field | Value |
|-------|-------|
| **Service name** | `ngrs-solver-api` |
| **Port** | `8080` |

**Environment variables:**

Add these environment variables:

```
PYTHONUNBUFFERED=1
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
```

**Add each variable:**

1. Click **Add variable**
2. Enter variable name and value
3. Repeat for each variable

✅ Click **Next**

### 4.5 Configure Instances & Auto-Scaling

**Instance configuration:**

| Field | Value |
|-------|-------|
| **vCPU** | `1` |
| **Memory** | `2 GB` |

**Auto-scaling:**

| Field | Value |
|-------|-------|
| **Min instances** | `1` |
| **Max instances** | `4` |
| **Max concurrency** | `100` |
| **CPU utilization target** | `70%` |
| **Memory utilization target** | `80%` |

✅ Click **Next**

### 4.6 Configure Monitoring

**Logging:**

| Setting | Value |
|---------|-------|
| **CloudWatch logs** | Enable |

**Observability:**

| Setting | Value |
|---------|-------|
| **Container metrics** | Enable |

✅ Click **Next**

### 4.7 Review and Create

1. Review all settings
2. Click **Create & deploy**

⏳ **App Runner will now build and deploy your service**

Expected time: **5-10 minutes for first build**

---

## ✅ Step 5: Verify Deployment

### 5.1 Check Service Status

1. Go to **App Runner** → **Services**
2. Click **ngrs-solver-api**
3. Wait for status to become **Running** (green)

### 5.2 Get Service URL

1. Under **Service details**, find **Default domain**
2. Format: `https://xxxxx.us-east-1.apprunner.amazonaws.com`
3. **Copy this URL** - this is your API endpoint

### 5.3 Test API Health

1. Open browser or Postman
2. Go to: `https://xxxxx.us-east-1.apprunner.amazonaws.com/health`
3. Should return: `{"status": "ok"}`

✅ API is running!

### 5.4 Access API Documentation

1. Go to: `https://xxxxx.us-east-1.apprunner.amazonaws.com/docs`
2. Should see Swagger UI with all endpoints

✅ Documentation is accessible!

---

## 🧪 Step 6: Test the API

### 6.1 Get Version Info

**Endpoint**: `GET /version`

```bash
curl https://xxxxx.us-east-1.apprunner.amazonaws.com/version
```

**Response**:
```json
{
  "apiVersion": "0.1.0",
  "solverVersion": "optfold-py-0.4.2",
  "schemaVersion": "0.43",
  "timestamp": "2025-11-13T12:00:00"
}
```

### 6.2 Solve a Problem

**Endpoint**: `POST /solve`

You can use the interactive API docs at `/docs` or curl:

```bash
curl -X POST https://xxxxx.us-east-1.apprunner.amazonaws.com/solve \
  -H "Content-Type: application/json" \
  -d @input.json
```

✅ API is working!

---

## 📊 Step 7: Set Up Monitoring

### 7.1 View Logs

1. Go to **App Runner** → **Services** → **ngrs-solver-api**
2. Click **Logs** tab
3. Select **Application logs**
4. Logs appear in real-time

### 7.2 View Metrics

1. Go to **Metrics** tab
2. View:
   - **CPU utilization**
   - **Memory utilization**
   - **Active instances**
   - **Request count**

### 7.3 Create CloudWatch Alarms

1. Go to **AWS Console** → **CloudWatch**
2. Click **Alarms** → **Create alarm**
3. Select metric: **App Runner CPU utilization**
4. Threshold: > 85%
5. Action: Send SNS notification
6. Click **Create alarm**

**Repeat for**:
- Memory utilization > 90%
- Service unhealthy

---

## 🌐 Step 8: Configure Custom Domain (Optional)

### 8.1 If You Have a Domain

1. Go to **Route 53** in AWS Console
2. Find your hosted zone
3. Click **Create record**
4. **Name**: `solver.yourdomain.com` (or whatever)
5. **Type**: CNAME
6. **Value**: Your App Runner default domain
7. Click **Create records**

### 8.2 SSL Certificate

App Runner automatically provides:
- ✅ Free SSL/TLS certificate
- ✅ Auto-renewal
- ✅ HTTPS on all domains

---

## 💾 Step 9: Upload Test Files to S3

### 9.1 Go to S3 Bucket

1. Go to **AWS Console** → **S3**
2. Click **ngrs-solver-files**

### 9.2 Upload Input Files

1. Click **input/** folder
2. Click **Upload**
3. Select your `input.json` files
4. Click **Upload**

### 9.3 View Output Files

After running the solver:

1. Click **output/** folder
2. Download any `output_*.json` file
3. Results are automatically stored here

---

## 🔄 Step 10: Auto-Deployment from GitHub

### 10.1 How It Works

Every time you push to the `dev` branch:

1. GitHub sends webhook to App Runner
2. App Runner automatically builds
3. New version deployed without downtime
4. Old version removed after health check passes

### 10.2 Manual Redeploy

1. Go to **App Runner** → **ngrs-solver-api**
2. Click **Deploy** button
3. Select source → Click **Deploy**
4. Service redeploys with latest code

---

## 📈 Performance Tips

### Auto-Scaling in Action

Your config automatically scales based on demand:

| Load | Expected Result |
|------|-----------------|
| Low (1-10 req/min) | 1 instance, ~$0.05/day |
| Medium (10-50 req/min) | 1-2 instances, ~$0.10/day |
| High (50+ req/min) | 3-4 instances, ~$0.20/day |

### Estimated Costs

| Scenario | Monthly Cost |
|----------|--------------|
| Dev (1000 req/day) | ~$26 |
| Production (10k req/day) | ~$200 |
| High (50k req/day) | ~$900 |

---

## 🐛 Troubleshooting

### Issue: Service Won't Deploy

**Check logs**:
1. Go to **Logs** tab
2. Look for error messages
3. Common issues:
   - Import errors (missing dependencies in build command)
   - GitHub connection expired
   - Insufficient IAM permissions

**Solution**:
1. Check `build command` has all dependencies
2. Reconnect GitHub connection
3. Verify IAM role has S3 permissions

### Issue: API Returns 5XX Errors

**Check**:
1. **Application logs** for Python exceptions
2. **CloudWatch logs** at `/aws/apprunner/ngrs-solver`
3. **Container metrics** for memory issues

**Common causes**:
- Out of memory (increase to 3GB)
- S3 bucket not accessible (check IAM)
- Missing environment variables

### Issue: Slow Response Times

**Check**:
1. CPU utilization in metrics
2. Memory utilization
3. Number of instances

**Solution**:
- Increase CPU to 2 vCPU
- Increase memory to 3 or 4 GB
- Reduce `time_limit` if solver takes too long

---

## 🔐 Security Best Practices

### ✅ Already Configured

- Non-root user in Dockerfile
- IAM role with least-privilege
- S3 bucket blocks public access
- HTTPS by default
- Secrets Manager support

### 🔒 Additional Steps

1. **API Keys**: Add API Gateway in front of App Runner
2. **VPC**: Use VPC connector for private API
3. **Monitoring**: Enable X-Ray tracing
4. **Backup**: Enable S3 versioning (already done)

---

## 📞 Next Steps

### After Deployment

1. ✅ Test all endpoints
2. ✅ Set up monitoring alarms
3. ✅ Configure custom domain (if needed)
4. ✅ Share API URL with users
5. ✅ Monitor costs in AWS Cost Explorer

### For Production

1. Set up CI/CD pipeline (GitHub Actions)
2. Add authentication to API
3. Set up usage analytics
4. Create runbooks for common issues
5. Plan for disaster recovery

---

## 📚 Related Files

- `apprunner.yaml` - Full configuration reference
- `Dockerfile.apprunner` - Optimized Docker image
- `aws-iam-policy.json` - IAM permissions needed
- `API_DOCUMENTATION.md` - API endpoint details
- `FASTAPI_INTEGRATION.md` - API architecture

---

## ✨ Success Indicators

Your deployment is successful when:

- ✅ Service status is **Running** (green)
- ✅ Health check endpoint returns `200 OK`
- ✅ API docs page loads at `/docs`
- ✅ `/solve` endpoint accepts requests
- ✅ CloudWatch logs show no errors
- ✅ Metrics dashboard shows traffic

---

**Deployment complete! Your NGRS Solver is now running on AWS App Runner.** 🎉
