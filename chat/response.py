import os
from .utils import *
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)
    
async def gpt_chat(prompt: str, chat_history = [], model_name="gpt-4.1-mini"):
    try:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        chat_history.append(system_instruction())
        chat_history.append({"role": "user", "content": prompt})

        response_tools = await client.chat.completions.create(
            model=model_name,
            messages=chat_history,
            n=1,
            stop=None,
            temperature=0.5,
            tools=assistant_tools,
            tool_choice="required",
            parallel_tool_calls=True
        )   

        response_tools = response_tools.choices[0].message
        calls = response_tools.tool_calls
        try:
            tool_messages = ToolExecutor().execute(calls)
        except Exception as e:
            print(e)
            yield "Xin lỗi có lỗi đang xảy ra, vui lòng thử lại sau"
            return

        chat_history.append(response_tools)
        if len(tool_messages) != 0:
            chat_history.extend(tool_messages)

        buffer = ""
        in_markdown_link = False
        async for chunk in await client.chat.completions.create(
            model=model_name,
            messages=chat_history,
            n=1,
            stop=None,
            temperature=0,
            stream=True
        ):
            content = chunk.choices[0].delta.content
            if content is None:
                continue

            if "[" in content:
                in_markdown_link = True
            if in_markdown_link: 
                buffer += content
                print(buffer)
                if ")" in buffer:
                    if buffer.count("(") == buffer.count(")"):
                        yield buffer
                        buffer = ""
                        in_markdown_link = False
            else:
                yield content
    except Exception as e:
        print(e)
        yield "Xin lỗi có lỗi đang xảy ra, vui lòng thử lại sau"

async def generate_chat_title(messages, model_name="gpt-4o-mini"):
    try:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = [
            {
                "role": "system", 
                "content": "Bạn là một trợ lý AI giúp tạo tiêu đề ngắn gọn cho đoạn hội thoại. "
                          "Hãy tạo một tiêu đề ngắn gọn (tối đa 15 ký tự) dựa trên nội dung của đoạn hội thoại. "
                          "Tiêu đề nên phản ánh chủ đề chính của cuộc trò chuyện."
            }
        ]
        
        # Thêm các tin nhắn từ lịch sử chat
        for msg in messages:
            prompt.append({"role": msg["role"], "content": msg["content"]})
            
        # Thêm yêu cầu cụ thể
        prompt.append({
            "role": "user",
            "content": "Hãy tạo một tiêu đề ngắn gọn cho đoạn hội thoại trên. Chỉ trả về tiêu đề, không thêm giải thích."
        })
        
        response = await client.chat.completions.create(
            model=model_name,
            messages=prompt,
            max_tokens=40,
            n=1,
            temperature=0.7
        )
        
        title = response.choices[0].message.content.strip()
        
        if title.startswith('"') and title.endswith('"'):
            title = title[1:-1]
            
        return title
    except Exception as e:
        print(f"Error generating chat title: {e}")
        return "Đoạn chat mới"
