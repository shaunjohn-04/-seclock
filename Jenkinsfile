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
                echo 'Checking out source code...'

                checkout scm
            }
        }


        stage('Python Setup') {
            steps {
                echo 'Checking Python...'

                sh '''
                    python3 --version
                    pip3 --version

                    python3 -m venv venv

                    . venv/bin/activate

                    pip install --upgrade pip

                    pip install -r requirements.txt
                '''
            }
        }


        stage('Test') {
            steps {
                echo 'Running Python tests...'

                sh '''
                    . venv/bin/activate

                    python -m compileall .

                    python -m pytest test_e2e.py -v
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
                        -Dsonar.python.version=3.12 \
                        -Dsonar.exclusions="venv/**,__pycache__/**,sample_certificates/**"
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
                echo 'Logging in to Amazon ECR...'

                sh '''
                    aws ecr get-login-password \
                    --region ${AWS_REGION} | \
                    docker login \
                    --username AWS \
                    --password-stdin ${ECR_REGISTRY}
                '''
            }
        }


        stage('Push Image to ECR') {
            steps {
                echo 'Pushing image to Amazon ECR...'

                sh '''
                    docker push ${IMAGE_NAME}:${IMAGE_TAG}

                    docker push ${IMAGE_NAME}:latest
                '''
            }
        }


        stage('Deploy to EKS') {
            steps {
                echo 'Deploying application to EKS...'

                sh '''
                    aws eks update-kubeconfig \
                    --region ${AWS_REGION} \
                    --name ${EKS_CLUSTER_NAME}

                    kubectl apply \
                    -f k8s/namespace.yaml

                    kubectl apply \
                    -f k8s/deployment.yaml

                    kubectl apply \
                    -f k8s/service.yaml

                    kubectl set image \
                    deployment/seclock-deployment \
                    seclock=${IMAGE_NAME}:${IMAGE_TAG} \
                    -n seclock

                    kubectl rollout status \
                    deployment/seclock-deployment \
                    -n seclock
                '''
            }
        }


        stage('Verify EKS Deployment') {
            steps {

                echo 'Checking EKS resources...'

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
              SonarQube
                 ↓
              Docker Build
                 ↓
              Amazon ECR
                 ↓
              Amazon EKS
                 ↓
              AWS LoadBalancer
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
