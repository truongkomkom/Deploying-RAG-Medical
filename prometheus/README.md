helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install prometheus-grafana-stack \
  prometheus-community/kube-prometheus-stack \
  -f values-prometheus.yaml \
  --namespace monitoring \
  --create-namespace


Get password and username
kubectl --namespace monitoring get secret prometheus-grafana-stack -o json
"admin-password": "MjMxMDIwMDM=", 23102003
"admin-user": "YWRtaW4=",