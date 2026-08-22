output "alb_dns_name" {
  description = "Public URL of the app (via ALB)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecr_repository_url" {
  description = "ECR repo URL to push images to"
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  value = aws_ecs_service.app.name
}

output "cloudwatch_log_group" {
  value = aws_cloudwatch_log_group.app.name
}

output "github_actions_role_arn" {
  description = "Role ARN to put in the GH Actions workflow's role-to-assume"
  value       = aws_iam_role.github_actions_deploy.arn
}
