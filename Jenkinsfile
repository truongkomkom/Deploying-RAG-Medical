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
                    // Ensure Docker can be accessed with sudo
                    def dockerImage = sh(script: "sudo docker build -t ${registry}:${imageTag} -f ./rag_medical/Dockerfile ./rag_medical", returnStdout: true).trim()
                    echo 'Docker image built: ${dockerImage}'
                    echo 'Pushing image to Docker Hub...'
                    // Push Docker image
                    docker.withRegistry('', registryCredential) {
                        sh "sudo docker push ${registry}:${imageTag}"
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
  containers:
    - name: helm
      image: nthaiduong83/jenkins-k8s:v1
      imagePullPolicy: Always
      command:
        - cat
      tty: true
    - name: jnlp
      image: jenkins/inbound-agent:latest
      imagePullPolicy: Always
      env:
        - name: JENKINS_AGENT_URL
          value: 'http://jenkins:8080'
      tty: true
"""
                }
            }
            steps {
                container('helm') {
                    sh """
                        echo 'Deploying the application using Helm...'
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
