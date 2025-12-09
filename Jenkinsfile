pipeline {
    agent any

    environment {
        // --- CONFIGURATION ---
        AWS_ACCOUNT_ID = '380171765307' 
        AWS_REGION     = 'ap-southeast-1'
        ECR_REPO_NAME  = 'todo-app'
        EC2_IP         = '54.179.160.195'
        IMAGE_TAG      = "${BUILD_NUMBER}"
        // Full Registry URL
        ECR_REGISTRY   = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    }

    stages {
        stage('Login to AWS ECR') {
            steps {
                script {
                    withAWS(credentials: 'aws-creds', region: AWS_REGION) {
                        sh "aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}"
                    }
                }
            }
        }

        stage('Build & Push') {
            steps {
                script {
                    withAWS(credentials: 'aws-creds', region: AWS_REGION) {
                        // Build
                        sh "docker build -t ${ECR_REPO_NAME} ."
                        
                        // Tag
                        sh "docker tag ${ECR_REPO_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:${IMAGE_TAG}"
                        sh "docker tag ${ECR_REPO_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"

                        // Push both tags
                        sh "docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:${IMAGE_TAG}"
                        sh "docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"
                    }
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    script {
                        // 1. Copy config files to Server (SCP)
                        // This updates the logic on the server with your latest docker-compose
                        sh "scp -o StrictHostKeyChecking=no docker-compose.yml ec2-user@${EC2_IP}:/home/ec2-user/docker-compose.yml"
                        sh "scp -o StrictHostKeyChecking=no prometheus.yml ec2-user@${EC2_IP}:/home/ec2-user/prometheus.yml"

                        // 2. Run Deployment Remotely
                        sh """
                        ssh -o StrictHostKeyChecking=no ec2-user@${EC2_IP} '
                            # Set the Image URI variable so docker-compose knows what to pull
                            export ECR_IMAGE_URI=${ECR_REGISTRY}/${ECR_REPO_NAME}:latest

                            # Login to ECR on the server
                            aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

                            # --- CRITICAL FIX: CLEANUP ---
                            # Stop any old "manual" containers to free up Port 5000
                            docker stop todo-app || true
                            docker rm todo-app || true

                            # Pull the latest images
                            docker-compose pull

                            # Start the stack (Detached)
                            # --remove-orphans cleans up any old services that were deleted from the file
                            docker-compose up -d --remove-orphans
                        '
                        """
                    }
                }
            }
        }
    }
}