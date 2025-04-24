pipeline {
    agent any

    environment {
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
        CLUSTER_NAME = 'cluster-1'
        CLUSTER_ZONE = 'us-central1-c'
        PROJECT_ID = 'core-veld-455815-d7'  // Sửa thành project ID đúng
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Checkout') {
            steps {
                // Checkout code from SCM rather than cloning explicitly
                checkout scm
            }
        }

        stage('Build and Push') {
            steps {
                script {
                    echo '🔧 Building image for deployment...'
                    sh "docker build -t ${registry}:${imageTag} -f ./rag_medical/Dockerfile ./rag_medical"
                    echo '🚀 Pushing image to Docker Hub...'
                    withCredentials([usernamePassword(credentialsId: registryCredential, usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        sh """
                            docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}
                            docker push ${registry}:${imageTag}
                            docker tag ${registry}:${imageTag} ${registry}:latest
                            docker push ${registry}:latest
                        """
                    }
                }
            }
        }

        stage('Authenticate GCP') {
            steps {
                withCredentials([file(credentialsId: 'gcp-credentials', variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh """
                        # Activate service account
                        gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                        
                        # Set project
                        gcloud config set project ${PROJECT_ID}
                        
                        # Verify project access
                        if ! gcloud projects describe ${PROJECT_ID} > /dev/null 2>&1; then
                            echo "ERROR: No access to project ${PROJECT_ID}"
                            exit 1
                        fi
                        
                        # Get cluster credentials
                        gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${CLUSTER_ZONE} --project ${PROJECT_ID}
                        
                        # Verify cluster access
                        if ! kubectl get nodes > /dev/null 2>&1; then
                            echo "ERROR: Cannot access GKE cluster"
                            exit 1
                        fi
                    """
                }
            }
        }

        stage('Deploy to GKE with Helm') {
            steps {
                script {
                    echo '🚢 Running Helm upgrade...'
                    sh """
                        helm upgrade --install rag-medical ./rag_medical/helm_rag_medical \
                          --namespace rag-controller --create-namespace \
                          --set deployment.image.name=${registry} \
                          --set deployment.image.version=${imageTag} \
                          --atomic --wait
                    """
                }
            }
        }
    }

}