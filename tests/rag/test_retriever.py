import sys
import os
import pytest
import numpy as np

# Mock heavy dependencies before importing the production module
import unittest.mock as mock
sys.modules['sentence_transformers'] = mock.MagicMock()

# Import directly from retriever module to avoid triggering src.rag.__init__
# which has heavy dependencies (fitz, sentence-transformers)
import importlib.util
spec = importlib.util.spec_from_file_location(
    "retriever_module",
    os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'rag', 'retriever.py')
)
retriever_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retriever_module)
VectorStore = retriever_module.VectorStore


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