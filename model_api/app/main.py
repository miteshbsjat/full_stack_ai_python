from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router
import logging
import time
import uvicorn
from uvicorn.config import LOGGING_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Document Search ML API",
    description="API for ML models used in document search",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_response_time(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    logger.info(f"Request to {request.url.path} took {process_time:.2f}ms")
    return response

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == '__main__':
    # Configure Uvicorn logging
    LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelprefix)s %(client_addr)s - \"%(request_line)s\" %(status_code)s"
    
    # Run the server
    uvicorn.run(
        'app.main:app',  # Updated module path
        host='0.0.0.0',
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_config=LOGGING_CONFIG
    ) 