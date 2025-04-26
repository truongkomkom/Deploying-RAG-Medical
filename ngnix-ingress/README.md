Step 1:

helm install nginx-ingress ingress-nginx/ingress-nginx  --namespace ingress-nginx  --create-namespace
helm repo update

Step 2:
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

--34.69.203.236