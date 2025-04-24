pipeline {
    agent {
        docker {
            image 'docker:latest'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    options {
        skipDefaultCheckout()
    }

    environment {
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
        CLUSTER_CONTEXT = 'gke_core-veld-455815-d7_us-central1-c_cluster-1'
        KUBECONFIG = '/root/.kube/config'
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

        stage('Build and Push') {
            steps {
                script {
                    echo '🔧 Building image for deployment...'
                    sh "docker build -t ${registry}:${imageTag} -f ./rag_medical/Dockerfile ./rag_medical"
                    echo '🚀 Pushing image to Docker Hub...'
                    withCredentials([usernamePassword(credentialsId: registryCredential, usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                        sh "docker login -u ${DOCKER_USERNAME} -p ${DOCKER_PASSWORD}"
                        sh "docker push ${registry}:${imageTag}"
                        sh "docker push ${registry}:latest"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    echo '🚢 Running Helm upgrade...'
                    sh """
                        export KUBECONFIG=${KUBECONFIG}
                        kubectl config use-context ${CLUSTER_CONTEXT}
                        helm upgrade --install rag-medical ./rag_medical/helm_rag_medical \
                          --namespace rag-controller --create-namespace \
                          --set deployment.image.name=${registry} \
                          --set deployment.image.version=${imageTag} \
                          --atomic  # Rollback on failure
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
