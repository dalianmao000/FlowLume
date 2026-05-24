import pytest
import tempfile
import os
from src.rag.document_loader import PDFLoader, DocumentLoaderFactory
from src.rag.text_splitter import RecursiveCharacterSplitter, SemanticSplitter


class TestDocumentLoader:
    """文档加载器测试"""

    def test_pdf_loader_nonexistent_file(self):
        """测试加载不存在的 PDF"""
        loader = PDFLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/file.pdf")


class TestTextSplitter:
    """文本分块器测试"""

    def test_recursive_splitter_basic(self):
        """测试基础分块"""
        splitter = RecursiveCharacterSplitter(chunk_size=100, chunk_overlap=20)
        text = "这是第一段文本。\n\n这是第二段文本，包含更多内容。" * 10
        chunks = splitter.split(text)
        assert len(chunks) > 0
        assert all(len(c) <= 120 for c in chunks)  # 允许一定溢出

    def test_recursive_splitter_overlap(self):
        """测试分块重叠"""
        splitter = RecursiveCharacterSplitter(chunk_size=50, chunk_overlap=20)
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 5
        chunks = splitter.split(text)
        if len(chunks) >= 2:
            # 验证重叠存在
            assert any(
                chunks[i][-20:] == chunks[i + 1][:20]
                for i in range(len(chunks) - 1)
                if len(chunks[i]) >= 20 and len(chunks[i + 1]) >= 20
            )

    def test_semantic_splitter(self):
        """测试语义分块"""
        splitter = SemanticSplitter(max_sentences_per_chunk=2)
        text = "这是第一句。这是第二句。这是第三句。这是第四句。" * 10
        chunks = splitter.split(text)
        assert len(chunks) >= 2