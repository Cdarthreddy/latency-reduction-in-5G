output "s3_bucket_name" {
  value = aws_s3_bucket.orchestrator_bucket.bucket
}

output "ec2_public_ip" {
  value = aws_instance.rl_instance.public_ip
}

output "ec2_instance_id" {
  value = aws_instance.rl_instance.id
}
