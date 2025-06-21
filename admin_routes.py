import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime
from auth_routes import get_current_user
from math import ceil
from database.weaviatedb import start_weaviate, delete_by_filename
from reader.scraper import WebScraper
from reader.reader import data2text, load_basic_data
from setup_vector_database import split_document, formating_chunk, create_new_collection, insert_data
from pydantic import BaseModel
import shutil

admin = APIRouter()
COLLECTION_NAME = "chatbot"

class DocumentURL(BaseModel):
    url: str | None = None

@admin.post("/admin/documents")
async def add_document(
    url: str = Form(None),
    file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    if not url and not file:
        return JSONResponse(
            content={"error": "Vui lòng cung cấp URL hoặc tải lên file"},
            status_code=400
        )
    
    try:
        base_path = r"..\data\documents"
        raw_path = os.path.join(base_path, "raw")
        text_path = os.path.join(base_path, "text")
        
        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(text_path, exist_ok=True)

        downloaded_files = []
        
        if url:
            scraper = WebScraper(
                url=url,
                max_depth=2,
                markdown_dir=raw_path,
                files_dir=raw_path
            )
            scraper.run()
        
        if file:
            filename = file.filename
            file_path = os.path.join(raw_path, filename)
            
            if not os.path.exists(file_path):
                async with aiofiles.open(file_path, 'wb') as out_file:
                    content = await file.read() 
                    await out_file.write(content)
                
        
        data2text(
            api_key=os.getenv("PARSER"),
            input_dir=raw_path,
            output_dir=text_path,
            not_read=[".doc", ".DOC"]
        )

        data = load_basic_data(input_dir=text_path)
        
        if data:
            client = start_weaviate()
            collection = create_new_collection(client=client, collection_name=COLLECTION_NAME)

            splits = split_document(data, collection)
            md_splits, metas = formating_chunk(splits)

            insert_data(
                client=client,
                splits=md_splits,
                metas=metas,
                collection_name=COLLECTION_NAME,
            )
            
            client.close()
        
        return JSONResponse(content={
            "message": "Tài liệu đã được tải, chuyển đổi và lưu vào cơ sở dữ liệu thành công",
            "files": downloaded_files
        })
        
    except Exception as e:
        return JSONResponse(
            content={"error": f"Lỗi khi xử lý tài liệu: {str(e)}"},
            status_code=500
        )

@admin.get("/admin/documents")
async def get_documents(
    current_user: dict = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1),
    search: str = Query(default="")
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
        
    raw_docs_path = r"..\data\documents\raw"
    documents = []
    
    if os.path.exists(raw_docs_path):
        for filename in os.listdir(raw_docs_path):
            if search and search.lower() not in filename.lower():
                continue
                
            file_path = os.path.join(raw_docs_path, filename)
            if os.path.isfile(file_path):
                creation_time = os.path.getctime(file_path)
                creation_date = datetime.fromtimestamp(creation_time)
                
                weekdays = ['thứ hai', 'thứ ba', 'thứ tư', 'thứ năm', 'thứ sáu', 'thứ bảy', 'chủ nhật']
                weekday = weekdays[creation_date.weekday()]
                formatted_date = f"{weekday}, {creation_date.day} tháng {creation_date.month} năm {creation_date.year} {creation_date.strftime('%H:%M')}"
                
                documents.append({
                    'filename': filename,
                    'created_at': formatted_date,
                    'timestamp': creation_time
                })
    
    documents.sort(key=lambda x: x['timestamp'], reverse=True)
    
    total_documents = len(documents)
    total_pages = ceil(total_documents / per_page)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    current_page_documents = documents[start_idx:end_idx]
    
    for doc in current_page_documents:
        doc.pop('timestamp', None)
    
    return JSONResponse(content={
        "documents": current_page_documents,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_documents": total_documents,
            "per_page": per_page
        }
    })

@admin.delete("/admin/documents/{filename}")
async def delete_document(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    base_path = r"..\data\documents"
    raw_docs_path = os.path.join(base_path, "raw")
    text_docs_path = os.path.join(base_path, "text")
    
    raw_file_path = os.path.join(raw_docs_path, filename)
    
    file_deleted = False
    if os.path.exists(raw_file_path):
        try:
            os.remove(raw_file_path)
            file_deleted = True
        except Exception as e:
            return JSONResponse(
                content={"error": f"Failed to delete file from raw folder: {str(e)}"}, 
                status_code=500
            )
    
    text_deleted = False
    if os.path.exists(text_docs_path):
        filename_no_ext = os.path.splitext(filename)[0]
        
        for text_file in os.listdir(text_docs_path):
            if text_file.startswith(filename_no_ext):
                text_file_path = os.path.join(text_docs_path, text_file)
                try:
                    os.remove(text_file_path)
                    text_deleted = True
                except Exception as e:
                    return JSONResponse(
                        content={
                            "warning": "File was deleted from raw folder but failed to delete from text folder",
                            "error": str(e)
                        },
                        status_code=500
                    )
    
    try:
        client = start_weaviate()
        deleted_count = delete_by_filename(client, COLLECTION_NAME, filename)
        client.close()
    except Exception as e:
        message = []
        if file_deleted:
            message.append("File was deleted from raw folder")
        if text_deleted:
            message.append("and text folder")
        if message:
            message.append("but failed to delete from Weaviate")
            return JSONResponse(
                content={
                    "warning": " ".join(message),
                    "error": str(e)
                },
                status_code=500
            )
        return JSONResponse(
            content={"error": f"Failed to delete from Weaviate: {str(e)}"}, 
            status_code=500
        )
    
    message = ["Successfully deleted file from raw folder"]
    if text_deleted:
        message.append("and text folder")
    message.append(f"and {deleted_count} related documents from Weaviate")
    
    return JSONResponse(content={
        "message": " ".join(message)
    })

@admin.get("/admin/documents/{filename}/download")
async def download_document(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    raw_docs_path = os.path.join(r"..\data\documents\raw", filename)
    
    if not os.path.exists(raw_docs_path):
        return JSONResponse(
            content={"error": "File không tồn tại"},
            status_code=404
        )
    
    return FileResponse(
        raw_docs_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@admin.get("/admin/documents/{filename}/view")
async def view_document(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    if not current_user:
        return JSONResponse(content={"error": "Unauthorized"}, status_code=401)
    
    raw_docs_path = os.path.join(r"..\data\documents\raw", filename)
    text_docs_path = os.path.join(r"..\data\documents\text", os.path.splitext(filename)[0] + ".txt")
    
    if not os.path.exists(raw_docs_path):
        return JSONResponse(
            content={"error": "File không tồn tại"},
            status_code=404
        )

    if filename.lower().endswith('.txt') or os.path.exists(text_docs_path):
        try:
            file_path = text_docs_path if os.path.exists(text_docs_path) else raw_docs_path
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return JSONResponse(content={
                "content": content,
                "filename": filename
            })
        except Exception as e:
            return JSONResponse(
                content={"error": f"Không thể đọc file: {str(e)}"},
                status_code=500
            )
    
    return JSONResponse(content={
        "download_url": f"/admin/documents/{filename}/download",
        "filename": filename
    }) 