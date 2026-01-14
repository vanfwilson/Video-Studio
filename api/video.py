from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.services.captions import generate_captions
from app.tasks.background import process_video_file

router = APIRouter()

@router.post("/upload")
async def upload_video(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    # Save locally or pass to FileManager, then queue processing
    background_tasks.add_task(process_video_file, file.filename)
    return {"message": f"{file.filename} received and processing started"}
