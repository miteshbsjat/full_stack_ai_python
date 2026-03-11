from sentence_transformers import SentenceTransformer
import torch
import psutil
import logging
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self._models: Dict[str, any] = {}
        self.default_model = 'all-MiniLM-L6-v2'

    def get_model(self, model_name: Optional[str] = None) -> any:
        """Get or load a model by name."""
        model_name = model_name or self.default_model
        
        if model_name not in self._models:
            logger.info(f"Loading model: {model_name}")
            mem_before = self.get_memory_usage()
            
            if model_name.startswith('all-MiniLM'):
                self._models[model_name] = SentenceTransformer(model_name)
            else:
                raise ValueError(f"Unknown model: {model_name}")
            
            mem_after = self.get_memory_usage()
            logger.info(f"Model loaded. Memory usage: {mem_after - mem_before:.2f} MB")
        
        return self._models[model_name]

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    async def generate_embeddings(
        self,
        texts: Union[str, List[str]],
        model_name: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for given texts."""
        if isinstance(texts, str):
            texts = [texts]
        
        model = self.get_model(model_name)
        
        with torch.no_grad():
            embeddings = model.encode(texts)
            # Convert numpy arrays to nested lists
            if len(texts) == 1:
                return [embeddings.tolist()]  # Single embedding
            return [emb.tolist() for emb in embeddings]  # Multiple embeddings

# Global model manager instance
model_manager = ModelManager() 