
Step 1: 
helm repo add milvus https://milvus-io.github.io/milvus-helm/
helm repo update

Step 2: 
kubectl create namespace milvus  

Step 3:
helm install my-milvus milvus/milvus --namespace milvus -f ./milvus-values.yaml

or

helm install my-milvus milvus/milvus  --namespace milvus --create-namespace  --set etcd.persistence.size=1Gi  --set minio.persistence.size=10Gi  --set standalone.persistence.size=10Gi  --set minio.persistence.storageClass=standard-rwo  --set etcd.persistence.storageClass=standard-rwo  --set standalone.persistence.storageClass=standard-rwo --set cluster.enabled=false  --set pulsar.enabled=false  --set etcd.replicaCount=1  --set minio.mode=standalone  --set minio.persistence.storageClass=standard-rwo --set image.all.tag=v2.5.9

Step 4:
kubectl port-forward svc/my-milvus 19530:19530 -n milvus


                                                             