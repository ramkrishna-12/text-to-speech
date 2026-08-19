terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Remote state - S3 + DynamoDB lock table. Create these two resources manually once
  # (or via a bootstrap script) before running `terraform init`, since state can't
  # bootstrap its own backend.
  backend "s3" {
    bucket         = "tts-app-terraform-state"   # override via -backend-config in CI
    key            = "tts-app/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "tts-app-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "tts-app"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}
