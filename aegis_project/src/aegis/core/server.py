# ==========================================================================
# SERVER.PY — СЕТЕВОЙ СЕРВЕР ОБРАБОТКИ ГОЛОСОВОГО И РУЧНОГО ВВОДА ЗВОНКА
# ==========================================================================

from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="A.E.G.I.S. Voice Hub")

# Разрешаем Electron общаться с сервером без блокировок CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextQuery(BaseModel):
    text: str
    chat_id: str = None

@app.get("/api/voice/greeting")
async def get_dynamic_greeting(chat_id: str = None):
    """
    Генерирует живое динамическое приветствие ИИ при старте звонка
    """
    if chat_id:
        return {"text": "Привет! Контекст нашей переписки поднят. Готова продолжить обсуждение голосом."}
    return {"text": "Привет! Я на связи и готова к работе. О чём поговорим сегодня?"}

@app.post("/api/voice/process_text")
async def process_manual_voice_input(query: TextQuery):
    """
    Принимает ручной ввод текста прямо из панели внутри звонка
    """
    user_text = query.text
    # Здесь запрос уходит в оркестратор оркестратора (orchestrator.py -> Ollama)
    agent_answer = f"Я зафиксировала ваш ручной запрос: '{user_text}'. Шаг обработан в песочнице."
    
    return {
        "user_text": user_text,
        "agent_answer": agent_answer,
        "audio_url": "/api/voice/tts_stream" # Ссылка на озвучку от бэкенда
    }

@app.post("/api/voice/upload_audio")
async def process_microphone_stream(file: UploadFile = File(...)):
    """
    Принимает сырой аудиофайл с микрофона Electron, распознает его и дает ответ
    """
    audio_bytes = await file.read()
    
    # В будущем тут будет вызов: text = await speech_to_text.transcribe_audio_stream(audio_bytes)
    recognized_text = "Тестовая фраза пользователя" 
    agent_answer = "Ответ ИИ-агента на вашу голосовую реплику."

    return {
        "recognized_text": recognized_text,
        "agent_answer": agent_answer
    }
