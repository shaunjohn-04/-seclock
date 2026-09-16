
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
                    echo "===== PYTHON COMPILE CHECK ====="

                    python3 -m py_compile \
                        main.py \
                        audit_ledger.py \
                        crypto_engine.py \
                        generate_certificates.py \
                        ocr_engine.py \
                        test_e2e.py

                    echo "===== RUNNING TESTS ====="

                    python3 -m pytest test_e2e.py -v
                '''
            }
        }


        stage('SonarQube Analysis') {
            steps {
                echo 'Running SonarQube analysis...'

                withSonarQubeEnv('SonarQube') {

                    withEnv(["PATH+SONAR=${tool 'SonarScanner'}/bin"]) {

                        sh '''
                            echo "===== SONARQUBE SCAN ====="

                            sonar-scanner \
                            -Dsonar.projectKey=seclock \
                            -Dsonar.projectName=seclock \
                            -Dsonar.sources=. \
                            -Dsonar.exclusions="venv/**,__pycache__/**,sample_certificates/**,.git/**,.pytest_cache/**"
                        '''
                    }
                }
            }
        }


        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'

                sh '''
                    echo "===== DOCKER BUILD ====="

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
                        echo "===== ECR LOGIN ====="

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
                    echo "===== PUSHING IMAGE TO ECR ====="

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
                        echo "===== CONNECTING TO EKS ====="

                        aws eks update-kubeconfig \
                        --region ${AWS_REGION} \
                        --name ${EKS_CLUSTER_NAME}


                        echo "===== CREATING NAMESPACE ====="

                        kubectl apply -f k8s/namespace.yaml


                        echo "===== APPLYING DEPLOYMENT ====="

                        kubectl apply -f k8s/deployment.yaml


                        echo "===== APPLYING SERVICE ====="

                        kubectl apply -f k8s/service.yaml


                        echo "===== UPDATING IMAGE ====="

                        kubectl set image deployment/seclock-deployment \
                        seclock=${IMAGE_NAME}:${IMAGE_TAG} \
                        -n seclock


                        echo "===== WAITING FOR ROLLOUT ====="

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
                    echo "=========================================="
                    echo "              PODS"
                    echo "=========================================="

                    kubectl get pods -n seclock


                    echo "=========================================="
                    echo "           DEPLOYMENT"
                    echo "=========================================="

                    kubectl get deployment -n seclock


                    echo "=========================================="
                    echo "             SERVICE"
                    echo "=========================================="

                    kubectl get svc -n seclock


                    echo "=========================================="
                    echo "          ENDPOINTS"
                    echo "=========================================="

                    kubectl get endpoints -n seclock
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
              Python Setup
                 ↓
              Python Tests
                 ↓
              SonarQube
                 ↓
              Docker Build
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
