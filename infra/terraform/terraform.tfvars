aws_region    = "us-east-1"
bucket_name   = "rl-orchestrator-results"
instance_type = "t3.small"
# key_name      = "project.pem"  # Comment out or set to "" if key doesn't exist
key_name      = ""  # Leave empty if you don't have a key pair (or set to your actual key name)
ami_id        = "ami-0360c520857e3138f"
git_repo_url  = "https://github.com/rishichowdary539/LatencyReductionInCloud.git"

# Set to false if running from EC2 without IAM permissions
create_iam_resources = false

# Set to false if CloudWatch log group already exists
create_cloudwatch_log_group = false 