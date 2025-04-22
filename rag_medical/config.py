config = {
    "llm": {
        "model_name": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "temperature": 0.5,
        "max_tokens": 1024,
        "streaming": True
    },
    "milvus": {
        "uri": "http://my-milvus.milvus.svc.cluster.local:19530",
        "collection_name": "test_demo_collection",
        "top_k": 3
    },
    "sentence_transformer": {
        "url": "http://emb-svc.emb.svc.cluster.local:81/vectorize"
    },
    "rag": {
        "weights": [0.8, 0.3]
    },
    "jaeger": {
        "collector_endpoint": "http://jaeger-all-in-one.jaeger-tracing.svc.cluster.local:14268/api/traces"
    }
}
