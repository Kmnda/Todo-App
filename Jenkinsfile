pipeline {
    agent any

    environment {
        // --- CONFIGURATION ---
        AWS_ACCOUNT_ID = '380171765307' 
        AWS_REGION     = 'ap-southeast-1'
        ECR_REPO_NAME  = 'todo-app'
        EC2_IP         = '54.179.160.195' 
        IMAGE_TAG      = "${BUILD_NUMBER}"
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
                        sh "docker build -t ${ECR_REPO_NAME} ."
                        sh "docker tag ${ECR_REPO_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:${IMAGE_TAG}"
                        sh "docker tag ${ECR_REPO_NAME}:latest ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"
                        sh "docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:${IMAGE_TAG}"
                        sh "docker push ${ECR_REGISTRY}/${ECR_REPO_NAME}:latest"
                    }
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sshagent(['ec2-ssh-key']) {
                    // --- FIX: Use withAWS to unwrap the 'AWS Credentials' object ---
                    withAWS(credentials: 'aws-creds', region: AWS_REGION) {
                        script {
                            // 1. Copy config files
                            sh "scp -o StrictHostKeyChecking=no docker-compose.yml ec2-user@${EC2_IP}:/home/ec2-user/docker-compose.yml"
                            sh "scp -o StrictHostKeyChecking=no prometheus.yml ec2-user@${EC2_IP}:/home/ec2-user/prometheus.yml"

                            // 2. Remote Deployment
                            // We inject the env vars provided by withAWS into the SSH session
                            sh """
                            ssh -o StrictHostKeyChecking=no ec2-user@${EC2_IP} '
                                # Inject keys from Jenkins environment to Remote Server environment
                                export AWS_ACCESS_KEY_ID=${env.AWS_ACCESS_KEY_ID}
                                export AWS_SECRET_ACCESS_KEY=${env.AWS_SECRET_ACCESS_KEY}
                                export AWS_DEFAULT_REGION=${AWS_REGION}
                                
                                # Set Image URI
                                export ECR_IMAGE_URI=${ECR_REGISTRY}/${ECR_REPO_NAME}:latest

                                # Login to ECR
                                aws ecr get-login-password | docker login --username AWS --password-stdin ${ECR_REGISTRY}

                                # Cleanup Old Containers
                                docker stop todo-app || true
                                docker rm todo-app || true

                                # Pull & Start
                                docker-compose pull
                                docker-compose up -d --remove-orphans
                            '
                            """
                        }
                    }
                }
            }
        }
    }
}