# AWS App Runner API Testing Examples

**Project**: NGRS Solver v0.7  
**Date**: November 13, 2025  
**Purpose**: Test your deployed App Runner service  

---

## 🔗 Prerequisite

Replace `https://xxxxx.us-east-1.apprunner.amazonaws.com` with your actual App Runner URL:
- Found in AWS Console → App Runner → Services → ngrs-solver-api → Default domain

---

## ✅ Test 1: Health Check

### Using curl

```bash
curl -X GET https://xxxxx.us-east-1.apprunner.amazonaws.com/health \
  -H "Content-Type: application/json"
```

**Expected Response**:
```json
{
  "status": "ok"
}
```

**Status**: 200 OK ✅

---

## ✅ Test 2: Get Version Information

### Using curl

```bash
curl -X GET https://xxxxx.us-east-1.apprunner.amazonaws.com/version \
  -H "Content-Type: application/json"
```

**Expected Response**:
```json
{
  "apiVersion": "0.1.0",
  "solverVersion": "optfold-py-0.4.2",
  "schemaVersion": "0.43",
  "timestamp": "2025-11-13T12:00:00.123456"
}
```

**Status**: 200 OK ✅

---

## ✅ Test 3: Access API Documentation

### In Browser

```
https://xxxxx.us-east-1.apprunner.amazonaws.com/docs
```

You should see:
- Swagger UI interface
- All available endpoints listed
- Try it out functionality
- Request/response models

---

## ✅ Test 4: Solve a Problem (Simple Example)

### Create test input file: `test-input.json`

```json
{
  "horizon": {
    "startDate": "2025-11-01",
    "endDate": "2025-11-30"
  },
  "demandItems": [
    {
      "demandId": "D_TEST",
      "headcount": 2,
      "siteId": "SITE-A",
      "shifts": [
        {
          "shiftCode": "D",
          "startTime": "08:00",
          "endTime": "20:00",
          "skillRequirements": []
        }
      ]
    }
  ],
  "employees": [
    {
      "employeeId": "E_001",
      "firstName": "John",
      "lastName": "Doe",
      "status": "ACTIVE"
    },
    {
      "employeeId": "E_002",
      "firstName": "Jane",
      "lastName": "Smith",
      "status": "ACTIVE"
    }
  ]
}
```

### Using curl

```bash
curl -X POST https://xxxxx.us-east-1.apprunner.amazonaws.com/solve \
  -H "Content-Type: application/json" \
  -d @test-input.json
```

### Expected Response (simplified):

```json
{
  "solverRun": {
    "status": "OPTIMAL",
    "duration": 2.5
  },
  "score": {
    "hard": 0,
    "soft": -10
  },
  "assignments": [
    {
      "employeeId": "E_001",
      "demandId": "D_TEST",
      "date": "2025-11-01",
      "startDateTime": "2025-11-01T08:00:00",
      "endDateTime": "2025-11-01T20:00:00",
      "siteId": "SITE-A"
    }
  ]
}
```

---

## 🐍 Python Testing Script

### Test with Python

```python
#!/usr/bin/env python3
"""
Test NGRS Solver App Runner deployment
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "https://xxxxx.us-east-1.apprunner.amazonaws.com"
HEADERS = {"Content-Type": "application/json"}

class NGRSSolverTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def test_health(self) -> bool:
        """Test health endpoint"""
        print("\n🏥 Testing health endpoint...")
        try:
            resp = self.session.get(f"{self.base_url}/health", headers=HEADERS)
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {resp.json()}")
            return resp.status_code == 200
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def test_version(self) -> bool:
        """Test version endpoint"""
        print("\n📦 Testing version endpoint...")
        try:
            resp = self.session.get(f"{self.base_url}/version", headers=HEADERS)
            print(f"  Status: {resp.status_code}")
            data = resp.json()
            print(f"  API Version: {data.get('apiVersion')}")
            print(f"  Solver Version: {data.get('solverVersion')}")
            print(f"  Schema Version: {data.get('schemaVersion')}")
            return resp.status_code == 200
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def test_solve(self, input_data: Dict[str, Any]) -> bool:
        """Test solve endpoint"""
        print("\n🧮 Testing solve endpoint...")
        try:
            start_time = time.time()
            resp = self.session.post(
                f"{self.base_url}/solve",
                headers=HEADERS,
                json=input_data
            )
            duration = time.time() - start_time
            
            print(f"  Status: {resp.status_code}")
            print(f"  Duration: {duration:.2f}s")
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Solver Status: {data.get('solverRun', {}).get('status')}")
                print(f"  Hard Score: {data.get('score', {}).get('hard')}")
                print(f"  Soft Score: {data.get('score', {}).get('soft')}")
                print(f"  Assignments: {len(data.get('assignments', []))}")
                return True
            else:
                print(f"  Error: {resp.text}")
                return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def test_docs(self) -> bool:
        """Test API documentation endpoint"""
        print("\n📚 Testing documentation endpoint...")
        try:
            resp = self.session.get(f"{self.base_url}/docs", headers=HEADERS)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  Swagger UI available")
                return True
            return False
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    def run_all_tests(self, input_data: Dict[str, Any] = None) -> None:
        """Run all tests"""
        print("=" * 60)
        print("NGRS Solver App Runner Test Suite")
        print("=" * 60)
        
        results = {
            "Health": self.test_health(),
            "Version": self.test_version(),
            "Docs": self.test_docs(),
        }
        
        if input_data:
            results["Solve"] = self.test_solve(input_data)
        
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name:20} {status}")
        
        total = len(results)
        passed = sum(1 for v in results.values() if v)
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Service is running correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the output above.")

# ============================================================================
# EXAMPLE INPUT FOR TESTING
# ============================================================================

SIMPLE_TEST_INPUT = {
    "horizon": {
        "startDate": "2025-11-01",
        "endDate": "2025-11-30"
    },
    "demandItems": [
        {
            "demandId": "D_TEST",
            "headcount": 2,
            "siteId": "SITE-A",
            "shifts": [
                {
                    "shiftCode": "D",
                    "startTime": "08:00",
                    "endTime": "20:00",
                    "skillRequirements": []
                }
            ]
        }
    ],
    "employees": [
        {
            "employeeId": "E_001",
            "firstName": "John",
            "lastName": "Doe",
            "status": "ACTIVE"
        },
        {
            "employeeId": "E_002",
            "firstName": "Jane",
            "lastName": "Smith",
            "status": "ACTIVE"
        }
    ]
}

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Replace with your actual App Runner URL
    app_runner_url = "https://xxxxx.us-east-1.apprunner.amazonaws.com"
    
    # Create tester
    tester = NGRSSolverTester(app_runner_url)
    
    # Run tests
    tester.run_all_tests(SIMPLE_TEST_INPUT)
```

### Run the test script

```bash
# Install requests if needed
pip install requests

# Run tests
python test_apprunner.py
```

---

## 📤 Test 5: Upload File to S3 and Solve

### Using Python

```python
import boto3
import json

# Initialize S3 client
s3_client = boto3.client('s3', region_name='us-east-1')

# Upload input file
input_file = 'input.json'
bucket = 'ngrs-solver-files'

with open(input_file, 'r') as f:
    input_data = json.load(f)

# Upload to S3
s3_client.put_object(
    Bucket=bucket,
    Key=f'input/{input_file}',
    Body=json.dumps(input_data),
    ContentType='application/json'
)

print(f"✅ Uploaded to s3://{bucket}/input/{input_file}")

# Now call the API
import requests

resp = requests.post(
    "https://xxxxx.us-east-1.apprunner.amazonaws.com/solve",
    headers={"Content-Type": "application/json"},
    json=input_data
)

# Download output
output_data = resp.json()
output_file = f"output_{int(time.time())}.json"

s3_client.put_object(
    Bucket=bucket,
    Key=f'output/{output_file}',
    Body=json.dumps(output_data),
    ContentType='application/json'
)

print(f"✅ Uploaded output to s3://{bucket}/output/{output_file}")
```

---

## 🔍 Test 6: Monitor Performance

### Check Response Times

```bash
# Test response time with time command
time curl -X POST https://xxxxx.us-east-1.apprunner.amazonaws.com/solve \
  -H "Content-Type: application/json" \
  -d @input.json
```

Expected: 2-30 seconds depending on problem complexity

### Check Concurrent Requests

```bash
# Use Apache Bench (ab) if installed
ab -n 100 -c 10 https://xxxxx.us-east-1.apprunner.amazonaws.com/health

# Or use wrk if installed
wrk -t 4 -c 100 -d 30s https://xxxxx.us-east-1.apprunner.amazonaws.com/health
```

---

## 📊 Test 7: View CloudWatch Logs

### Using AWS CLI

```bash
# Get recent logs
aws logs tail /aws/apprunner/ngrs-solver --follow --region us-east-1
```

### Using AWS Console

1. Go to **CloudWatch** → **Log Groups**
2. Find `/aws/apprunner/ngrs-solver`
3. Click to view logs in real-time

---

## 🐛 Debugging Failed Tests

### If Health Check Fails

```bash
# Check if service is running
curl -v https://xxxxx.us-east-1.apprunner.amazonaws.com/health

# Check AWS Console for service status
# AWS Console → App Runner → Services → ngrs-solver-api
# Look for "Status" field (should be "Running")
```

### If Solve Returns 500 Error

```bash
# Check application logs
aws logs tail /aws/apprunner/ngrs-solver --follow

# Common issues:
# - Missing environment variables
# - S3 bucket not accessible
# - Input validation failed
```

### If Service is Slow

```bash
# Check metrics in AWS Console
# AWS Console → CloudWatch → Metrics → AppRunner
# Look for:
# - High CPU utilization (scale up vCPU)
# - High memory utilization (scale up memory)
# - Many instances scaling up (increase SOLVER_TIME_LIMIT)
```

---

## 📋 Testing Checklist

After deployment, run through this checklist:

- [ ] Health check returns 200 OK
- [ ] Version endpoint shows correct versions
- [ ] API docs page loads (Swagger UI)
- [ ] Can submit a simple solve request
- [ ] Solve request returns valid JSON
- [ ] Solver status is not ERROR
- [ ] Response time is < 60 seconds
- [ ] CloudWatch logs show no ERROR level messages
- [ ] Can upload files to S3
- [ ] Can download output files from S3
- [ ] Service handles multiple concurrent requests
- [ ] Service auto-scales when load increases

---

## 🚀 Next Steps

Once all tests pass:

1. **Load testing**: Use wrk or Apache Bench to test capacity
2. **Custom domain**: Configure Route 53 DNS
3. **API authentication**: Add API Gateway in front
4. **Monitoring**: Set up CloudWatch alarms
5. **Usage tracking**: Enable metrics export
6. **User documentation**: Create client library examples

---

**All tests passing? Your App Runner deployment is ready for production! 🎉**
