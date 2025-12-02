output "s3_bucket_name" {
  value = aws_s3_bucket.orchestrator_bucket.bucket
}

output "ec2_public_ip" {
  value = aws_instance.rl_instance.public_ip
}

output "ec2_instance_id" {
  value = aws_instance.rl_instance.id
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group for orchestrator logs"
  value       = var.create_cloudwatch_log_group ? (length(aws_cloudwatch_log_group.orchestrator_logs) > 0 ? aws_cloudwatch_log_group.orchestrator_logs[0].name : null) : data.aws_cloudwatch_log_group.existing_logs[0].name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch Log Group"
  value       = var.create_cloudwatch_log_group ? (length(aws_cloudwatch_log_group.orchestrator_logs) > 0 ? aws_cloudwatch_log_group.orchestrator_logs[0].arn : null) : data.aws_cloudwatch_log_group.existing_logs[0].arn
}