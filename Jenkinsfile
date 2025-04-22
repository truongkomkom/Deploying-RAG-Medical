pipeline {
    agent any

    environment{
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
    }

    stages {
        stage('Build and Push') {
            when {
                changeset "**/rag_medical/**"  // Kiểm tra sự thay đổi trong thư mục rag_medical
            }
            steps {
                script {
                    echo 'Building image for deployment..'
                    def dockerImage = docker.build("${registry}:${imageTag}", "-f ./rag_medical/Dockerfile ./rag_medical")
                    echo 'Pushing image to dockerhub..'
                    docker.withRegistry( '', registryCredential ) {
                        dockerImage.push()
                    }
                }
            }
        }

        stage('Deploy') {
            when {
                changeset "**/rag_medical/**"  // Kiểm tra sự thay đổi trong thư mục rag_medical
            }
            agent {
                kubernetes {
                    containerTemplate {
                        name 'helm' // Name of the container to be used for helm upgrade
                        image 'nthaiduong83/jenkins-k8s:v1' // The image containing helm
                        alwaysPullImage true // Always pull image in case of using the same tag
                    }
                }
            }
            steps {
                script {
                    container('helm') {
                        sh("helm upgrade --install rag-medical ./rag_medical/helm_rag_medical --namespace rag-controller --set deployment.image.name=${registry} --set deployment.image.version=${imageTag}")
                    }
                }
            }
        }
    }
}
