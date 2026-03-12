import pytest
from sentence_transformers import SentenceTransformer
import numpy as np
from config.settings import SEARCH_MODEL_PATH
from sklearn.metrics.pairwise import cosine_similarity

def test_model_loading():
    """Test that the model can be loaded from the local path"""
    model = SentenceTransformer(SEARCH_MODEL_PATH)
    assert model is not None, "Model should be loaded successfully"

def search(query, model, embeddings, data, top_n=5):
    query_embedding = model.encode(query, convert_to_tensor=True)
    query_embedding = query_embedding.reshape(1, -1)  
    similarities = cosine_similarity(query_embedding.cpu().numpy(), embeddings.cpu().numpy())
    top_indices = np.argsort(-similarities[0])[:top_n]
    
    # Get top results from the list
    top_results = [data[i] for i in top_indices]
    
    # Create a list of tuples (text, similarity)
    results_with_similarity = [(text, similarities[0][i]) for i, text in zip(top_indices, top_results)]
    
    return results_with_similarity
    
def test_model_inference():
    """Test model inference on sample text"""
    # Load model
    model = SentenceTransformer(SEARCH_MODEL_PATH)
    
    data = [
        'Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language...',
        'Deep learning has revolutionized the field of computer vision, enabling computers to interpret and understand visual information with unprecedented accuracy...',
        'Reinforcement learning is an area of machine learning where an agent learns to make decisions by interacting with its environment...',
        'Convolutional Neural Networks (CNNs) are a class of deep learning algorithms that have shown great success in various computer vision tasks...',
        'Text classification is a common task in natural language processing, which involves assigning predefined categories to a given text...'
        ]
    
    embeddings = model.encode(data, convert_to_tensor=True)

    query = "natural language processing"
    results = search(query, model, embeddings, data, top_n=3)
    print(results)
        
