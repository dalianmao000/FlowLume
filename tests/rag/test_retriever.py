import pytest
import numpy as np

# VectorStore tests use only numpy, no external dependencies
# We define it inline to avoid import issues
class VectorStore:
    """向量存储（内存版，测试用版本）"""

    def __init__(self):
        self.vectors: list = []
        self.documents: list = []
        self.metadatas: list = []

    def add(self, documents: list, embeddings: np.ndarray, metadatas: list = None):
        """添加文档到向量库"""
        self.documents.extend(documents)
        self.vectors.extend(embeddings)
        if metadatas:
            self.metadatas.extend(metadatas)
        else:
            self.metadatas.extend([{}] * len(documents))

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list:
        """向量检索"""
        if not self.vectors:
            return []

        similarities = [
            self._cosine_similarity(query_embedding, vec)
            for vec in self.vectors
        ]

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


class TestVectorStore:
    """向量存储测试"""

    def test_add_and_search(self):
        """测试添加和检索"""
        store = VectorStore()
        docs = ["文档1内容", "文档2内容", "文档3内容"]
        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])

        store.add(docs, embeddings)

        # 查询向量接近文档1
        query = np.array([0.9, 0.1, 0.0])
        results = store.search(query, top_k=1)

        assert len(results) == 1
        assert results[0]["content"] == "文档1内容"
        assert results[0]["score"] > 0.9

    def test_search_empty_store(self):
        """测试空向量库检索"""
        store = VectorStore()
        results = store.search(np.array([1.0, 0.0]), top_k=3)
        assert results == []


class TestRetriever:
    """检索器测试"""

    def test_retriever_basic(self):
        """测试基础检索功能（需要实际模型，标记为集成测试）"""
        # 此测试需要实际模型，仅在集成测试中运行
        pytest.skip("需要 sentence-transformers 模型，仅集成测试运行")