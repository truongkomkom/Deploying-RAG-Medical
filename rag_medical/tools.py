from langchain_community.tools.tavily_search.tool import TavilySearchResults
from langchain.agents import Tool, initialize_agent, AgentType
from hybrid_search import hybrid_search
from dotenv import load_dotenv
from helper import format_results
from langchain_together.chat_models import ChatTogether
from prompts import *
from langchain_core.messages import SystemMessage
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from config import config
from pymilvus import MilvusClient


load_dotenv()



# Khởi tạo mô hình ngôn ngữ với các tham số từ cấu hình
llm = ChatTogether(
    model=config["llm"]["model_name"],
    temperature=config["llm"]["temperature"],
    max_tokens=config["llm"]["max_tokens"],
    streaming=config["llm"]["streaming"]
)

# Khởi tạo Milvus client
client = MilvusClient(uri=config["milvus"]["uri"])


collection_name = config["milvus"]["collection_name"]
weights = tuple(config["rag"]["weights"])
top_k = config["milvus"]["top_k"]
conversation_memory = ConversationBufferMemory(memory_key="conversation", k=5)
# Cải thiện hàm search_knowledge_base để đảm bảo trả về tiếng Việt
def search_knowledge_base(question: str):
    try:
        # Thực hiện hybrid search
        context = hybrid_search(client, collection_name, question, weights, top_k)
        
        # Format kết quả
        formatted_context = format_results(context)

        # Nếu không tìm thấy gì, trả kết quả này để agent cân nhắc công cụ khác
        if not formatted_context.strip() or "Không tìm thấy dữ liệu" in formatted_context:
            return "Không tìm thấy dữ liệu liên quan trong cơ sở dữ liệu nội bộ."

        # Tạo prompt và gọi LLM nếu có kết quả
        prompt_template = PromptTemplate(
            input_variables=["formatted_context", "question"],
            template=RAG_PROMPT
        )
        prompt = prompt_template.format(
            formatted_context=formatted_context,
            question=question
        )

        print(f"Prompt gửi tới LLM: {prompt}")  # Debug

        response = llm.invoke(prompt)

        # Kiểm tra xem phản hồi từ LLM có hợp lệ không
        if not response or not hasattr(response, 'content'):
            raise ValueError("Phản hồi từ LLM không hợp lệ.")

        return response.content

    except Exception as e:
        return f"Đã xảy ra lỗi khi tìm kiếm thông tin y khoa: {str(e)}. Vui lòng thử lại."

# Tạo công cụ RAG
def create_rag_tool():
    return Tool(
        name="RAGTool",
        func=search_knowledge_base,
        description=(
            "Dùng công cụ này để tìm kiếm thông tin từ cơ sở dữ liệu y khoa nội bộ bằng tiếng Việt. "
            "Công cụ này giúp truy xuất thông tin về bệnh lý, chẩn đoán, điều trị, và hướng dẫn y khoa "
            "có trong hệ thống. Đây nên là công cụ đầu tiên được sử dụng với bất kỳ câu hỏi y khoa nào."
        )
    )

# Tạo công cụ tìm kiếm web

def create_search_tool():
    """Khởi tạo công cụ tìm kiếm web với Tavily, giới hạn kết quả trả về"""
    search = TavilySearchResults(max_results=2, k=2)
    
    return Tool(
        name="WebSearchTool",  # Đổi tên thành một chuỗi đơn giản
        func=search.run,
        description=(
            "Dùng công cụ này để tìm kiếm thông tin y khoa thời gian thực trên internet "
            "khi dữ liệu nội bộ không đủ hoặc không có. Phù hợp với các câu hỏi về cập nhật mới, "
            "khuyến cáo hiện hành, tài liệu chuyên sâu chưa có trong hệ thống."
        )
    )

# Hàm xử lý đầu vào
def process_medical_query(user_query):
    try:
        # Thêm yêu cầu tiếng Việt vào câu hỏi
        enhanced_query = f"{user_query} (trả lời bằng tiếng Việt)"
        
        # Khởi tạo agent với các tham số linh hoạt và thêm memory vào
        agent = initialize_agent(
            tools=[create_rag_tool(), create_search_tool()],
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True,
            memory=conversation_memory,  # Thêm bộ nhớ vào agent
            agent_kwargs={
                "system_message": SystemMessage(content=SYSTEM_PROMPT),
            },
            handle_parsing_errors=True,
            max_iterations=5,  # Tăng số lần lặp tối đa
            timeout=100,  # Tăng thời gian timeout (s)
        )

        # Chạy agent
        response = agent.invoke({
            "input": enhanced_query
        })

        # Kiểm tra kết quả đầu ra
        output = response.get("output", "")
        if not output:
            return "Không có kết quả trả về từ hệ thống. Vui lòng thử lại."

        return output
    except Exception as e:
        return f"Đã xảy ra lỗi trong quá trình xử lý câu hỏi: {str(e)}"

# Ví dụ sử dụng
if __name__ == "__main__":
    question = "Ước tính từ 1 đến 5% số lần đặt Combitube vào khí quản; trong những trường hợp này, nếu phát hiện sai vị trí, ống thông có thể được sử dụng để đặt ống nội khí quản. Có thể có ít nhất 10% trường hợp chọc vào được thực hiện bằng ống thanh quản King mới vào khí quản; thông khí có thể thông qua ống thông xa trong những trường hợp này. Các ống King cũ được đặt cạnh để hầu như tất cả các ống dẫn vào thực quản."


    answer = process_medical_query(question)
    print(answer)
