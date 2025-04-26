docker volume create jenkins_data


docker run -u 0 --privileged --name jenkins -it -d \
  -p 8080:8080 -p 50000:50000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ./config:/root/.kube/config \
  -v jenkins_data:/var/jenkins_home \
  jenkins-with-tools



