import torch
import pandas as pd
import time

# Define um diretório de cache
cache_dir = 'cache_dir'

# Inicia a contagem de tempo
start_time = time.time()

# Verifica se há uma GPU disponível e define o dispositivo (GPU ou CPU)
device = torch.device('cuda') if torch.cuda.is_available() else 'cpu'
num_gpus = torch.cuda.device_count()

# Verifica se há GPUs disponíveis e imprime informações sobre elas
if num_gpus > 0:
    print(f"GPUs available: {num_gpus}")
    for i in range(num_gpus):
        gpu_name = torch.cuda.get_device_name(i)
        print(f"GPU {i}: {gpu_name}")
else:
    print("There is no GPU available. Using CPU")

# Lê um arquivo CSV usando pandas e adiciona uma coluna 'id' com índices
# Link para download do arquivo .csv: https://www.kaggle.com/code/sela001/facebook-google-store-reviews/input
pdf = pd.read_csv(f"data/facebook_reviews.csv")
pdf['id'] = pdf.index

# Importa a classe InputExample do pacote sentence_transformers
from sentence_transformers import InputExample

# Cria um subconjunto do DataFrame pdf com as primeiras 100.000 linhas
pdf_subset = pdf.head(1000)

# Importa a classe SentenceTransformer do pacote sentence_transformers
from sentence_transformers import SentenceTransformer

# Inicializa um modelo SentenceTransformer com o modelo 'all-MiniLM-L6-v2'
model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    cache_folder=cache_dir
)

model.to(device)

# Codifica os textos do DataFrame pdf_subset usando o modelo SentenceTransformer
faiss_review_text_embedding = model.encode(pdf_subset.review_text.values.tolist())

# Importa bibliotecas numpy e faiss para tarefas de busca e indexação
import numpy as np
import faiss

# Define um índice com base nas representações vetoriais normalizadas
pdf_to_index = pdf_subset.set_index(['id'], drop=False)
id_index = np.array(pdf_to_index.id.values).flatten().astype('int')

content_encoded_normalized = faiss_review_text_embedding.copy()
faiss.normalize_L2(content_encoded_normalized)

index_content = faiss.IndexIDMap(faiss.IndexFlatIP(len(faiss_review_text_embedding[0])))
index_content.add_with_ids(content_encoded_normalized, id_index)

# Define uma função para realizar a busca de conteúdo
def search_content(query, pdf_to_index, k=5):
    query_vector = model.encode([query])
    faiss.normalize_L2(query_vector)

    top_k = index_content.search(query_vector, k)
    ids = top_k[1][0].tolist()
    similarities = top_k[0][0].tolist()

    results = pdf_to_index.loc[ids]
    results['similarities'] = similarities

    return results

# Realiza uma pesquisa de conteúdo com a consulta 'annoying ads'
# e exibe os resultados com as similaridades
print(search_content('annoying ads', pdf_to_index))

# Encerra a contagem de tempo e calcula o tempo total de execução
end_time = time.time()
total_time = end_time - start_time
total_time = time.strftime("%H:%M:%S", time.gmtime(total_time))
print("Script execution time:", total_time)
