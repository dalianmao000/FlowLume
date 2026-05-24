import os
from abc import ABC, abstractmethod
from typing import List
import fitz  # PyMuPDF


class DocumentLoader(ABC):
    """文档加载器抽象基类"""

    @abstractmethod
    def load(self, source: str) -> str:
        """加载文档内容"""
        pass


class PDFLoader(DocumentLoader):
    """PDF 文档加载器"""

    def load(self, source: str) -> str:
        """从 PDF 文件加载文本"""
        if not os.path.exists(source):
            raise FileNotFoundError(f"PDF 文件不存在: {source}")

        text_parts = []
        doc = fitz.open(source)
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text_parts.append(page.get_text())
        finally:
            doc.close()

        return "\n\n".join(text_parts)


class WebLoader(DocumentLoader):
    """网页内容加载器"""

    def load(self, source: str) -> str:
        """从 URL 加载网页文本（PoC 阶段简化实现）"""
        try:
            import httpx
            response = httpx.get(source, timeout=30)
            response.raise_for_status()
            # 简化处理：实际生产应使用 BeautifulSoup 提取正文
            return response.text[:10000]  # 限制长度
        except Exception as e:
            raise RuntimeError(f"网页加载失败 {source}: {e}")


class DocumentLoaderFactory:
    """文档加载器工厂"""

    @staticmethod
    def get_loader(source: str) -> DocumentLoader:
        """根据文件扩展名获取对应加载器"""
        if source.endswith(".pdf"):
            return PDFLoader()
        elif source.startswith("http"):
            return WebLoader()
        else:
            raise ValueError(f"不支持的文档类型: {source}")

    @staticmethod
    def load_any(source: str) -> str:
        """自动识别类型并加载"""
        loader = DocumentLoaderFactory.get_loader(source)
        return loader.load(source)