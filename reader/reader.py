import os
from collections import defaultdict
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

def data2text(
        api_key:str, 
        input_dir:str,
        output_dir:str,
        not_read= []
):
    os.makedirs(output_dir, exist_ok=True)

    all_files = os.listdir(input_dir)
    pdf_files = [os.path.join(input_dir, f) for f in all_files if f.lower().endswith('.pdf')]
    extensions = set(os.path.splitext(f)[1].lower() for f in all_files)
    extensions= [extension for extension in extensions if extension not in not_read]

    existing_txt_files = {
        os.path.splitext(f)[0] for f in os.listdir(output_dir) if f.endswith(".txt")
    }
    
    print("Converting data to text...")
    try:
        reader = SimpleDirectoryReader(
            input_dir=input_dir,
            required_exts=extensions
        )
        documents = reader.load_data(show_progress=True)
        merged_documents = defaultdict(str)
        for doc in documents:
            file_name = doc.metadata["file_name"]
            if file_name in existing_txt_files:
                print(f"File {file_name} already processed, skipping...")
                continue
            merged_documents[file_name] += doc.text + "\n"
        for file_name, content in merged_documents.items():
            txt_file_name = file_name + ".txt"
            txt_file_path = os.path.join(output_dir, txt_file_name)
            with open(txt_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved txt file: {txt_file_name}")
    except Exception as e:
        print(f"Lỗi khi đọc thư mục: {e}")

        
    parser = LlamaParse(
        result_type="text", 
        api_key=api_key,
        language="vi",
        split_by_page=False,
    )
    file_extractor = {".pdf": parser}
    for pdf_path in pdf_files:
        file_name= os.path.basename(pdf_path)
        if file_name in existing_txt_files:
            print(f"File {file_name} already processed, skipping...")
            continue
        documents = SimpleDirectoryReader(input_files=[pdf_path], file_extractor=file_extractor).load_data()
        for doc in documents:
            file_name = doc.metadata["file_name"]
            txt_file_name = file_name + ".txt"
            txt_file_path = os.path.join(output_dir, txt_file_name)
            with open(txt_file_path, "w", encoding="utf-8") as f:
                f.write(doc.text)
            print(f"Saved txt file: {txt_file_name}")

def load_basic_data(input_dir:str): 
    reader = SimpleDirectoryReader(
        input_dir=input_dir
    )

    documents = reader.load_data(show_progress=True)
    merged_documents = defaultdict(str)
    for doc in documents:
        file_name = os.path.splitext(doc.metadata["file_name"])[0]
        merged_documents[file_name] += doc.text + "\n"

    final_documents = []
    for file_name, content in merged_documents.items():
        final_documents.append({"file_name": file_name, "content": content}) 

    return final_documents
