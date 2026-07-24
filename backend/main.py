from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routers.chat_router import router as chat_router

load_dotenv()
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN","http://localhost:3000")

app = FastAPI(title="Ask AI")

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status":"ok"}

# main.py is entry point
app.include_router(chat_router)

