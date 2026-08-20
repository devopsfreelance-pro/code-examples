terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2         = "http://localhost:4566"
    autoscaling = "http://localhost:4566"
    cloudwatch  = "http://localhost:4566"
    elbv2       = "http://localhost:4566"
    iam         = "http://localhost:4566"
    sts         = "http://localhost:4566"
  }
}

# VPC minima con dos subnets en distintas AZ, requisito de un ASG real
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "escalabilidad-aws-demo"
  }
}

resource "aws_subnet" "a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "escalabilidad-aws-subnet-a"
  }
}

resource "aws_subnet" "b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "escalabilidad-aws-subnet-b"
  }
}

# Launch Template: como se lanza cada instancia del Auto Scaling Group
resource "aws_launch_template" "web" {
  name          = "escalabilidad-aws-lt"
  image_id      = "ami-12345678"
  instance_type = "t3.micro"

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "escalabilidad-aws-instance"
    }
  }
}

# Auto Scaling Group: el componente central del post (escalado horizontal)
resource "aws_autoscaling_group" "web" {
  name                = "escalabilidad-aws-asg"
  min_size            = 2
  max_size            = 10
  desired_capacity    = 2
  health_check_type   = "EC2"
  vpc_zone_identifier = [aws_subnet.a.id, aws_subnet.b.id]

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "escalabilidad-aws-asg-instance"
    propagate_at_launch = true
  }
}

# Politica de escalado por target tracking en CPU, igual a la del post
resource "aws_autoscaling_policy" "cpu_target_tracking" {
  name                   = "escalabilidad-aws-cpu-policy"
  autoscaling_group_name = aws_autoscaling_group.web.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Alarma de CloudWatch que dispara el scale-out cuando CPU > 70% por 2 minutos
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "escalabilidad-aws-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 70
  alarm_description   = "Scale up si CPU > 70% durante 2 minutos"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.web.name
  }

  alarm_actions = [aws_autoscaling_policy.cpu_target_tracking.arn]
}
