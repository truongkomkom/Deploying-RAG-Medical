from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from langchain.agents import initialize_agent, AgentType
from tools import create_search_tool, create_rag_tool, llm, conversation_memory
from prompts import SYSTEM_PROMPT
from langchain_core.messages import SystemMessage

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider
from opentelemetry.trace.status import Status, StatusCode
from config import config 
import logging
import time

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------- Jaeger Tracing --------------------



jaeger_exporter = JaegerExporter(
    collector_endpoint=config["jaeger"]["collector_endpoint"]
)
trace_provider = TracerProvider(
    resource=Resource.create({
        SERVICE_NAME: "RAG-Query-from-user",
        "deployment.environment": "development"
    })
)
trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
set_tracer_provider(trace_provider)

tracer = trace.get_tracer(__name__)

# -------------------- FastAPI --------------------
app = FastAPI(
    title="RAG",
    docs_url="/rag/docs",
    redoc_url="/rag/redoc",
    openapi_url="/rag/openapi.json"
)

# -------------------- Request Model --------------------
class QueryRequest(BaseModel):
    question: str

# -------------------- Agent --------------------
# Add span around agent initialization
with tracer.start_as_current_span("initialize_agent"):
    agent = initialize_agent(
        tools=[create_rag_tool(), create_search_tool()],
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        memory=conversation_memory,
        agent_kwargs={
            "system_message": SystemMessage(content=SYSTEM_PROMPT),
        },
        handle_parsing_errors=True,
        max_iterations=5,
        timeout=100,
    )

# -------------------- Processing Function --------------------
def process_medical_query(user_query: str) -> str:
    with tracer.start_as_current_span("process_medical_query") as process_span:
        try:
            # Add request metadata to span
            process_span.set_attribute("query.original", user_query)
            process_span.set_attribute("query.length", len(user_query))
            start_time = time.time()
            
            # Đánh dấu và log cho mỗi truy vấn
            logger.info(f"Đang xử lý truy vấn y tế: {user_query}")

            with tracer.start_as_current_span("enhance_query") as enhance_span:
                enhanced_query = f"{user_query} (trả lời bằng Tiếng Việt)"
                enhance_span.set_attribute("query.enhanced", enhanced_query)
                logger.info(f"Truy vấn sau khi tăng cường: {enhanced_query}")
            
            with tracer.start_as_current_span("agent_invoke") as agent_span:
                agent_span.set_attribute("agent.type", "ZERO_SHOT_REACT_DESCRIPTION")
                agent_span.set_attribute("agent.max_iterations", 5)
                
                logger.info(f"Đang gọi agent với truy vấn: {enhanced_query}")
                
                with tracer.start_as_current_span("llm_processing"):
                    response = agent.invoke({"input": enhanced_query})
                
                # Track agent performance
                agent_span.set_attribute("agent.success", True if response else False)

            # Truy vấn thành công sẽ trả về kết quả từ agent
            with tracer.start_as_current_span("process_response") as response_span:
                output = response.get("output", "")
                response_span.set_attribute("response.length", len(output) if output else 0)
                response_span.set_attribute("response.empty", not bool(output))
                
                if output:
                    logger.info(f"Trả về kết quả từ agent: {output[:100]}...")  # Log only first 100 chars
                else:
                    logger.warning("Không có kết quả trả về từ agent.")
                    response_span.set_status(Status(StatusCode.ERROR))
                
            # Add overall processing stats
            process_span.set_attribute("processing.time_ms", int((time.time() - start_time) * 1000))
            return output if output else "Không có kết quả trả về từ hệ thống. Vui lòng thử lại."
            
        except Exception as e:
            # Log lỗi nếu có và track in span
            logger.exception("Lỗi xử lý truy vấn y tế")
            process_span.set_status(Status(StatusCode.ERROR))
            process_span.record_exception(e)
            return f"Đã xảy ra lỗi trong quá trình xử lý câu hỏi: {str(e)}"

# -------------------- Endpoints --------------------
@app.post("/ask")
async def ask_question(request: QueryRequest):
    with tracer.start_as_current_span("ask_question_endpoint") as endpoint_span:
        endpoint_span.set_attribute("http.method", "POST")
        endpoint_span.set_attribute("http.route", "/ask")
        
        # Add request information to span
        endpoint_span.set_attribute("request.question_length", len(request.question))
        
        start_time = time.time()
        result = process_medical_query(request.question)
        
        # Add response information to span
        endpoint_span.set_attribute("response.length", len(result))
        endpoint_span.set_attribute("processing.time_ms", int((time.time() - start_time) * 1000))
        
        return {"answer": result}

@app.get("/healthz")
def health_check():
    with tracer.start_as_current_span("health_check") as health_span:
        health_span.set_attribute("http.method", "GET")
        health_span.set_attribute("http.route", "/healthz")
        return JSONResponse(status_code=200, content={"status": "ok", "message": "Healthy"})

# Add middleware for tracing all requests
@app.middleware("http")
async def tracing_middleware(request, call_next):
    request_path = request.url.path
    request_method = request.method
    
    with tracer.start_as_current_span(f"{request_method} {request_path}") as request_span:
        request_span.set_attribute("http.method", request_method)
        request_span.set_attribute("http.url", str(request.url))
        request_span.set_attribute("http.path", request_path)
        
        start_time = time.time()
        response = await call_next(request)
        
        # Add response data
        request_span.set_attribute("http.status_code", response.status_code)
        request_span.set_attribute("http.response_time_ms", int((time.time() - start_time) * 1000))
        
        if response.status_code >= 400:
            request_span.set_status(Status(StatusCode.ERROR))
        
        return response

# -------------------- Run Uvicorn --------------------
if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)