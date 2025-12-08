pipeline {
    agent any

    environment {
        // --- CONFIGURATION ---
        AWS_ACCOUNT_ID = '380171765307' 
        AWS_REGION     = 'ap-southeast-1'
        ECR_REPO_NAME  = 'todo-app'
        EC2_IP         = '13.214.211.37'
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
                        // Make sure prometheus.yml exists in your git repo!
                        sh "scp -o StrictHostKeyChecking=no docker-compose.yml ec2-user@${EC2_IP}:/home/ec2-user/docker-compose.yml"
                        sh "scp -o StrictHostKeyChecking=no prometheus.yml ec2-user@${EC2_IP}:/home/ec2-user/prometheus.yml"

                        // 2. Run Docker Compose Remotely
                        sh """
                        ssh -o StrictHostKeyChecking=no ec2-user@${EC2_IP} '
                            # Set the Image URI variable for the server session
                            export ECR_IMAGE_URI=${ECR_REGISTRY}/${ECR_REPO_NAME}:latest

                            # Login to ECR on the server
                            aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

                            # Pull the latest images
                            docker-compose pull

                            # Start the stack (Detached)
                            docker-compose up -d --remove-orphans
                        '
                        """
                    }
                }
            }
        }
    }
}
