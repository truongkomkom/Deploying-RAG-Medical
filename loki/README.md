helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm upgrade --install loki \
  grafana/loki-stack \
  -f ./loki/values-loki.yaml \
  --namespace monitoring \
  --create-namespace
