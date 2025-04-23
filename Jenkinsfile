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
                    echo 'Building image for deployment...'
                    def dockerImage = docker.build("${registry}:${imageTag}", "-f ./rag_medical/Dockerfile ./rag_medical")
                    echo 'Pushing image to Docker Hub...'
                    docker.withRegistry('', registryCredential) {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Deploy') {
            agent {
                kubernetes {
                    containerTemplate {
                        name 'helm' // Tên container để sử dụng cho helm upgrade
                        image 'nthaiduong83/jenkins-k8s:v1' // Image có sẵn helm + kubectl
                        alwaysPullImage true // Luôn kéo lại image khi chạy
                    }
                }
            }
            steps {
                script {
                    container('helm') {
                        sh """
                            echo 'Triển khai ứng dụng bằng Helm...'
                            helm upgrade --install rag-medical ./rag_medical/helm_rag_medical \\
                                --namespace rag-controller \\
                                --set deployment.image.name=${registry} \\
                                --set deployment.image.version=${imageTag}
                        """
                    }
                }
            }
        }
    }
}
