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
                    yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-deployer
spec:
  serviceAccountName: jenkins
  containers:
    - name: helm
      image: alpine/helm:3.12.3
      command:
        - cat
      tty: true
  restartPolicy: Never
"""
                }
            }
            steps {
                container('helm') {
                    sh """
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
