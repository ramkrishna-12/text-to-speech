variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment name (dev/staging/prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Short name used to prefix resources"
  type        = string
  default     = "tts-app"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDRs for public subnets (ALB)"
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDRs for private subnets (ECS tasks)"
  type        = list(string)
  default     = ["10.20.11.0/24", "10.20.12.0/24"]
}

variable "container_port" {
  description = "Port the FastAPI container listens on"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "Fargate task CPU units"
  type        = string
  default     = "256"
}

variable "task_memory" {
  description = "Fargate task memory (MB)"
  type        = string
  default     = "512"
}

variable "desired_count" {
  description = "Desired number of running tasks"
  type        = number
  default     = 2
}

variable "min_capacity" {
  description = "Minimum tasks for autoscaling"
  type        = number
  default     = 2
}

variable "max_capacity" {
  description = "Maximum tasks for autoscaling"
  type        = number
  default     = 6
}

variable "ecr_image_tag" {
  description = "Image tag to deploy (set by CI/CD, e.g. the git SHA)"
  type        = string
  default     = "latest"
}

variable "ecr_retained_image_count" {
  description = "Number of most-recent images to retain in ECR before expiry"
  type        = number
  default     = 5
}

variable "alarm_notification_email" {
  description = "Email for CloudWatch alarm notifications (optional)"
  type        = string
  default     = ""
}
