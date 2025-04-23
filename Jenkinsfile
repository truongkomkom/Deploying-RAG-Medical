pipeline {
    agent any

    environment {
        KUBECONFIG = "C:/Users/MINH TRUONG/.kube/config"  // Đường dẫn đến kubeconfig của bạn
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
        CLUSTER_CONTEXT = 'gke_core-veld-455815-d7_us-central1-c_cluster-1'  // Thay bằng tên context mà bạn tìm thấy
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
                    // Chọn context từ kubeconfig trước khi chạy lệnh Helm
                    echo '🚢 Running Helm upgrade...'
                    sh """
                        export KUBECONFIG=${KUBECONFIG}
                        kubectl config use-context ${CLUSTER_CONTEXT}  // Chỉ định context
                        helm upgrade --install rag-medical ./rag_medical/helm_rag_medical --namespace rag-controller --create-namespace --set deployment.image.name=${registry} --set deployment.image.version=${imageTag}
                    """
                }
            }
        }
    }
}
