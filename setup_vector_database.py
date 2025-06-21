import os
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from llama_index.core import Document
from llama_index.core.node_parser import TokenTextSplitter

from database.retrieve import file_exists
from database.weaviatedb import start_weaviate, create_new_collection, insert_data
from reader.reader import load_basic_data, data2text
from reader.scraper import WebScraper

PARSER = os.getenv("PARSER")

data_folder= "./data/documents/raw"
doc_folder= "./data/documents/text"
not_read= [".pdf", ".PDF", ".doc", ".DOC"]
collection_name= "chatbot"
url = "https://student.uit.edu.vn/qui-che-qui-dinh-qui-trinh"

def create_txt_splitter():
    splitter = TokenTextSplitter(chunk_size=1024, chunk_overlap=256)
    return splitter

def split_document(file_contents, collection):
    splitter = create_txt_splitter()

    splits = {
        doc['file_name']: {
            "splits": [node.text for node in splitter([Document(text=doc['content'])])]
        }
        for doc in tqdm(file_contents, desc="Splitting documents...", unit="doc")
        if file_exists(filename=doc['file_name'], collection=collection) == False
    }
    return splits

def formating_chunk(splitted_chunks):
    md_splits = []
    metas = []

    for filename, splitted_doc in splitted_chunks.items():
        for chunk in splitted_doc["splits"]:
            md_splits.append(chunk)

            metas.append({
                "filename": filename, 
            })

    return md_splits, metas

if __name__ == "__main__":    
    scraper = WebScraper(url, max_depth=2, markdown_dir=data_folder, files_dir=data_folder)
    scraper.run()

    data2text(
        api_key=PARSER,
        input_dir=data_folder,
        output_dir=doc_folder,
        not_read=not_read
    )

    data= load_basic_data(
        input_dir=doc_folder,
    )

    client = start_weaviate()
    collection= create_new_collection(client=client, collection_name=collection_name)

    splits = split_document(data, collection)

    md_splits, metas = formating_chunk(
        splitted_chunks=splits)


    insert_data(
        client=client,
        splits=md_splits, 
        metas=metas,
        collection_name=collection_name,
    )
    
    client.close()

    print("Data inserted successfully")
