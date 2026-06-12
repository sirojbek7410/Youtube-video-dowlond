import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YouTube Advanced Downloader API")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Foydalanuvchi yuborishi kerak bo'lgan ma'lumotlar strukturasi
class VideoRequest(BaseModel):
    url: str
    quality: str  # '1080p', '720p', '480p' yoki 'audio' bo'lishi kerak

def cache_cleaner(file_path: str):
    """Server xotirasi to'lib ketmasligi uchun faylni o'chirish"""
    if os.path.exists(file_path):
        os.remove(file_path)

@app.post("/download")
async def download_video(request: VideoRequest, background_tasks: BackgroundTasks):
    url = request.url
    quality = request.quality.lower()
    
    # Sifatga qarab yt-dlp format qoidalarini belgilaymiz
    if quality == '1080p':
        ydl_format = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
    elif quality == '720p':
        ydl_format = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
    elif quality == '480p':
        ydl_format = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]'
    elif quality == 'audio':
        # Faqat audio yuklash (eng sifatli audio va uni m4a yoki mp3 qilib berish)
        ydl_format = 'bestaudio[ext=m4a]/bestaudio'
    else:
        raise HTTPException(status_code=400, detail="Noto'g'ri sifat tanlandi. '1080p', '720p', '480p' yoki 'audio' yuboring.")

    ydl_opts = {
        'format': ydl_format,
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'noplaylist': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        if os.path.exists(filename):
            # Faylni foydalanuvchi olgach, o'chirishga qo'yamiz
            background_tasks.add_task(cache_cleaner, filename)
            
            # Fayl nomini aniqlash va mos formatda qaytarish
            ext = 'mp3' if quality == 'audio' else 'mp4'
            content_type = 'audio/mpeg' if quality == 'audio' else 'video/mp4'
            
            return FileResponse(
                path=filename, 
                filename=f"{info.get('title', 'media')}.{ext}", 
                media_type=content_type
            )
        else:
            raise HTTPException(status_code=500, detail="Fayl yuklashda xatolik.")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Xatolik: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
