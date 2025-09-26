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

        docker run -d --restart unless-stopped -p 80:8000 \
        # --- DATABASE VARIABLES UPDATED ---
        -e WRITER_DB_HOST=${aws_rds_global_cluster.main.endpoint} \
        -e READER_DB_HOST=${aws_rds_cluster.main.reader_endpoint} \
        -e DATABASE_NAME=${aws_rds_cluster.main.database_name} \
        -e DATABASE_USER=${aws_rds_cluster.main.master_username} \
        -e DATABASE_PASSWORD=${var.db_password} \
        -e DATABASE_PORT=${aws_rds_cluster.main.port} \
        # --- CACHE VARIABLES ---
        # Note: The elasticache cluster is not defined in the provided files.
        # This line will cause an error if the resource "aws_elasticache_cluster.tf_cache" is not defined elsewhere.
        # -e REDIS_HOST=${aws_elasticache_cluster.tf_cache.cache_nodes[0].address} \
        # -e REDIS_PORT=${var.cache_port} \
        2000023946/userauthmodule:latest
    EOF

    tags = {
    Name = "single-app-server"
    }
}

