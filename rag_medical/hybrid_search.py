from pymilvus import AnnSearchRequest, WeightedRanker
import httpx
from pymilvus import MilvusClient
from config import config
# Hàm lấy vector từ API
def get_dense_vector(text):
    try:
        # Gửi yêu cầu POST tới API vectorize
        response = httpx.post(
            config["sentence_transformer"]["url"],  # URL của API vectorize
            json={"text": text},  # Dữ liệu gửi đi là text
            timeout=10.0  # Thời gian timeout nếu API không phản hồi
        )
        response.raise_for_status()  # Kiểm tra nếu có lỗi trong phản hồi
        return response.json()["vector"]  # Trả về vector dưới dạng danh sách
    except Exception as e:
        raise RuntimeError(f"Lỗi khi gọi embedding API: {e}")


# Hàm tạo yêu cầu tìm kiếm dạng dense
def build_dense_search_request(vector, limit=2):
    return AnnSearchRequest(
        data=[vector],
        anns_field="dense",
        param={
            "metric_type": "IP",
            "params": {"nprobe": 10}
        },
        limit=limit
    )


# Hàm tạo yêu cầu tìm kiếm dạng sparse
def build_sparse_search_request(text, limit=2):
    return AnnSearchRequest(
        data=[text],
        anns_field="sparse",
        param={"metric_type": "BM25"},
        limit=limit
    )


# Hàm tìm kiếm kết hợp (hybrid search)
def hybrid_search(client, collection_name, query_text, weights=(0.8, 0.3), top_k=2):
    # Lấy vector từ API
    dense_vector = get_dense_vector(query_text)
    
    # Tạo yêu cầu tìm kiếm dạng dense và sparse
    dense_req = build_dense_search_request(dense_vector, limit=top_k)
    sparse_req = build_sparse_search_request(query_text, limit=top_k)
    
    # Xử lý kết quả với WeightedRanker
    ranker = WeightedRanker(*weights)
    
    # Thực hiện tìm kiếm kết hợp
    results = client.hybrid_search(
        collection_name=collection_name,
        reqs=[dense_req, sparse_req],
        ranker=ranker,
        limit=top_k,
        output_fields=["text", "source"]
    )
    return results


# Ví dụ sử dụng hybrid_search
if __name__ == "__main__":
    # Giả sử bạn có một client Milvus đã được kết nối và collection_name
    client = MilvusClient(uri=config["milvus"]["uri"])
 # Cần thay bằng client Milvus thực tế đã được cấu hình
    collection_name = "test_demo_collection"  # Tên collection của bạn
    query_text = "Đối với nhịp nhanh co thắt"
    
    # Chạy hàm tìm kiếm kết hợp
    results = hybrid_search(client, collection_name, query_text, weights=(0.8, 0.3), top_k=2)
    
    # In kết quả trả về
    print(results)
