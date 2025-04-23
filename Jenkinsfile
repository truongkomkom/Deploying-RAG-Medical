pipeline {
    agent any

    environment {
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
                    echo '🚢 Running Helm upgrade...'
                    sh """
                        echo 'Triển khai ứng dụng bằng Helm...'
                        helm upgrade --install rag-medical ./rag_medical/helm_rag_medical \\
                            --namespace rag-controller \\
                            --create-namespace \\
                            --set deployment.image.name=${registry} \\
                            --set deployment.image.version=${imageTag}
                    """
                }
            }
        }
    }
}
