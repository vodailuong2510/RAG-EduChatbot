import os
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import weaviate
import weaviate.classes.config as wc
from weaviate.classes.init import Auth
from weaviate.collections.classes.filters import Filter
from sentence_transformers import SentenceTransformer

def start_weaviate():
    # client = weaviate.connect_to_weaviate_cloud(
    #     cluster_url=os.getenv("WEAVIATE_URL"),
    #     auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY"))
    # )
    client = weaviate.connect_to_local()

    print("Client is ready:", client.is_ready())

    return client

def create_new_collection(client, collection_name):
    try:
        collection= client.collections.get(collection_name)
        print(collection)
        print("Collection already exists")
        return collection
    except weaviate.exceptions.UnexpectedStatusCodeException:
        print("Creating new collection")
        client.collections.create(
            name=collection_name,
            description="A collection of documents",
            properties=[
                wc.Property(name="filename", data_type=wc.DataType.TEXT),
                wc.Property(name="content", data_type=wc.DataType.TEXT),
            ],
        )
        print("Collection created")
        collection= client.collections.get(collection_name)
        return collection

def insert_data(client, splits, metas, collection_name):
    embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")

    with client.batch.dynamic() as batch:
        for md_text, meta in tqdm(zip(splits, metas), desc="Inserting into Weaviate", unit="doc"):
            vector = embedding_model.encode(md_text).tolist() 

            batch.add_object(
                collection= collection_name,
                properties= {
                    "filename": meta["filename"],
                    "content": md_text,  
                },
                vector=vector, 
            )

def delete_by_filename(client, collection_name, filename):
    collection = client.collections.get(collection_name)
    
    filter_obj = Filter.by_property("filename").equal(filename)
    
    result = collection.query.fetch_objects(
        filters=filter_obj
    )
    
    deleted_count = 0
    for obj in result.objects:
        collection.data.delete_by_id(obj.uuid)
        deleted_count += 1
        
    return deleted_count

if __name__ == "__main__":
    client= start_weaviate()
    # print(client.collections.list_all())
    print(client.collections.delete("multilingual_e5_large"))
    client.close()