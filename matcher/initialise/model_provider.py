from sentence_transformers import SentenceTransformer

g_model = None

def get_sentenance_model():
    global g_model
    if g_model is None:
        g_model = SentenceTransformer("all-MiniLM-L6-v2")
    return g_model