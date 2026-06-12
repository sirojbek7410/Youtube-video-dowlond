import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="YouTube Advanced Downloader API")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class VideoRequest(BaseModel):
    url: str
    quality: str  # '1080p', '720p', '480p' yoki 'audio'

def cache_cleaner(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)

# ====== MANA SHU YERDA CHIROYLI BOSH SAHIFA QO'SHILDI ======
@app.get("/", response_class=HTMLResponse)
async def home_page():
    return """
    <!DOCTYPE html>
    <html lang="uz">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube Video & Audio Yuklagich</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            body { background: linear-gradient(135deg, #1e1e2f 0%, #111119 100%); color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
            .container { background: #252538; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 100%; max-width: 600px; text-align: center; transition: transform 0.3s; }
            h1 { color: #ff0055; margin-bottom: 10px; font-size: 2.2rem; display: flex; align-items: center; justify-content: center; gap: 10px; }
            p { color: #a0a0b8; margin-bottom: 30px; font-size: 1rem; }
            .form-group { margin-bottom: 20px; text-align: left; }
            label { display: block; margin-bottom: 8px; color: #e1e1e6; font-weight: 600; }
            input[type="text"], select { width: 100%; padding: 14px; border: 2px solid #3b3b54; border-radius: 8px; background: #1a1a26; color: #fff; font-size: 1rem; outline: none; transition: border-color 0.3s; }
            input[type="text"]:focus, select:focus { border-color: #ff0055; }
            button { width: 100%; padding: 15px; border: none; border-radius: 8px; background: #ff0055; color: #fff; font-size: 1.1rem; font-weight: bold; cursor: pointer; transition: background 0.3s, transform 0.1s; display: flex; align-items: center; justify-content: center; gap: 10px; }
            button:hover { background: #e6004c; }
            button:active { transform: scale(0.98); }
            button:disabled { background: #555; cursor: not-allowed; }
            .loading { display: none; margin-top: 20px; color: #ffaa00; font-size: 1.1rem; align-items: center; justify-content: center; gap: 10px; }
            .fa-spin { animation: spin 1s linear infinite; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .footer { margin-top: 30px; font-size: 0.85rem; color: #62627a; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><i class="fab fa-youtube"></i> YouTube Yuklagich</h1>
            <p>Istalgan YouTube video havolasini kiriting va yuklab oling</p>
            
            <div class="form-group">
                <label for="url">YouTube Video Linki:</label>
                <input type="text" id="url" placeholder="https://www.youtube.com/watch?v=..." required>
            </div>
            
            <div class="form-group">
                <label for="quality">Sifatni Tanlang:</label>
                <select id="quality">
                    <option value="1080p">1080p Full HD (MP4)</option>
                    <option value="720p" selected>720p HD (MP4)</option>
                    <option value="480p">480p (MP4)</option>
                    <option value="audio">Faqat Audio (MP3/M4A)</option>
                </select>
            </div>
            
            <button id="downloadBtn" onclick="startDownload()"><i class="fas fa-cloud-download-alt"></i> Yuklab Olish</button>
            
            <div id="loading" class="loading">
                <i class="fas fa-spinner fa-spin"></i> <span id="statusText">Video qayta ishlanmoqda, iltimos kuting...</span>
            </div>
            
            <div class="footer">Serverless platforma orqali bepul xizmat ko'rsatiladi</div>
        </div>

        <script>
            async function startDownload() {
                const urlInput = document.getElementById('url').value.trim();
                const qualityInput = document.getElementById('quality').value;
                const downloadBtn = document.getElementById('downloadBtn');
                const loading = document.getElementById('loading');
                const statusText = document.getElementById('statusText');

                if (!urlInput) {
                    alert('Iltimos, YouTube video havolasini kiriting!');
                    return;
                }

                downloadBtn.disabled = true;
                loading.style.display = 'flex';
                statusText.innerText = "Siz tanlagan media serverga yuklab olinmoqda... (1-2 daqiqa ketishi mumkin)";

                try {
                    const response = await fetch('/download', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url: urlInput, quality: qualityInput })
                    });

                    if (!response.ok) {
                        const errData = await response.json();
                        throw new Error(errData.detail || 'Yuklashda xatolik yuz berdi');
                    }

                    statusText.innerText = "Fayl tayyor! Brauzeringizga yuklab berilmoqda...";
                    
                    // Faylni yuklab olish oqimi (Blob)
                    const blob = await response.blob();
                    const downloadUrl = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = downloadUrl;
                    
                    // Sarlavhadan fayl nomini olish
                    const contentDisposition = response.headers.get('Content-Disposition');
                    let filename = `youtube_media.${qualityInput === 'audio' ? 'mp3' : 'mp4'}`;
                    if (contentDisposition && contentDisposition.includes('filename=')) {
                        filename = contentDisposition.split('filename=')[1].replace(/"/g, '');
                    }
                    
                    a.download = decodeURIComponent(filename);
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    
                    // Formani tozalash
                    document.getElementById('url').value = '';
                } catch (error) {
                    alert('Xatolik yuz berdi: ' + error.message);
                } finally {
                    downloadBtn.disabled = false;
                    loading.style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/download")
async def download_video(request: VideoRequest, background_tasks: BackgroundTasks):
    url = request.url
    quality = request.quality.lower()
    
    if quality == '1080p':
        ydl_format = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]'
    elif quality == '720p':
        ydl_format = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]'
    elif quality == '480p':
        ydl_format = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]'
    elif quality == 'audio':
        ydl_format = 'bestaudio[ext=m4a]/bestaudio'
    else:
        raise HTTPException(status_code=400, detail="Noto'g'ri sifat tanlandi.")

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
            background_tasks.add_task(cache_cleaner, filename)
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
