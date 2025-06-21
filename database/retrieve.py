from .weaviatedb import start_weaviate
from sentence_transformers import SentenceTransformer
from weaviate.collections.classes.filters import Filter

def retrieve_document(query: str=""):
    client = start_weaviate()
    collection = client.collections.get("chatbot")

    embedding_model = SentenceTransformer("intfloat/multilingual-e5-large")
    query_vector = embedding_model.encode(query).tolist()

    result = collection.query.hybrid(
        query=query,
        vector=query_vector,
        limit=10,
        alpha=0.7,
    )
    
    context= []
    for o in result.objects:
        context.append(f"filename: {o.properties['filename']}\ncontent:\n{o.properties['content']}")

    client.close()
    
    return "\n\n".join(context)

def file_exists(filename:str, collection):
    try:
        filters = Filter.by_property("filename").equal(filename)
        
        result= collection.query.fetch_objects(
            filters=filters,
            return_properties=["filename"],
            limit=1
        )

        if len(result.objects) > 0:
            print(f"File {filename} exists in Weaviate, skipping upload.")
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking file {filename} in Weaviate: {e}")
        return False

if __name__ == "__main__":
    client = start_weaviate()
    collection = client.collections.get("chatbot")
    print(file_exists("01_2017_qd-ttg_ban_hanh_danh_muc_gddt_cua_he_thong_giao_duc_quoc_dan.pdf.txt", collection))
    client.close()