# CloudWatch Setup Guide

This guide explains how to set up and use CloudWatch logging and metrics for the Latency Orchestrator project.

## Overview

CloudWatch integration provides:
- **Logs**: Centralized logging of training runs, errors, and execution flow
- **Metrics**: Custom metrics for latency, training progress, and S3 uploads
- **Monitoring**: Real-time visibility into system performance

## Automatic Setup (via Terraform)

If you're using Terraform to deploy, CloudWatch is automatically configured:

1. **Log Group**: Created at `/aws/latency-orchestrator/logs`
2. **IAM Permissions**: EC2 instance gets CloudWatch Logs and Metrics permissions
3. **Retention**: Logs are retained for 7 days

### Terraform Commands

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

After applying, check the outputs:
```bash
terraform output cloudwatch_log_group
# Output: /aws/latency-orchestrator/logs
```

## 🔧 Manual Setup (if not using Terraform)

### Step 1: Create CloudWatch Log Group

Via AWS Console:
1. Go to **CloudWatch** → **Logs** → **Log groups**
2. Click **Create log group**
3. Name: `/aws/latency-orchestrator/logs`
4. Set retention to **7 days** (optional but recommended)

Via AWS CLI:
```bash
aws logs create-log-group \
  --log-group-name /aws/latency-orchestrator/logs \
  --region us-east-1

# Set retention (optional)
aws logs put-retention-policy \
  --log-group-name /aws/latency-orchestrator/logs \
  --retention-in-days 7 \
  --region us-east-1
```

### Step 2: Configure IAM Permissions

The EC2 instance needs permissions to write logs and publish metrics.

#### Option A: Using IAM Role (Recommended)

1. Go to **IAM** → **Roles**
2. Select your EC2 instance role (e.g., `rl-orchestrator-role`)
3. Click **Add permissions** → **Attach policies**
4. Attach these policies:
   - `CloudWatchLogsFullAccess` (for logging)
   - Create a custom policy for metrics (see below)

#### Option B: Custom Policy for Metrics

Create a custom policy with this JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 3: Configure AWS Credentials

If running locally (not on EC2 with IAM role):

```bash
# Option 1: AWS CLI configure
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1

# Option 3: Credentials file (~/.aws/credentials)
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
```

## Usage

### Automatic Integration

CloudWatch logging is automatically enabled when:
- Running on EC2 with proper IAM role
- AWS credentials are configured
- `boto3` is installed

The code will **gracefully degrade** if CloudWatch is not available (no errors, just local logging).

### What Gets Logged

**Logs** (`/aws/latency-orchestrator/logs`):
- Run start/end times
- Training progress milestones
- S3 upload status
- Errors and warnings
- Configuration details

**Metrics** (Namespace: `LatencyOrchestrator`):
- `TrainingAverageLatency`: Average latency from training (Milliseconds)
- `TrainingReward`: RL reward per episode (None)
- `TaskLatency`: Per-task latency with dimensions NodeType, AppType (Milliseconds)
- `EvaluationEdgeAvgLatency`: Average edge node latency (Milliseconds)
- `EvaluationCloudAvgLatency`: Average cloud node latency (Milliseconds)
- `S3UploadSuccess`: Number of successful S3 uploads (Count)
- `S3UploadFailure`: Number of failed S3 uploads (Count)
- `JobCompletion`: Job completion status (Count)

### Viewing Logs

**Via AWS Console:**
1. Go to **CloudWatch** → **Logs** → **Log groups**
2. Click `/aws/latency-orchestrator/logs`
3. Select a log stream to view messages

**Via AWS CLI:**
```bash
# List log streams
aws logs describe-log-streams \
  --log-group-name /aws/latency-orchestrator/logs \
  --region us-east-1

# View recent logs
aws logs tail /aws/latency-orchestrator/logs \
  --follow \
  --region us-east-1
```

### Viewing Metrics

**Via AWS Console:**
1. Go to **CloudWatch** → **Metrics** → **All metrics**
2. Under **Custom namespaces**, select **LatencyOrchestrator**
3. Browse available metrics

**Via AWS CLI:**
```bash
# Get metric statistics
aws cloudwatch get-metric-statistics \
  --namespace LatencyOrchestrator \
  --metric-name TrainingAverageLatency \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average \
  --region us-east-1
```

## 🔍 Troubleshooting

### Issue: "CloudWatch logging disabled (local mode)"

**Solution**: This is normal if running locally without AWS credentials. CloudWatch will work automatically on EC2 with IAM role.

### Issue: "Access Denied" errors

**Solution**: Check IAM permissions:
```bash
# Test permissions
aws logs describe-log-groups \
  --log-group-name-prefix /aws/latency-orchestrator \
  --region us-east-1

aws cloudwatch put-metric-data \
  --namespace TestNamespace \
  --metric-data MetricName=TestMetric,Value=1.0,Unit=Count \
  --region us-east-1
```

### Issue: Logs not appearing

**Solution**: 
1. Check log group exists: `aws logs describe-log-groups --region us-east-1`
2. Verify IAM permissions
3. Check CloudWatch service is available in your region

### Issue: Too many API calls / High costs

**Solution**: The code already throttles metric publishing:
- Training metrics: Every 10% of episodes (not every episode)
- Task latency: Every 10th task (not every task)

You can adjust these in `utils/cloudwatch.py` and `train_rl.py` if needed.

## 💰 Cost Considerations

- **CloudWatch Logs**: First 5 GB/month is free, then $0.50/GB
- **CloudWatch Metrics**: First 10 metrics free, then $0.30/metric/month
- **Data ingestion**: Minimal (we throttle metric publishing)

With default settings, costs should be < $1/month for typical usage.

## 📚 Additional Resources

- [CloudWatch Logs Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/)
- [CloudWatch Metrics Documentation](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)
- [boto3 CloudWatch Examples](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/logs.html)

