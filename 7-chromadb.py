import chromadb
import struct
import time
import hashlib
import numpy as np
from common import read_verses
from sentence_transformers import SentenceTransformer
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
md5_hash = hashlib.md5()

# setup Chroma in-memory, for easy prototyping. Can add persistence easily!
client = chromadb.HttpClient(
    host="localhost",
    port=18000,
    ssl=False,
    headers=None,
    settings=Settings(),
    tenant=DEFAULT_TENANT,
    database=DEFAULT_DATABASE
)

collection_name = "collection_768"
# Create collection. get_collection, get_or_create_collection, delete_collection also available!
try:
    collection = client.get_collection(name=collection_name)
except Exception as e:
    collection = client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})


def chroma_inserts(chunk):
    start_time = time.perf_counter()

    documents = []
    embeddings = []
    metadatas = []
    ids = []
    for id, text, meta, embedding in chunk:
        md5_hash.update(id.encode('utf-8'))
        id = md5_hash.hexdigest()

        # Ensure embedding is a list of floats
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()

        documents.append(text)
        embeddings.append(embedding)
        metadatas.append(meta)
        ids.append(id)

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"batch insert: {elapsed_time} sec")

    return elapsed_time

def chroma_filter_search(embeddings):
    # # Query/search 2 most similar results. You can also .get by id
    results = collection.query(
        query_embeddings=[embeddings],
        n_results=10,
        # where={"metadata_field": "is_equal_to_this"}, # optional filter
        # where_document={"$contains":"search_string"}  # optional filter
    )

    # print(results)
    documents = results['documents'][0]  # The documents list is nested inside another list
    distances = results['distances'][0]  # The documents list is nested inside another list

    for text, distance in zip(documents, distances):
        print(f"Text: {text}; Similarity: {1-distance}")



read_verses(chroma_inserts, max_items=1400000, minibatch_size=1000)

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
embeddings = model.encode("воскресил из мертвых")
embeddings = embeddings.tolist()

start_time = time.perf_counter()

chroma_filter_search(embeddings)
chroma_filter_search(embeddings)
chroma_filter_search(embeddings)
chroma_filter_search(embeddings)
chroma_filter_search(embeddings)

end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(f"Search time: {elapsed_time/5} sec")