pipeline {
    agent any

    environment {
        registry = 'truongkomkom/truong_rag_medical'
        registryCredential = 'dockerhub'
        imageTag = "v1.$BUILD_NUMBER"
    }

    stages {
        stage('Build and Push') {
            when {
                changeset "**/rag_medical/**"
            }
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
            when {
                changeset "**/rag_medical/**"
            }
            agent {
                kubernetes {
                    yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    app: jenkins-deployer
spec:
  containers:
    - name: helm
      image: nthaiduong83/jenkins-k8s:v1
      imagePullPolicy: Always
      command:
        - cat
      tty: true
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
