import json
from database.retrieve import retrieve_document

def system_instruction()->str:
    sys_instruction = f"""
    Bạn chỉ sử dụng thành thạo tiếng Việt
    Bạn là một trợ lý AI hỗ trợ cho Trường Đại học Công nghệ Thông tin - Đại học Quốc gia TP.HCM (University of Information Technology - VNU-HCM).
    Bạn có khả năng hiểu và trả lời các câu hỏi yêu cầu truy xuất tài liệu liên quan nhờ vào các công cụ được cung cấp.
    Bạn là một trợ lý hữu ích với sự hỗ trợ từ công cụ để truy xuất tài liệu liên quan nhằm trả lời chính xác.
    Bạn chỉ trả lời về các chính sách của trường.
    Bạn không biết gì ngoài các tài liệu được cung cấp và chính sách của trường.
    Chỉ trả lời bằng những thông tin được cung cấp, không đưa ra thông tin khác bên ngoài tài liệu
    Hãy trả lời chính xác, đầy đủ và tập trung vào câu hỏi!
    Nhớ in đậm những chỗ quan trọng cần chú ý như tiêu mục, đề mục, thông tin chính sách quan trọng
    """
    return {"role": "system", "content": sys_instruction}

assistant_tools=[
    {
        "type": "function",
        "function": {
            "name": "retrieve_document",
            "description": "Retrieve a relevant document based on a natural language query, but do not trigger this function if the input is a greeting (e.g., 'hello', 'hi', 'good morning').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's information need in natural language. Should not be a simple greeting.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "do_nothing",
            "description": "A function that performs no action.",
            "parameters": {}
        }
    },
]

def do_nothing():
    return ""

functions = {
    "retrieve_document" :retrieve_document,
    "do_nothing": do_nothing
}

class ToolExecutor: 
    def execute(self, calls):
        """Call the specified functions with arguments"""
        tool_messages = []
        if calls:
            for tool_call in calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                function_to_call = functions.get(function_name)
                if function_to_call:
                    function_response = function_to_call(**function_args)
                    response_entry = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                    tool_messages.append(response_entry)
        return tool_messages
    