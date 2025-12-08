terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-1" # You can safely change this region now!
}

# --- DATA SOURCES (The fix for hardcoded values) ---

# 1. Fetch the latest Amazon Linux 2023 AMI automatically
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# 2. Fetch available Availability Zones in the current region
data "aws_availability_zones" "available" {
  state = "available"
}

# --- RESOURCES ---

# 1. THE NETWORK (VPC)
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true # Good practice for public access
  enable_dns_support   = true
  tags                 = { Name = "todo-vpc" }
}

# 2. THE PUBLIC SUBNET
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  # Dynamic AZ: Pick the first available zone in your region
  availability_zone       = data.aws_availability_zones.available.names[0]
  tags                    = { Name = "todo-public-subnet" }
}

# 3. INTERNET GATEWAY
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "todo-igw" }
}

# 4. ROUTE TABLE
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = { Name = "todo-public-rt" }
}

resource "aws_route_table_association" "a" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public_rt.id
}

# 5. SECURITY GROUP
resource "aws_security_group" "web_sg" {
  name        = "todo-web-sg"
  description = "Allow HTTP, Grafana, and SSH"
  vpc_id      = aws_vpc.main.id

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # Grafana
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  # SSH (WARNING: 0.0.0.0/0 allows the whole world to try logging in)
  # For production, replace "0.0.0.0/0" with your specific IP: ["YOUR_IP/32"]
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound Traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 6. SSH KEY PAIR
# PREREQUISITE: Run `ssh-keygen -f ~/.ssh/aws_key` in your terminal first!
resource "aws_key_pair" "deployer" {
  key_name   = "deployer-key"
  public_key = file("~/.ssh/aws_key.pub")
}

# 7. THE SERVER (EC2 Instance)
resource "aws_instance" "app_server" {
  # Use the dynamic AMI ID we fetched earlier
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t2.micro"

  subnet_id              = aws_subnet.public.id
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  # User Data to install Docker immediately (Optional but helpful)
  user_data = <<-EOF
              #!/bin/bash
              dnf update -y
              dnf install -y docker git
              service docker start
              usermod -a -G docker ec2-user
              EOF

  tags = { Name = "Todo-App-Server" }
}

# 9. ECR REPOSITORY
resource "aws_ecr_repository" "app_repo" {
  name         = "todo-app"
  force_delete = true
}

# OUTPUTS
output "ecr_url" {
  value = aws_ecr_repository.app_repo.repository_url
}

output "server_public_ip" {
  value = aws_instance.app_server.public_ip
}