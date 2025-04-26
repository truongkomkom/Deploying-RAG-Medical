from minio import Minio
import fitz  # PyMuPDF
import io
import re
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient,  FieldSchema, CollectionSchema, DataType, Function, FunctionType
import uuid

class PDFProcessor:
    def __init__(self, chunk_size=1024, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", ", ", " ", ""],
            keep_separator=True
        )

    def preprocess_text(self, text):
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'^ +| +$', '', text, flags=re.MULTILINE)
        return text

    def extract_text_from_pdf(self, pdf_bytes):
        doc = fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf")
        return "".join([page.get_text() for page in doc])

    def split_text(self, text):
        cleaned = self.preprocess_text(text)
        return self.text_splitter.split_documents([Document(page_content=cleaned)])
class MilvusStorage:
    def __init__(self, collection_name, embedding_dim):
        self.client = MilvusClient(uri="http://localhost:19530")
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        self._init_collection()
        self._create_index()  # Tạo index sau khi insert
    def _init_collection(self):
        if self.client.has_collection(collection_name=self.collection_name):
            self.client.drop_collection(collection_name=self.collection_name)

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535, enable_analyzer=True),
            FieldSchema(name="sparse", dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name="dense", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
        ]
        schema = CollectionSchema(fields=fields, description="medical collection")
        # Define function to generate sparse vectors

        bm25_function = Function(
            name="text_bm25_emb",  # Function name
            input_field_names=["text"],  # Name of the VARCHAR field containing raw text data
            output_field_names=["sparse"],  # Name of the SPARSE_FLOAT_VECTOR field reserved to store generated embeddings
            function_type=FunctionType.BM25,
        )
        schema.add_function(bm25_function)
        self.client.create_collection(collection_name=self.collection_name, schema=schema)




    def insert_chunks(self, chunks):
        if chunks:
            self.client.insert(collection_name=self.collection_name, data=chunks)
            self.client.flush(collection_name=self.collection_name)

    def _create_index(self):
        try:
            # Create index params using the prepare_index_params method
            index_params = MilvusClient.prepare_index_params()

            # Add indexes
            index_params.add_index(
                field_name="dense",
                index_name="dense_index",
                index_type="IVF_FLAT",
                metric_type="IP",
                params={"nlist": 128},
            )

            index_params.add_index(
                field_name="sparse",
                index_name="sparse_index",
                index_type="SPARSE_INVERTED_INDEX",  # Index type for sparse vectors
                metric_type="BM25",  # Set to BM25 when using function to generate sparse vectors
                params={"inverted_index_algo": "DAAT_MAXSCORE"},
                # The ratio of small vector values to be dropped during indexing
            )

            # Create the index with the prepared params
            self.client.create_index(
                collection_name=self.collection_name,
                index_params=index_params,
                sync=True  # Wait for completion
            )
            print("✅ Index created successfully")
        except Exception as e:
            print(f"Error creating index: {e}")


class MinIOClient:
    def __init__(self, endpoint, access_key, secret_key, bucket_name):
        self.bucket_name = bucket_name
        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)

    def get_pdf_objects(self):
        return [obj for obj in self.client.list_objects(self.bucket_name, recursive=True) if obj.object_name.endswith(".pdf")]

    def get_pdf_bytes(self, object_name):
        return self.client.get_object(self.bucket_name, object_name).read()
class PDFEmbeddingPipeline:
    def __init__(self, embedding_model, pdf_processor, milvus_storage, minio_client):
        self.embedding_model = embedding_model
        self.processor = pdf_processor
        self.milvus = milvus_storage
        self.minio = minio_client

    def run(self):
        pdf_objects = self.minio.get_pdf_objects()
        for obj in pdf_objects:
            print(f"Đang xử lý: {obj.object_name}")
            pdf_bytes = self.minio.get_pdf_bytes(obj.object_name)
            text = self.processor.extract_text_from_pdf(pdf_bytes)
            chunks = self.processor.split_text(text)

            data = []
            for i, chunk in enumerate(chunks):
                content = chunk.page_content
                vector = self.embedding_model.encode(content, batch_size=1, show_progress_bar=False)
                data.append({
                    "id": str(uuid.uuid4()),
                    "dense": vector.tolist(),
                    "text": content,
                    "source": obj.object_name,
                })

            self.milvus.insert_chunks(data)
            print(f"✅ Đã insert {len(data)} chunks vào Milvus")
if __name__ == "__main__":
    # Load mô hình embedding
    model = SentenceTransformer("D:\LastDance\embedding\model")

    # Khởi tạo các thành phần
    processor = PDFProcessor(chunk_size=2000, chunk_overlap=50)
    storage = MilvusStorage(collection_name="test_demo_collection", embedding_dim=model.get_sentence_embedding_dimension())
    minio = MinIOClient(endpoint="localhost:9100", access_key="minioadmin", secret_key="minioadmin", bucket_name="crawled-data-medical")

    # Chạy pipeline
    pipeline = PDFEmbeddingPipeline(model, processor, storage, minio)
    pipeline.run()