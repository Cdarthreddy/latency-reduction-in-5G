# Terraform Setup Guide

## ⚠️ Important: IAM Permissions

**Terraform requires IAM permissions to create IAM roles and policies.** 

If you're running Terraform from an EC2 instance that doesn't have admin/IAM permissions, you have two options:

### Option 1: Run Terraform Locally (Recommended)

Run Terraform from your local machine or a machine with IAM permissions:

```bash
# On your local machine (with AWS credentials configured)
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### Option 2: Use Existing IAM Resources

If the IAM role already exists and you're running Terraform from EC2 without IAM permissions:

1. Set the variable in `terraform.tfvars`:
```hcl
create_iam_resources = false
```

2. Make sure the IAM role `LatencyOrchestratorRole` already exists with the required policies attached.

---

## CloudWatch Log Group Already Exists

If you see this error:
```
ResourceAlreadyExistsException: The specified log group already exists
```

You have two options:

### Option 1: Use Existing Log Group

Set in `terraform.tfvars`:
```hcl
create_cloudwatch_log_group = false
```

### Option 2: Import Existing Log Group

```bash
terraform import aws_cloudwatch_log_group.orchestrator_logs /aws/latency-orchestrator/logs
```

---

## Quick Start

### 1. Configure Variables

Edit `terraform.tfvars`:
```hcl
aws_region     = "us-east-1"
bucket_name    = "rl-orchestrator-results"
ami_id         = "ami-0360c520857e3138f"  # Amazon Linux 2
instance_type  = "t3.small"
key_name       = "project.pem"
git_repo_url   = "https://github.com/your-username/LatencyReductionInCloud.git"

# Set to false if running from EC2 without IAM permissions
create_iam_resources = true

# Set to false if log group already exists
create_cloudwatch_log_group = true
```

### 2. Initialize Terraform

```bash
terraform init
```

### 3. Plan Changes

```bash
terraform plan
```

### 4. Apply Changes

```bash
terraform apply
```

---

## Common Issues

### Issue: "User is not authorized to perform: iam:CreateRole"

**Solution:** 
- Run Terraform from a machine with IAM permissions (your local machine)
- Or set `create_iam_resources = false` in `terraform.tfvars` if the role already exists

### Issue: "log group already exists"

**Solution:**
- Set `create_cloudwatch_log_group = false` in `terraform.tfvars`
- Or import the existing log group: `terraform import aws_cloudwatch_log_group.orchestrator_logs /aws/latency-orchestrator/logs`

### Issue: "Warning: Value for undeclared variable"

**Solution:** These warnings are harmless if you're using variables in `terraform.tfvars` that aren't declared. You can either:
- Ignore them (they won't affect execution)
- Add the variable declarations to `variables.tf`
- Remove unused variables from `terraform.tfvars`

---

## Manual IAM Setup (If Needed)

If you can't create IAM resources via Terraform, create them manually:

### 1. Create IAM Role

```bash
aws iam create-role \
  --role-name LatencyOrchestratorRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

### 2. Attach Policies

```bash
aws iam attach-role-policy \
  --role-name LatencyOrchestratorRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
  --role-name LatencyOrchestratorRole \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

### 3. Create Instance Profile

```bash
aws iam create-instance-profile \
  --instance-profile-name LatencyOrchestratorRole

aws iam add-role-to-instance-profile \
  --instance-profile-name LatencyOrchestratorRole \
  --role-name LatencyOrchestratorRole
```

### 4. Update Terraform

Set `create_iam_resources = false` in `terraform.tfvars` and run `terraform apply` again.

---

## Outputs

After successful deployment:

```bash
terraform output
```

Shows:
- `s3_bucket_name` - S3 bucket for artifacts
- `ec2_instance_id` - EC2 instance ID
- `ec2_public_ip` - EC2 public IP address
- `cloudwatch_log_group` - CloudWatch log group name

---

## Destroy Resources

To remove all created resources:

```bash
terraform destroy
```

**Note:** This will delete the EC2 instance, S3 bucket, IAM role (if created), and other resources.

