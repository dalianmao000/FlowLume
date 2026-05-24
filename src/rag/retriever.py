import os
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()


class EmbeddingModel:
    """嵌入模型封装"""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(self.model_name)

    def embed(self, texts: List[str]) -> np.ndarray:
        """将文本列表转为嵌入向量"""
        return self.model.encode(texts, show_progress_bar=False)


class VectorStore:
    """向量存储（内存版，PoC 阶段使用）"""

    def __init__(self):
        self.vectors: List[np.ndarray] = []
        self.documents: List[str] = []
        self.metadatas: List[dict] = []

    def add(self, documents: List[str], embeddings: np.ndarray, metadatas: List[dict] = None):
        """添加文档到向量库"""
        self.documents.extend(documents)
        self.vectors.extend(embeddings)
        if metadatas:
            self.metadatas.extend(metadatas)
        else:
            self.metadatas.extend([{}] * len(documents))

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[dict]:
        """向量检索"""
        if not self.vectors:
            return []

        # 计算余弦相似度
        similarities = [
            self._cosine_similarity(query_embedding, vec)
            for vec in self.vectors
        ]

        # 获取 top_k 索引
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [
            {
                "content": self.documents[i],
                "metadata": self.metadatas[i],
                "score": float(similarities[i]),
            }
            for i in top_indices
        ]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8)

    def save(self, path: str):
        """保存向量库到磁盘（简化实现）"""
        import pickle
        with open(path, "wb") as f:
            pickle.dump({
                "vectors": self.vectors,
                "documents": self.documents,
                "metadatas": self.metadatas,
            }, f)

    def load(self, path: str):
        """从磁盘加载向量库"""
        import pickle
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.vectors = data["vectors"]
            self.documents = data["documents"]
            self.metadatas = data["metadatas"]


class Retriever:
    """检索器封装"""

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        top_k: int = 5,
    ):
        self.embedding_model = embedding_model or EmbeddingModel()
        self.vector_store = vector_store or VectorStore()
        self.top_k = top_k

    def index_documents(
        self,
        documents: List[str],
        metadatas: List[dict] = None,
        batch_size: int = 32,
    ):
        """索引文档"""
        embeddings = self.embedding_model.embed(documents)
        self.vector_store.add(documents, embeddings, metadatas)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[dict]:
        """检索相关文档"""
        query_embedding = self.embedding_model.embed([query])[0]
        return self.vector_store.search(query_embedding, top_k or self.top_k)

    def save_index(self, path: str):
        """保存索引"""
        self.vector_store.save(path)

    def load_index(self, path: str):
        """加载索引"""
        self.vector_store.load(path)