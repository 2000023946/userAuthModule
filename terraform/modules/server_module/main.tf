# File: modules/server_module/main.tf

// =================================================================================
// Load Balancer (Public Facing)
// =================================================================================

resource "aws_lb" "main" {
  name               = "${var.name_prefix}-app-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.load_balancer_sg_id]
  subnets            = var.public_subnet_ids # Correctly in public subnets

  tags = {
    Name = "${var.name_prefix}-alb"
  }
}

resource "aws_lb_target_group" "main" {
  name     = "${var.name_prefix}-app-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = "/"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${var.name_prefix}-target-group"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}


// =================================================================================
// EC2 Launch Template & Auto Scaling Group (Private and Secure)
// =================================================================================

resource "aws_launch_template" "main" {
  name_prefix   = "${var.name_prefix}-app-"
  image_id      = "resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
  instance_type = var.instance_type
  key_name      = var.key_name

  vpc_security_group_ids = [var.app_server_sg_id]

  # For a real production system, use AWS Secrets Manager instead of environment variables
  user_data = base64encode(<<-EOF
      #!/bin/bash
      yum update -y
      yum install -y docker
      systemctl start docker
      systemctl enable docker
      usermod -a -G docker ec2-user

      docker run -d --restart unless-stopped -p 80:8000 \
      -e WRITER_DB_HOST=${var.writer_db_host} \
      -e READER_DB_HOST=${var.reader_db_host} \
      -e DATABASE_NAME=${var.database_name} \
      -e DATABASE_USER=${var.database_user} \
      -e DATABASE_PASSWORD=${var.db_password} \
      -e DATABASE_PORT=${var.database_port} \
      ${var.docker_image}
  EOF
  )

  tags = {
    Name = "${var.name_prefix}-launch-template"
  }
}

resource "aws_autoscaling_group" "main" {
  name                = "${var.name_prefix}-asg"
  desired_capacity    = 2
  max_size            = 5
  min_size            = 1

  vpc_zone_identifier = var.private_subnet_ids
  target_group_arns   = [aws_lb_target_group.main.arn]

  launch_template {
    id      = aws_launch_template.main.id
    version = "$Latest"
  }

  # This is the corrected block. 
  # Note it's a "tag" block, not a "tags = [...]" argument.
  tag {
    key                 = "Name"
    value               = "${var.name_prefix}-app-instance"
    propagate_at_launch = true
  }
}
// The manual aws_lb_target_group_attachment resource has been removed.
// The Auto Scaling Group handles this automatically.