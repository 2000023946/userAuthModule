resource "aws_instance" "app_server" {
  ami           = "resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
  instance_type = "t3.micro"

  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  user_data = <<-EOF
    #!/bin/bash
    yum update -y
    yum install -y docker
    systemctl start docker
    systemctl enable docker
    usermod -a -G docker ec2-user

    # The docker run command now includes REDIS_HOST and REDIS_PORT
    docker run -d --restart unless-stopped -p 80:8000 \
      -e DATABASE_HOST=${aws_db_instance.tf_rds.address} \
      -e DATABASE_NAME=${aws_db_instance.tf_rds.db_name} \
      -e DATABASE_USER=${aws_db_instance.tf_rds.username} \
      -e DATABASE_PASSWORD=${var.db_password} \
      -e DATABASE_PORT=${var.db_port} \
      -e REDIS_HOST=${aws_elasticache_cluster.tf_cache.cache_nodes[0].address} \
      -e REDIS_PORT=${var.cache_port} \
      2000023946/userauthmodule:latest
  EOF

  tags = {
    Name = "single-app-server"
  }
}