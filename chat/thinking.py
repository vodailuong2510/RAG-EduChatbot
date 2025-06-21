import re
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "Minh64/Qwen3-preferenced-data",
    max_seq_length = 2048,
    dtype = None,
    load_in_4bit = True,
)

FastLanguageModel.for_inference(model) # Enable native 2x faster inference

def gen(inp: str):
    messages = [
        {"role" : "user", "content" : inp}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize = False,
        add_generation_prompt = True, # Must add for generation
        enable_thinking = False, # Disable thinking
    )

    outputs = model.generate(
        **tokenizer(text, return_tensors = "pt").to("cuda"), 
        max_new_tokens = 2048, 
        temperature = 0.7, top_p = 0.8, top_k = 20,
        # temperature = 0.01, top_p = 1.0, top_k = 0,
        use_cache = True
    )
    
    return tokenizer.batch_decode(outputs)

def take_answer(s):
    if isinstance(s, list):
        s = s[0]  # or join if it's multiline
    pattern = r'<think>\s*</think>\s*([\s\S]*?)<\|im_end\|>'
    m = re.search(pattern, s)
    if m:
        return m.group(1)
    else:
        return None
    
query = "Trường hợp nào giảng viên buộc phải đổi lịch buổi dạy bù?"
query += "\n"
print(f"Question: {query}")

for i in range (5):
    print(f"Step {i}")

    subquery = take_answer(gen(query))

    if "Final answer: " in subquery:
        print(subquery)
        break
    else:
    
        retrieve_query, flag = subquery.split('\n')[:2]
        query += retrieve_query

        print(f"{retrieve_query}\n{flag}\n")
        
        if "Intermediate answer" in flag:
            query += "\nIntermediate answer: "
        elif "retrieve the documents" in flag:
            _, _, ret = retrieve_query.partition("Follow up: ")
            context = retrieve_document(ret)
            query += "\nLet's retrieve the documents.\n"
            query += "Context: " + context + "\n"
        else:
            print(f"THIS IS THE FLAG: \n{flag}")
    
        ans = take_answer(gen(query))
    
        if "Final answer: " in ans:
            print(ans)
            break
        else:
            print(f"- {ans}")
        
        query += ans