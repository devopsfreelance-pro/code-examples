output "autoscaling_group_name" {
  value = aws_autoscaling_group.web.name
}

output "launch_template_id" {
  value = aws_launch_template.web.id
}

output "cloudwatch_alarm_name" {
  value = aws_cloudwatch_metric_alarm.cpu_high.alarm_name
}
