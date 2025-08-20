import os
import faiss
import torch
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Dict

class PolishRAGSystem:
    def __init__(
        self,
        data_folder: str = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_max_size: int = 5000,
        chunk_overlap: int = 200
    ):
        """
        Initialize the FAISS‑based RAG system with document chunking.
        If a data folder is provided, all .txt files in that folder will be loaded,
        chunked, and added to the FAISS index.
        """
        self.device = "cpu"  # "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        self.index = None         # FAISS index
        self.documents = []       # list of document chunks
        self.metadata = []        # corresponding metadata (e.g. filename) per chunk
        self.dimension = None
        self.chunk_max_size = chunk_max_size
        self.chunk_overlap = chunk_overlap
        self.reranker = None      # Will be set if you call load_reranker()

        if data_folder is not None:
            text_files = [
                os.path.join(data_folder, f)
                for f in os.listdir(data_folder)
                if f.endswith(".txt")
            ]
            for file in text_files:
                try:
                    with open(file, encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error reading {file}: {e}")
                    continue
                # Split the content into overlapping chunks
                chunks = self.split_text(content, chunk_max_size, chunk_overlap)
                for chunk in chunks:
                    self.documents.append(chunk)
                    self.metadata.append({"filename": os.path.basename(file)})
            # Add all chunks to the FAISS index
            self.add_documents(self.documents, self.metadata)

    def split_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Splits a given text into chunks of approximately `chunk_size` characters,
        with an overlap of `chunk_overlap` tokens between chunks.
        This is a simple implementation (token-based) and can be improved if needed.
        """
        tokens = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        for token in tokens:
            token_length = len(token) + 1  # approximate length including a space
            if current_length + token_length > chunk_size and current_chunk:
                chunk = " ".join(current_chunk)
                chunks.append(chunk)
                # Create overlap: take last chunk_overlap tokens (if available)
                overlap = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk
                current_chunk = overlap.copy()
                current_length = sum(len(t) + 1 for t in current_chunk)
            current_chunk.append(token)
            current_length += token_length
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def add_documents(self, documents: List[str], metadata_list: List[Dict] = None):
        """
        Compute embeddings for the given documents (chunks) and add them to the FAISS index.
        """
        if metadata_list is None:
            metadata_list = [{} for _ in documents]
        embeddings = self.model.encode(documents, convert_to_numpy=True)
        if self.dimension is None:
            self.dimension = embeddings.shape[1]
        # Create FAISS index if it does not exist
        if self.index is None:
            if self.device == "cuda":
                res = faiss.StandardGpuResources()
                cpu_index = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
            else:
                self.index = faiss.IndexFlatL2(self.dimension)
        # Add embeddings to the index
        self.index.add(embeddings)

    def search(self, query: str, top_k: int = 5, include_metadata: bool = True) -> List[Dict]:
        """
        Search for the top_k document chunks that are most similar to the query.
        Returns a list of dictionaries containing the text, similarity score, and metadata.
        """
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)
        results = []
        for d, idx in zip(distances[0], indices[0]):
            result = {
                'text': self.documents[idx],
                'similarity_score': 1 - d  # Note: d is an L2 distance; you may adjust this conversion.
            }
            if include_metadata:
                result['metadata'] = self.metadata[idx]
            results.append(result)
        return results

    def load_reranker(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2") -> "PolishRAGSystem":
        """
        Load a cross‑encoder model for reranking search results.
        """
        self.reranker = CrossEncoder(model_name, device=self.device)
        return self

    def rerank(self, query: str, results: List[Dict], top_k: int = 3) -> List[Dict]:
        """
        Rerank the search results using the cross‑encoder.
        Returns the top_k results after reranking.
        """
        if self.reranker is None:
            raise ValueError("Reranker model is not loaded. Call load_reranker() first.")
        # Prepare (query, document) pairs for scoring
        pairs = [(query, result['text']) for result in results]
        scores = self.reranker.predict(pairs)
        # Combine results with their scores and sort in descending order
        scored_results = list(zip(results, scores))
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return [result for result, score in scored_results[:top_k]]
