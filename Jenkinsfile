pipeline {

    agent any

    environment {

        AWS_REGION = "ap-south-2"

        AWS_ACCOUNT_ID = "599499159844"

        ECR_REPOSITORY = "seclock"

        ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

        IMAGE_NAME = "${ECR_REGISTRY}/${ECR_REPOSITORY}"

        IMAGE_TAG = "${BUILD_NUMBER}"

        EKS_CLUSTER_NAME = "beginner-cluster"
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source code from GitHub...'
                checkout scm
            }
        }

        stage('Python Setup') {
            steps {
                echo 'Installing Python dependencies...'

                sh '''
                    python3 --version
                    pip3 --version

                    pip3 install --break-system-packages -r requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Running Python tests...'

                sh '''
                    python3 -m compileall .

                    python3 -m pytest test_e2e.py -v
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                echo 'Running SonarQube analysis...'

                withSonarQubeEnv('SonarQube') {

                    sh '''
                        sonar-scanner \
                        -Dsonar.projectKey=seclock \
                        -Dsonar.projectName=seclock \
                        -Dsonar.sources=. \
                        -Dsonar.exclusions="venv/**,__pycache__/**,sample_certificates/**,.git/**"
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'

                sh '''
                    docker build \
                    -t ${IMAGE_NAME}:${IMAGE_TAG} \
                    -t ${IMAGE_NAME}:latest \
                    .
                '''
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                echo 'Logging into Amazon ECR...'

                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding',
                     credentialsId: 'aws-credentials']
                ]) {

                    sh '''
                        aws ecr get-login-password \
                        --region ${AWS_REGION} | \
                        docker login \
                        --username AWS \
                        --password-stdin ${ECR_REGISTRY}
                    '''
                }
            }
        }

        stage('Push Image to ECR') {
            steps {
                echo 'Pushing Docker image to Amazon ECR...'

                sh '''
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}
                    docker push ${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Deploy to EKS') {
            steps {
                echo 'Deploying application to Amazon EKS...'

                withCredentials([
                    [$class: 'AmazonWebServicesCredentialsBinding',
                     credentialsId: 'aws-credentials']
                ]) {

                    sh '''
                        aws eks update-kubeconfig \
                        --region ${AWS_REGION} \
                        --name ${EKS_CLUSTER_NAME}

                        kubectl apply -f k8s/namespace.yaml

                        kubectl apply -f k8s/deployment.yaml

                        kubectl apply -f k8s/service.yaml

                        kubectl set image deployment/seclock-deployment \
                        seclock=${IMAGE_NAME}:${IMAGE_TAG} \
                        -n seclock

                        kubectl rollout status \
                        deployment/seclock-deployment \
                        -n seclock
                    '''
                }
            }
        }

        stage('Verify EKS Deployment') {
            steps {
                echo 'Checking EKS deployment...'

                sh '''
                    echo "===== PODS ====="
                    kubectl get pods -n seclock

                    echo "===== DEPLOYMENT ====="
                    kubectl get deployment -n seclock

                    echo "===== SERVICE ====="
                    kubectl get svc -n seclock
                '''
            }
        }
    }

    post {

        success {
            echo '''
            ==========================================
              SECLOCK CI/CD PIPELINE SUCCESSFUL
            ==========================================

              GitHub
                 ↓
              Jenkins
                 ↓
              Python Tests
                 ↓
              SonarQube
                 ↓
              Docker
                 ↓
              Amazon ECR
                 ↓
              Amazon EKS
                 ↓
              LoadBalancer

            ==========================================
            '''
        }

        failure {
            echo '''
            ==========================================
              SECLOCK CI/CD PIPELINE FAILED
            ==========================================

              Check Jenkins Console Output

            ==========================================
            '''
        }
    }
}
   
