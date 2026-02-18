import numpy as np
from sentence_transformers import SentenceTransformer
import torch

# Carrega modelo local gratuito (faz download apenas na primeira vez)
# Usaremos um modelo pequeno e eficiente para embeddings
print("Carregando modelo... (isso acontece apenas na primeira vez)")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')  # Suporta português

# Se tiver GPU, adicione isso após carregar o modelo
if torch.cuda.is_available():
    model = model.to('cuda')
    print("Usando GPU para aceleração!")

# Base de documentos
documents = [
    "Aprendizado de máquina é um subcampo da inteligência artificial.",
    "Redes neurais são inspiradas no cérebro humano.",
    "O Brasil possui grande biodiversidade.",
    "O PostgreSQL é um banco de dados relacional.",
    "Embeddings transformam texto em vetores numéricos."
]

# Gerar embeddings para os documentos
print("Gerando embeddings dos documentos...")
doc_embeddings = model.encode(documents)

# Função de similaridade (cosine similarity)
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# Função de busca semântica
def semantic_search(query, top_k=3):
    # Gera embedding para a query
    query_embedding = model.encode(query)
    
    # Calcula similaridades
    similarities = [
        cosine_similarity(query_embedding, doc_embedding)
        for doc_embedding in doc_embeddings
    ]
    
    # Ordena pelos mais similares
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    return [(documents[i], similarities[i]) for i in top_indices]

# Teste
query = "Como funcionam redes neurais?"
results = semantic_search(query, top_k=10)

print("\n🔎 Query:", query)
print("\n📌 Resultados:\n")

for text, score in results:
    print(f"Score: {score:.4f}")
    print("Texto:", text)
    print()