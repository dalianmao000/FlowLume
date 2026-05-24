from typing import List
from abc import ABC, abstractmethod


class TextSplitter(ABC):
    """文本分块器抽象基类"""

    @abstractmethod
    def split(self, text: str) -> List[str]:
        """将文本切分为块"""
        pass


class RecursiveCharacterSplitter(TextSplitter):
    """递归字符分块器"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", "，", " ", ""]

    def split(self, text: str) -> List[str]:
        """递归分块"""
        chunks = []
        start = 0

        while start < len(text):
            original_end = start + self.chunk_size
            end = original_end
            chunk = text[start:end]

            # 寻找最佳分割点
            if end < len(text):
                best_sep = -1
                for sep in self.separators:
                    last_sep = chunk.rfind(sep)
                    if last_sep > self.chunk_size // 2:
                        best_sep = last_sep
                        break

                if best_sep > 0:
                    chunk = chunk[:best_sep]
                    end = start + best_sep

            chunks.append(chunk.strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]


class SemanticSplitter(TextSplitter):
    """基于句子边界的语义分块器（PoC 简化版）"""

    def __init__(self, max_sentences_per_chunk: int = 5):
        self.max_sentences_per_chunk = max_sentences_per_chunk

    def split(self, text: str) -> List[str]:
        """按句子数分块"""
        import re
        # 简单句子分割（中文/英文）
        sentences = re.split(r'([。.!?]+)', text)
        # 合并句子和标点
        merged = []
        for i in range(0, len(sentences) - 1, 2):
            merged.append(sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else ""))

        chunks = []
        current_chunk = ""
        for sentence in merged:
            if len(current_chunk) + len(sentence) <= self.max_sentences_per_chunk * 100:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks