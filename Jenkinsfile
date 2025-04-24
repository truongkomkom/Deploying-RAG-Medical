pipeline {
    agent any

    environment {
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
        CLUSTER_CONTEXT = 'gke_core-veld-455815-d7_us-central1-c_cluster-1'
        KUBECONFIG = '/root/.kube/config'  // Vì bạn chạy container Jenkins với user root (-u 0)
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/truongkomkom/Deploying-RAG-Medical.git', branch: 'main'
            }
        }

        stage('Build and Push') {
            steps {
                script {
                    echo '🔧 Building image for deployment...'
                    def dockerImage = docker.build("${registry}:${imageTag}", "-f ./rag_medical/Dockerfile ./rag_medical")
                    echo '🚀 Pushing image to Docker Hub...'
                    docker.withRegistry('', registryCredential) {
                        dockerImage.push()
                        dockerImage.push('latest')  // Also push as latest tag
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
