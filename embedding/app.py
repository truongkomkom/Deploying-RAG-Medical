from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import uvicorn

app = FastAPI()

# Load the model once when the app starts
model = SentenceTransformer("./model")


model.max_seq_length = 2048  # Increased from default to handle longer texts

class TextRequest(BaseModel):
    text: str


class CompareRequest(BaseModel):
    query: str
    documents: list[str]

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.post("/vectorize")
async def vectorize(request: TextRequest):
    # Generate embedding for a single text
    vector = model.encode(request.text)
    return {"vector": vector.tolist()}



if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)