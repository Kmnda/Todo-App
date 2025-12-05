pipeline {
    agent any

    environment {
        // --- CONFIGURATION ---
        // Double check these values matches your AWS/Terraform output
        AWS_ACCOUNT_ID = '380171765307' 
        AWS_REGION     = 'ap-southeast-1'
        ECR_REPO_NAME  = 'todo-app'
        EC2_IP         = '13.229.100.152'
        IMAGE_TAG      = "${BUILD_NUMBER}"
    }

    stages {
        stage('Login to AWS ECR') {
            steps {
                script {
                    // NEW CODE: Using 'withAWS' for AWS Credentials kind
                    // This automatically injects your AKIA... and Secret Key into the environment
                    withAWS(credentials: 'aws-creds', region: AWS_REGION) {
                        sh """
                        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
                        """
                    }
                }
            }
        }

        stage('Build & Tag Image') {
            steps {
                script {
                    // Build the Docker image
                    sh "docker build -t ${ECR_REPO_NAME} ."
                    
                    // Tag it for ECR
                    sh "docker tag ${ECR_REPO_NAME}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}"
                    sh "docker tag ${ECR_REPO_NAME}:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest"
                }
            }
        }

        stage('Push to ECR') {
            steps {
                script {
                    // We need AWS permissions to push, so we wrap this in withAWS too
                    withAWS(credentials: 'aws-creds', region: AWS_REGION) {
                        sh "docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:${IMAGE_TAG}"
                        sh "docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest"
                    }
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                // Connect to EC2 using the SSH Key credential
                sshagent(['ec2-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ec2-user@${EC2_IP} '
                            # Note: The EC2 server uses its own "aws configure" settings we did earlier
                            # It does NOT use the Jenkins credentials
                            aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

                            docker pull ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest

                            docker stop todo-app || true
                            docker rm todo-app || true

                            docker run -d \
                                --name todo-app \
                                -p 5000:5000 \
                                --restart always \
                                -e POSTGRES_HOST=172.17.0.1 \
                                -e POSTGRES_USER=app_user \
                                -e POSTGRES_PASSWORD=secret \
                                ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}:latest
                        '
                    """
                }
            }
        }
    }
}