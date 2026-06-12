import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YouTube Video Downloader API")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    url: str

def cache_cleaner(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

@app.post("/download")
async def download_video(request: VideoRequest, background_tasks: BackgroundTasks):
    url = request.url
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        if not os.path.exists(filename):
            filename = os.path.splitext(filename)[0] + ".mp4"

        if os.path.exists(filename):
            background_tasks.add_task(cache_cleaner, filename)
            return FileResponse(
                path=filename, 
                filename=f"{info.get('title', 'video')}.mp4", 
                media_type='video/mp4'
            )
        else:
            raise HTTPException(status_code=500, detail="Fayl yuklanmadi.")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Xatolik yuz berdi: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
