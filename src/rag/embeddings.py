"""BGE Embedding 服务 — 为 HybridRetriever 提供向量语义搜索能力

支持 BGE 模型（BAAI/bge-small-zh-v1.5），带自动降级：
- FlagEmbedding 可用 → 真实向量相似度
- sentence-transformers 可用 → 真实向量相似度
- 都不可用 → 降级为 TF-IDF 关键词匹配
"""

import os
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass

import numpy as np


@dataclass
class EmbeddingConfig:
    """Embedding 模型配置"""
    model_name: str = "BAAI/bge-small-zh-v1.5"
    device: str = "cpu"  # "cpu" | "cuda"
    normalize: bool = True  # BGE 模型推荐归一化
    max_seq_length: int = 512


class EmbeddingService:
    """Embedding 服务 — 统一的向量化接口

    自动检测可用的 embedding 后端：
    1. FlagEmbedding (BGE 官方库) — 最快，支持中文
    2. sentence-transformers — 通用，模型生态丰富
    3. TF-IDF — 纯 Python，零依赖降级
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self._model = None
        self._backend = None  # "flagembedding" | "sentence_transformers" | "tfidf"
        self._vocab: dict = {}  # TF-IDF 词汇表
        self._idf: dict = {}    # TF-IDF IDF 值

    @property
    def backend(self) -> str:
        """检测当前使用的后端"""
        if self._backend is None:
            self._backend = self._detect_backend()
        return self._backend

    def _detect_backend(self) -> str:
        """自动检测可用的 embedding 后端"""
        # 1. 尝试 FlagEmbedding
        try:
            from FlagEmbedding import BGEM3FlagModel  # noqa: F401
            return "flagembedding"
        except ImportError:
            pass

        try:
            from flagembedding import FlagModel  # noqa: F401
            return "flagembedding"
        except ImportError:
            pass

        # 2. 尝试 sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401
            return "sentence_transformers"
        except ImportError:
            pass

        # 3. 降级 TF-IDF
        return "tfidf"

    # ========== 模型加载 ==========

    def _load_flagembedding(self):
        """加载 FlagEmbedding 模型"""
        try:
            try:
                from FlagEmbedding import BGEM3FlagModel
                self._model = BGEM3FlagModel(
                    self.config.model_name,
                    use_fp16=False,
                    device=self.config.device,
                )
            except ImportError:
                from flagembedding import FlagModel
                self._model = FlagModel(
                    self.config.model_name,
                    query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
                    use_fp16=False,
                )
        except (OSError, MemoryError, RuntimeError) as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to load FlagEmbedding model '{self.config.model_name}': {e}"
            )
            self._model = None
            self._backend = "tfidf"

    def _load_sentence_transformers(self):
        """加载 sentence-transformers 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device,
            )
        except (OSError, MemoryError, RuntimeError) as e:
            # 模型下载失败或内存不足 → 降级到 TF-IDF
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to load SentenceTransformer model '{self.config.model_name}': {e}"
            )
            self._model = None
            self._backend = "tfidf"

    def _ensure_model(self):
        """延迟加载模型"""
        if self._model is not None:
            return

        backend = self.backend
        if backend == "flagembedding":
            self._load_flagembedding()
        elif backend == "sentence_transformers":
            self._load_sentence_transformers()
        # TF-IDF 不需要加载模型

    # ========== 向量编码 ==========

    def encode(self, texts: List[str]) -> np.ndarray:
        """将文本列表编码为向量

        Args:
            texts: 文本列表

        Returns:
            shape (len(texts), dim) 的 numpy 数组
        """
        self._ensure_model()

        backend = self.backend
        if backend == "flagembedding":
            return self._encode_flagembedding(texts)
        elif backend == "sentence_transformers":
            return self._encode_sentence_transformers(texts)
        else:
            return self._encode_tfidf(texts)

    def encode_query(self, query: str) -> np.ndarray:
        """编码查询文本（单条）

        BGE 模型推荐对 query 添加 instruction prefix。
        """
        self._ensure_model()

        backend = self.backend
        if backend == "flagembedding":
            # FlagEmbedding 自动处理 query instruction
            return self._encode_flagembedding([query])
        elif backend == "sentence_transformers":
            return self._encode_sentence_transformers([query])
        else:
            return self._encode_tfidf([query])

    def _encode_flagembedding(self, texts: List[str]) -> np.ndarray:
        """FlagEmbedding 编码"""
        embeddings = self._model.encode(
            texts,
            batch_size=8,
            max_length=self.config.max_seq_length,
        )
        # BGEM3FlagModel 返回 dict with 'dense_vecs'
        if isinstance(embeddings, dict):
            embeddings = embeddings.get("dense_vecs", embeddings.get("dense_embeddings"))
        result = np.array(embeddings)
        if self.config.normalize and result.ndim == 2:
            norms = np.linalg.norm(result, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            result = result / norms
        return result

    def _encode_sentence_transformers(self, texts: List[str]) -> np.ndarray:
        """sentence-transformers 编码"""
        embeddings = self._model.encode(
            texts,
            batch_size=8,
            normalize_embeddings=self.config.normalize,
        )
        return np.array(embeddings)

    # ========== TF-IDF 降级实现 ==========

    def _build_vocab(self, documents: List[str]):
        """从文档集合构建 TF-IDF 词汇表"""
        from collections import Counter

        # 分词（简单字符级 bigram，适合中文）
        doc_tokens = []
        for doc in documents:
            tokens = []
            # 字符级 uni-gram + bi-gram
            chars = list(doc.replace(" ", ""))
            tokens.extend(chars)
            for i in range(len(chars) - 1):
                tokens.append(chars[i] + chars[i + 1])
            doc_tokens.append(Counter(tokens))

        # 计算 IDF
        N = len(documents)
        all_tokens = set()
        for dt in doc_tokens:
            all_tokens.update(dt.keys())

        self._idf = {}
        for token in all_tokens:
            df = sum(1 for dt in doc_tokens if token in dt)
            self._idf[token] = math.log((N + 1) / (df + 1)) + 1

        self._vocab = {token: i for i, token in enumerate(sorted(all_tokens))}

    def _encode_tfidf(self, texts: List[str]) -> np.ndarray:
        """TF-IDF 向量编码"""
        from collections import Counter

        # 如果没有词汇表，用当前 texts 构建
        if not self._vocab:
            self._build_vocab(texts)

        vectors = np.zeros((len(texts), len(self._vocab)))
        for i, text in enumerate(texts):
            chars = list(text.replace(" ", ""))
            tokens = chars + [chars[j] + chars[j + 1] for j in range(len(chars) - 1)]
            tf = Counter(tokens)
            total = sum(tf.values()) or 1
            for token, count in tf.items():
                if token in self._vocab:
                    idx = self._vocab[token]
                    vectors[i][idx] = (count / total) * self._idf.get(token, 1.0)

        # 归一化
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return vectors / norms

    # ========== 相似度计算 ==========

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """计算两个向量的余弦相似度"""
        dot = np.dot(a.flatten(), b.flatten())
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    def batch_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        """计算查询向量与多个文档向量的余弦相似度

        Args:
            query_vec: shape (dim,)
            doc_vecs: shape (n, dim)

        Returns:
            shape (n,) 相似度数组
        """
        query_vec = query_vec.flatten()
        norms_q = np.linalg.norm(query_vec)
        norms_d = np.linalg.norm(doc_vecs, axis=1)
        dots = np.dot(doc_vecs, query_vec)
        denom = norms_q * norms_d
        denom = np.where(denom == 0, 1, denom)
        return dots / denom


# 全局单例
embedding_service = EmbeddingService()
