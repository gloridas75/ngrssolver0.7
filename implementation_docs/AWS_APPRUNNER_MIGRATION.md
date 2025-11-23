# AWS App Runner Migration Guide for NGRS Solver

**Date**: November 13, 2025  
**Status**: Pre-Migration Planning  
**Version**: 1.0  

---

## 📋 Executive Summary

This guide provides a comprehensive approach to migrating the NGRS Solver from local Docker to **AWS App Runner**. App Runner is ideal for your use case because it:

- ✅ Automatically builds Docker images from your GitHub repo
- ✅ Manages auto-scaling without infrastructure overhead
- ✅ Provides built-in monitoring and logging
- ✅ No need to manage EC2 instances or container orchestration
- ✅ Cost-effective pay-per-use model
- ✅ Automatic SSL/TLS certificates
- ✅ Easy environment management

---

## 🔍 Current Application Analysis

### Application Profile

| Component | Current State | App Runner Compatible |
|-----------|--------------|----------------------|
| **Framework** | FastAPI + Uvicorn | ✅ Yes |
| **Python Version** | 3.11-slim | ✅ Yes |
| **Port** | 8080 (HTTP) | ✅ Yes |
| **Memory Needs** | 1GB min, 2GB recommended | ✅ Yes (1-4GB options) |
| **CPU Needs** | 1-2 vCPU | ✅ Yes (1-4 vCPU options) |
| **Build Time** | ~2-3 minutes | ✅ Acceptable |
| **Dependencies** | ortools, pydantic, fastapi, uvicorn | ✅ All available |
| **Data Storage** | Needs persistent storage | ⚠️ See solutions below |

### Key Considerations

**Stateless Design**: ✅ Your API is stateless
- Each `/solve` request is independent
- No session state stored on server
- No need for shared memory cache

**Data Handling**: ⚠️ Input/output files
- Current: Docker volumes (./input, ./output)
- AWS App Runner: Ephemeral storage (lost on deployment)
- Solution: Use S3 for persistent storage

**Scale Profile**: Solve time ~15-30 seconds per request
- Memory: 2GB recommended (ortools needs it)
- CPU: 2 vCPU recommended
- Concurrency: 5-10 concurrent requests typical

---

## 🏗️ Architecture Options

### Option 1: **Recommended - App Runner + S3 + API Gateway** (Most Common)

```
User/Client
    ↓
API Gateway (Optional: rate limiting, API keys)
    ↓
App Runner (Stateless API)
    ↓
┌─────────┴─────────┐
│                   │
S3 Bucket        CloudWatch
(Input/Output)   (Logging)
```

**Pros**:
- Simple and clean architecture
- Auto-scaling built-in
- S3 for persistent file storage
- Cost: ~$0.05/request + $0.04 per GB memory-hour

**Cons**:
- Need to refactor file I/O for S3
- S3 costs (~$0.023 per GB stored)

**Best for**: Production deployments, public APIs, professional users

---

### Option 2: App Runner + EFS (If you need file storage)

```
App Runner → EFS (Elastic File System)
```

**Pros**:
- Files persist across deployments
- No need to refactor code
- Easy to use (mount like local filesystem)

**Cons**:
- More expensive (~$0.30/GB-month)
- Requires VPC setup
- Slightly more complex

**Best for**: If you need quick deployment without code changes

---

### Option 3: App Runner + RDS (If future database integration)

For future phases when you might need:
- User accounts
- Request history
- Audit logging

```
App Runner → RDS (PostgreSQL)
          ↓
        S3 (files)
          ↓
    CloudWatch (logs)
```

---

## 📊 Cost Comparison (Monthly Estimate)

### Scenario: 1000 requests/day, 30 seconds avg solve time

| Component | Option 1 (S3) | Option 2 (EFS) | Notes |
|-----------|---------------|----------------|-------|
| **App Runner** | $25/month | $25/month | 1 vCPU, 2GB memory |
| **Storage** | $1/month | $10/month | 1000 requests × 5MB = 5GB |
| **Data Transfer** | $0.50/month | $0.50/month | Minimal |
| **Monitoring** | Free | Free | CloudWatch included |
| **TOTAL** | ~$26.50 | ~$35.50 | **Option 1 is cheaper** |

---

## ⚠️ Information I Need From You

Before I create the migration plan, please provide:

### 1. **AWS Account & Permissions**
- [ ] Do you have an AWS account already?
- [ ] Do you have IAM permissions to create App Runner services, S3 buckets, and policies?
- [ ] Preferred AWS region (us-east-1, us-west-2, eu-west-1, etc.)?

### 2. **GitHub Repository**
- [ ] Is your code in a GitHub repository?
- [ ] What's the repository URL?
- [ ] Which branch should App Runner deploy from (main, develop)?
- [ ] Do you need a specific secret for GitHub connection (or should I use OIDC)?

### 3. **Storage & Data**
- [ ] **Critical**: Do you need input/output files to persist between API calls?
  - Yes → Use S3 or EFS
  - No → Use ephemeral storage (current Dockerfile works as-is)
- [ ] How long should files be retained? (24 hours, 30 days, indefinite?)
- [ ] Do you need to access files after deployment? (e.g., download output JSON)

### 4. **API & Access**
- [ ] Should the API be **public** (anyone can call) or **private** (API key protected)?
- [ ] Do you need API Gateway for rate limiting / API management?
- [ ] What are the expected concurrent requests? (estimate)
- [ ] Expected peak requests per day?

### 5. **Monitoring & Logging**
- [ ] Do you want CloudWatch logs? (default: yes)
- [ ] Do you need custom metrics?
- [ ] Alert notifications (SNS email when service is down)?

### 6. **Domain & SSL**
- [ ] Do you want a custom domain? (e.g., solver.mycompany.com)
- [ ] Should it use HTTPS? (default: yes, auto-managed)

### 7. **Performance Requirements**
- [ ] Memory requirement: 1GB, 2GB, 3GB, or 4GB?
- [ ] CPU requirement: 0.25 vCPU, 0.5 vCPU, 1 vCPU, 2 vCPU, or 4 vCPU?
- [ ] Concurrent request capacity needed?
- [ ] Timeout acceptable? (Default 60s, max 3600s)

### 8. **Environment Configuration**
- [ ] CORS origins needed? (currently localhost)
- [ ] Any API keys or secrets to configure?
- [ ] Database connection strings?
- [ ] Custom environment variables?

### 9. **Deployment Strategy**
- [ ] Immediate deployment vs. staged rollout?
- [ ] Keep local Docker setup or fully migrate?
- [ ] Blue-green deployment needed?

### 10. **Budget Constraint**
- [ ] What's your acceptable monthly cost?
- [ ] Any budget constraints I should know about?

---

## 🎯 What I'll Create Based on Your Answers

Once you provide the information above, I'll create:

### Phase 1: Preparation
- [ ] **app-runner-config.yaml** - App Runner configuration
- [ ] **S3-setup.sh** - Script to create S3 bucket with proper permissions
- [ ] **refactored-api-server.py** - Updated code for S3 support (if needed)
- [ ] **aws-environment-vars.json** - Environment configuration
- [ ] **IAM-policy.json** - Security policy for App Runner

### Phase 2: Infrastructure
- [ ] **infrastructure-as-code.tf** (optional Terraform) or CloudFormation template
- [ ] **Dockerfile.apprunner** - Optimized Dockerfile for App Runner
- [ ] **deployment-checklist.md** - Step-by-step deployment guide

### Phase 3: Integration
- [ ] **app-runner-setup.md** - Complete AWS setup guide
- [ ] **api-client-examples.py** - Python examples for calling from App Runner
- [ ] **monitoring-dashboard.md** - CloudWatch dashboard setup

### Phase 4: Optimization
- [ ] **cost-optimization.md** - Tips for reducing monthly costs
- [ ] **auto-scaling-config.md** - Optimal scaling parameters
- [ ] **troubleshooting-guide.md** - Common issues and solutions

---

## 🚀 Quick Start (Without Answers)

If you want to get started immediately with defaults:

### Default Assumptions:
```yaml
Region: us-east-1
Memory: 2GB
CPU: 1 vCPU
Storage: S3 (auto-setup)
API: Public with basic logging
Domain: App Runner auto-generated URL
Environment: Production-ready
```

**To proceed with defaults**, just confirm and I'll:
1. ✅ Create all configuration files
2. ✅ Refactor code for S3 storage
3. ✅ Generate deployment scripts
4. ✅ Provide step-by-step AWS console instructions

---

## 📈 Migration Timeline

### Typical Project Timeline

| Phase | Timeline | Effort |
|-------|----------|--------|
| **Preparation** | 1-2 hours | Planning + config files |
| **Infrastructure** | 2-3 hours | S3 setup + App Runner config |
| **Deployment** | 30-60 min | Follow checklist |
| **Testing** | 1-2 hours | Validate endpoints |
| **Optimization** | 1-2 hours | Scaling tuning |
| **TOTAL** | 6-10 hours | Mostly automated |

---

## ✅ Pre-Migration Checklist

Before we start, ensure you have:

- [ ] AWS account with appropriate permissions
- [ ] GitHub account (if not using GitHub connection)
- [ ] Local development environment (for testing)
- [ ] Docker installed locally (for testing builds)
- [ ] AWS CLI installed locally (optional but helpful)
- [ ] Understanding of your API usage patterns
- [ ] Decision on public vs. private API

---

## 🔗 Related Documentation

- `FASTAPI_INTEGRATION.md` - Current API structure
- `DOCKER_DEPLOYMENT.md` - Current Docker setup
- `API_DOCUMENTATION.md` - Endpoint specifications
- `CONSTRAINTS_COMPLETE.txt` - Solver details

---

## 💬 Next Steps

**Please provide answers to the 10 questions above**, and I'll immediately:

1. Create an optimized deployment package
2. Generate AWS setup scripts
3. Provide step-by-step console instructions
4. Create monitoring dashboards
5. Set up auto-scaling policies

**Or** confirm "use defaults" and I'll proceed with standard production configuration.

---

**Questions?** Check the FAQ below:

### FAQ

**Q: Will my current Dockerfile work with App Runner?**
A: Yes! App Runner can use Dockerfiles directly. We'll optimize it for faster builds.

**Q: What happens to my data between deployments?**
A: Depends on your choice. S3 persists forever; EFS persists across deployments; App Runner ephemeral storage is lost.

**Q: How do I handle file uploads/downloads?**
A: Through S3 bucket or EFS. Your API reads from and writes to cloud storage instead of local disk.

**Q: Can I scale based on request volume?**
A: Yes! App Runner auto-scales instances. We'll configure min/max concurrency.

**Q: How do I monitor performance?**
A: CloudWatch provides built-in metrics. We'll create a dashboard for visibility.

**Q: What about cost overruns?**
A: App Runner pricing is predictable. We'll set up alarms to alert you if costs spike.

**Q: Can I rollback deployments?**
A: Yes! App Runner keeps deployment history. Easy rollback if needed.

**Q: How long until it's live?**
A: From "yes go ahead" to production is typically 2-3 hours of actual work.
