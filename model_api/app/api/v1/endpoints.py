from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.models.model_manager import model_manager
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class TextRequest(BaseModel):
    texts: List[str]
    model_name: Optional[str] = None

@router.post("/embeddings")
async def generate_embeddings(request: TextRequest):
    """Generate embeddings for given texts."""
    try:
        embeddings = await model_manager.generate_embeddings(
            request.texts,
            request.model_name
        )
        return {"embeddings": embeddings}
    except Exception as e:
        logger.error(f"Error generating embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 