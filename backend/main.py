from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
import traceback


from routers.chat_router import router as chat_router
from routers.ingest_router import router as ingest_router


FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN","http://localhost:3000")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("askDocs")

app = FastAPI(title="Ask AI")

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    # Log the entire traceback to terminal
    logger.error("Unhandled error on %s\n%s", request.url.path,traceback.format_exc())
    return JSONResponse(
        status_code = 500,
        content={"error":str(exc), "type":type(exc).__name__},
    )

@app.get("/health")
def health():
    return {"status":"ok"}

# main.py is entry point
app.include_router(chat_router)
app.include_router(ingest_router)

