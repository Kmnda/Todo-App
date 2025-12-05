terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-1"  # Change if you prefer another region
}

# 1. THE NETWORK (VPC)
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "todo-vpc" }
}

# 2. THE PUBLIC SUBNET (Where your server lives)
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "ap-southeast-1a"
  tags = { Name = "todo-public-subnet" }
}

# 3. INTERNET GATEWAY (The door to the internet)
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "todo-igw" }
}

# 4. ROUTE TABLE (Traffic directions)
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

# 5. SECURITY GROUP (The Firewall)
resource "aws_security_group" "web_sg" {
  name        = "todo-web-sg"
  description = "Allow HTTP and SSH"
  vpc_id      = aws_vpc.main.id

  # Allow HTTP from anywhere (User traffic)
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow SSH from anywhere (For you to manage)
  # Ideally, restrict this to your IP: ["YOUR_IP/32"]
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # Allow all outbound traffic (Updates, etc)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 6. SSH KEY PAIR (Upload your local key to AWS)
resource "aws_key_pair" "deployer" {
  key_name   = "deployer-key"
  public_key = file("~/.ssh/aws_key.pub")
}

# 7. THE SERVER (EC2 Instance)
resource "aws_instance" "app_server" {
  ami           = "ami-06d753822bd94c64e" # Amazon Linux 2023 (Free Tier Eligible in us-east-1)
  instance_type = "t2.micro"
  
  subnet_id     = aws_subnet.public.id
  key_name      = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.web_sg.id]

  tags = { Name = "Todo-App-Server" }
}
# 9. ECR REPOSITORY (Docker Image Store)
resource "aws_ecr_repository" "app_repo" {
  name         = "todo-app"
  force_delete = true  # Allows destroying repo even if it has images
}

output "ecr_url" {
  value = aws_ecr_repository.app_repo.repository_url
}
# 8. OUTPUT (Tell us the IP)
output "server_public_ip" {
  value = aws_instance.app_server.public_ip
}