from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId

def get_mongo_collection(Mongo_Key):
    if not Mongo_Key:
        raise ValueError("MongoDB URI is not provided")
        
    client = MongoClient(Mongo_Key)
    db = client["ceduit-chat"] 

    google_users = db["google_users"]
    facebook_users = db["facebook_users"]
    github_users = db["github_users"]
    messages_collection = db["messages"]
    chats_collection = db["chats"]

    return {
        "google_users": google_users,
        "facebook_users": facebook_users,
        "github_users": github_users,
        "messages": messages_collection,
        "chats": chats_collection
    }

def generate_user_id(user_data: dict) -> str:
    return f"{user_data['id']}-{user_data['name']}-{user_data['email']}"

def get_user_data(collections, provider: str, user_id:str):
    collection = collections.get(f"{provider}_users")
    if collection is None:
        raise ValueError(f"Invalid provider: {provider}")
    
    return collection.find_one({"user_id": user_id})

def create_new_user(collections, user_data: dict):
    user_id = generate_user_id(user_data)
    collection = collections.get(f"{user_data['provider']}_users")
    if collection is None:
        raise ValueError(f"Invalid provider: {user_data['provider']}")
    
    existing_user = collection.find_one({"user_id": user_id})
    if existing_user:
        return existing_user
    
    user_doc = {
        "user_id": user_id,
        "name": user_data["name"],
        "email": user_data["email"],
        "avatar": user_data.get("avatar"),
        "provider": user_data["provider"],
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    collection.insert_one(user_doc)
    return user_doc

def create_new_chat(collections, user_data: dict, title: str = None):
    user_id = generate_user_id(user_data)
    user_doc = get_user_data(collections, user_data["provider"], user_id)
    if not user_doc:
        raise ValueError("User not found")
    
    chat = {
        "user_id": user_id,
        "title": title or f"New Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    result = collections["chats"].insert_one(chat)
    return str(result.inserted_id)

def update_chat_title(collections, user_data: dict, chat_id: str, title: str):
    user_id = generate_user_id(user_data)
    user_doc = get_user_data(collections, user_data["provider"], user_id)
    if not user_doc:
        raise ValueError("User not found")
    
    result = collections["chats"].update_one(
        {"_id": ObjectId(chat_id), "user_id": user_id},
        {"$set": {"title": title, "updated_at": datetime.now()}}
    )
    
    return result.modified_count

def get_user_chats(collections, user_data: dict):
    user_id = generate_user_id(user_data)
    user_doc = get_user_data(collections, user_data["provider"], user_id)
    if not user_doc:
        raise ValueError("User not found")
    
    chats = collections["chats"].find({
        "user_id": user_id
    }).sort("updated_at", -1)
    
    return [{"chat_id": str(chat["_id"]), "title": chat["title"], "updated_at": chat["updated_at"].isoformat()} for chat in chats]

def save_message(collections, user_data: dict, chat_id: str, sender: str, content: str):
    user_id = generate_user_id(user_data)
    user_doc = get_user_data(collections, user_data["provider"], user_id)
    if not user_doc:
        raise ValueError("User not found")
    
    message = {
        "chat_id": chat_id,
        "user_id": user_id,
        "sender": sender,
        "content": content,
        "timestamp": datetime.now()
    }
    collections["messages"].insert_one(message)
    
    collections["chats"].update_one(
        {"_id": ObjectId(chat_id)},
        {"$set": {"updated_at": datetime.now()}}
    )

def get_messages(collections, user_data: dict, chat_id: str, limit: int = 10):
    user_id = generate_user_id(user_data)
    user_doc = get_user_data(collections, user_data["provider"], user_id)
    if not user_doc:
        raise ValueError("User not found")
    
    messages = collections["messages"].find({
        "chat_id": chat_id,
        "user_id": user_id
    }).sort("timestamp", -1).limit(limit)

    return [{"role": "user" if msg["sender"] == "user" else "assistant", "content": msg["content"]} for msg in messages]

def delete_chat(collections, user_data: dict, chat_id: str):
    user_id = generate_user_id(user_data)
    user_doc = get_user_data(collections, user_data["provider"], user_id)
    if not user_doc:
        raise ValueError("User not found")
    
    collections["messages"].delete_many({
        "chat_id": chat_id,
        "user_id": user_id
    })
    
    result = collections["chats"].delete_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })
    
    return result.deleted_count

def get_chat_by_id(collections, user_data: dict, chat_id: str):
    user_id = generate_user_id(user_data)
    user_doc = get_user_data(collections, user_data["provider"], user_id)
    if not user_doc:
        raise ValueError("User not found")
    
    chat = collections["chats"].find_one({
        "_id": ObjectId(chat_id),
        "user_id": user_id
    })
    
    if chat:
        chat["_id"] = str(chat["_id"])
        
    return chat

