pipeline {
    agent any

    environment {
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
        PROJECT_ID = 'core-veld-455815-d7'
        CLUSTER_NAME = 'cluster-1'
        CLUSTER_ZONE = 'us-central1-c'
    }

    stages {
        stage('Clean Workspace') {
            steps {
                cleanWs()
            }
        }

        stage('Checkout') {
            steps {
                sh 'git clone https://github.com/truongkomkom/Deploying-RAG-Medical.git .'
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                script {
                    echo '🔧 Building image for deployment...'
                    sh "docker build -t ${registry}:${imageTag} -f ./rag_medical/Dockerfile ./rag_medical"

                    echo '🚀 Pushing image to Docker Hub...'
                    withCredentials([usernamePassword(credentialsId: registryCredential, usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        sh """
                            echo "${DOCKER_PASSWORD}" | docker login -u "${DOCKER_USERNAME}" --password-stdin
                            docker push ${registry}:${imageTag}
                            docker tag ${registry}:${imageTag} ${registry}:latest
                            docker push ${registry}:latest
                        """
                    }
                }
            }
        }

        stage('Deploy to GKE') {
            steps {
                script {
                    echo '🚢 Getting GKE credentials and deploying...'
                    sh """
                        gcloud config set project ${PROJECT_ID}
                        gcloud container clusters get-credentials ${CLUSTER_NAME} --zone ${CLUSTER_ZONE}

                        helm upgrade --install rag-medical ./rag_medical/helm_rag_medical \
                          --namespace rag-controller --create-namespace \
                          --set deployment.image.name=${registry} \
                          --set deployment.image.version=${imageTag} \
                          --atomic
                    """
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed!'
        }
    }
}
