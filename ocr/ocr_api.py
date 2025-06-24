from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import easyocr
import numpy as np
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализируем OCR
reader = easyocr.Reader(['ru', 'en'], verbose=False)

@app.post("/ocr")
async def extract_text(file: UploadFile = File(...)):
    try:
        # Читаем изображение
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image_np = np.array(image)
        
        # Распознаем текст
        results = reader.readtext(image_np)
        
        # Извлекаем только текст
        text_list = [text.strip('"\'') for (_, text, confidence) in results if confidence > 0.3]
        full_text = " ".join(text_list)
        
        return full_text
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)