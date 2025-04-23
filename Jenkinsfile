pipeline {
    agent any

    environment {
        KUBECONFIG = "C:/Users/MINH TRUONG/.kube/config"  // Đường dẫn đến kubeconfig của bạn
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
    }

    stages {
        stage('Build and Push') {
            steps {
                script {
                    echo '🔧 Building image for deployment...'
                    def dockerImage = docker.build("${registry}:${imageTag}", "-f ./rag_medical/Dockerfile ./rag_medical")
                    echo '🚀 Pushing image to Docker Hub...'
                    docker.withRegistry('', registryCredential) {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    // Chạy các lệnh kubectl hoặc helm, và xác thực từ kubeconfig
                    echo '🚢 Running Helm upgrade...'
                    sh """
                        export KUBECONFIG=${KUBECONFIG}
                        helm upgrade --install rag-medical ./rag_medical/helm_rag_medical --namespace rag-controller --create-namespace --set deployment.image.name=${registry} --set deployment.image.version=${imageTag}
                    """
                }
            }
        }
    }
}
