"""混合检索器 — BM25 + BGE 向量检索

V2 升级：
- 集成 BGE embedding 模型进行语义向量搜索
- 关键词 BM25 匹配 + 向量相似度融合
- 自动降级：BGE 不可用时退化为纯关键词匹配
"""

import json
import math
import os
from collections import Counter
from typing import List, Dict, Optional, Tuple

import numpy as np

from .embeddings import embedding_service, EmbeddingService


class BM25Scorer:
    """BM25 关键词匹配评分器"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self._doc_freqs: Dict[str, int] = {}  # 词 → 文档频率
        self._doc_lengths: List[int] = []       # 每篇文档长度
        self._avg_dl: float = 0.0               # 平均文档长度
        self._total_docs: int = 0

    def fit(self, documents: List[str]):
        """训练 BM25 — 统计词频和文档频率"""
        self._doc_freqs.clear()
        self._doc_lengths.clear()
        self._total_docs = len(documents)

        for doc in documents:
            tokens = self._tokenize(doc)
            self._doc_lengths.append(len(tokens))
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1

        self._avg_dl = (
            sum(self._doc_lengths) / self._total_docs
            if self._total_docs > 0
            else 1.0
        )

    def score(self, query: str, doc_idx: int) -> float:
        """计算查询对某篇文档的 BM25 分数"""
        if self._total_docs == 0:
            return 0.0

        query_tokens = self._tokenize(query)
        doc_len = self._doc_lengths[doc_idx]
        score = 0.0

        tf_counter = Counter(query_tokens)
        for token, qf in tf_counter.items():
            df = self._doc_freqs.get(token, 0)
            if df == 0:
                continue
            idf = math.log((self._total_docs - df + 0.5) / (df + 0.5) + 1.0)
            # 简化：假设词在文档中出现 1 次
            tf = 1.0
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self._avg_dl)
            score += idf * numerator / denominator * qf

        return score

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """中文分词 — 字符级 uni-gram + bi-gram"""
        text = text.replace(" ", "").replace("\n", "")
        tokens = list(text)  # uni-gram
        for i in range(len(text) - 1):
            tokens.append(text[i] + text[i + 1])  # bi-gram
        return tokens


class HybridRetriever:
    """混合检索器：BM25 关键词 + BGE 向量语义搜索

    V2 升级要点：
    - BGE embedding 模型提供语义理解能力
    - BM25 保证精确关键词匹配
    - 加权融合两种分数
    - 自动降级：BGE 不可用时退化为纯 BM25
    """

    def __init__(
        self,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        embedding_model: str = "BAAI/bge-small-zh-v1.5",
    ):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.embedding_model = embedding_model
        self.documents: List[Dict] = []
        self._doc_texts: List[str] = []
        self._doc_vectors: Optional[np.ndarray] = None
        self._bm25: Optional[BM25Scorer] = None
        self._embedding: Optional[EmbeddingService] = None
        self._vectors_ready: bool = False

        self._load_data()

    def _load_data(self):
        """加载景区知识库数据"""
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        json_path = os.path.join(data_dir, "attractions.json")

        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as fp:
                self.documents = json.load(fp)
        else:
            self.documents = self._get_builtin_data()

        # 构建检索文本
        self._build_index()

    def _build_index(self):
        """构建检索索引"""
        self._doc_texts = []
        for doc in self.documents:
            # 组合检索字段
            text = " ".join([
                doc.get("title", ""),
                doc.get("city", ""),
                doc.get("type", ""),
                doc.get("content", ""),
            ])
            self._doc_texts.append(text)

        # 初始化 BM25
        self._bm25 = BM25Scorer()
        if self._doc_texts:
            self._bm25.fit(self._doc_texts)

        # 延迟初始化向量（首次检索时进行，避免导入时加载模型）
        self._vectors_ready = False

    def _ensure_vectors(self):
        """确保向量已编码（延迟初始化）"""
        if self._vectors_ready:
            return
        if not self._doc_texts:
            self._vectors_ready = True
            return

        self._embedding = embedding_service
        try:
            self._doc_vectors = self._embedding.encode(self._doc_texts)
        except Exception:
            # 向量编码失败，降级为纯 BM25
            self._doc_vectors = None

        self._vectors_ready = True

    def _get_builtin_data(self) -> List[Dict]:
        """内置景区知识库"""
        return [
            {"title": "故宫博物院", "city": "北京", "type": "历史文化",
             "content": "故宫博物院位于北京中轴线中心，是中国明清两代的皇家宫殿，旧称紫禁城。"
                       "占地面积72万平方米，建筑面积约15万平方米，有大小宫殿七十多座，房屋九千余间。"
                       "故宫是世界上现存规模最大、保存最为完整的木质结构古建筑群之一，"
                       "1987年被列为世界文化遗产。游览时间约4小时，门票60元。亲子友好，有休息区。",
             "duration": "4小时", "price": 60, "kid_friendly": True},
            {"title": "中国科技馆", "city": "北京", "type": "科技馆",
             "content": "中国科学技术馆是中国唯一的国家级综合性科技馆，位于北京奥林匹克公园中心区。"
                       "馆内设有科学乐园、华夏之光、探索与发现等五大主题展厅，"
                       "拥有丰富的互动体验项目和科学实验表演，是亲子科普教育的绝佳场所。"
                       "游览时间约3小时，门票30元。极其适合带娃出行。",
             "duration": "3小时", "price": 30, "kid_friendly": True},
            {"title": "颐和园", "city": "北京", "type": "园林",
             "content": "颐和园是中国清朝时期皇家园林，坐落于北京西郊，占地约290公顷。"
                       "以昆明湖、万寿山为基址，以杭州西湖为蓝本，汲取江南园林的设计手法建成。"
                       "园内有长廊、石舫、佛香阁等著名景点。游览时间约3小时，门票30元。"
                       "环境优美，适合全家散步游览。",
             "duration": "3小时", "price": 30, "kid_friendly": True},
            {"title": "北京动物园", "city": "北京", "type": "动物园",
             "content": "北京动物园位于北京市西城区，是中国最大的城市动物园之一。"
                       "园内饲养展览动物500余种5000多只，最受欢迎的当属大熊猫馆。"
                       "还有海洋馆、狮虎山、猴山等热门场馆。游览时间约3小时，门票15元。"
                       "亲子出行的首选目的地。",
             "duration": "3小时", "price": 15, "kid_friendly": True},
            {"title": "798艺术区", "city": "北京", "type": "艺术区",
             "content": "798艺术区位于北京朝阳区酒仙桥街道大山子地区，原为国营798厂等老工业厂区。"
                       "现已成为北京最具影响力的当代艺术区之一，聚集了大量画廊、艺术工作室和创意店铺。"
                       "适合年轻人拍照打卡，游览时间约2小时，免费开放。",
             "duration": "2小时", "price": 0, "kid_friendly": False},
            {"title": "西湖", "city": "杭州", "type": "自然风光",
             "content": "西湖位于浙江省杭州市西部，是中国主要的观赏性淡水湖泊之一，"
                       "也是世界文化遗产。西湖三面环山，面积约6.39平方千米，"
                       "以'苏堤春晓、断桥残雪、雷峰夕照'等十景闻名。免费开放，"
                       "适合全天游览。亲子友好，可以坐船游湖。",
             "duration": "半天", "price": 0, "kid_friendly": True},
            {"title": "灵隐寺", "city": "杭州", "type": "宗教文化",
             "content": "灵隐寺位于浙江省杭州市西湖区，始建于东晋咸和元年（326年），"
                       "是中国佛教禅宗十大古刹之一。寺内主要建筑有天王殿、大雄宝殿、药师殿等。"
                       "飞来峰造像更是珍贵的佛教艺术遗产。游览时间约2小时，门票45元。",
             "duration": "2小时", "price": 45, "kid_friendly": False},
            {"title": "杭州乐园", "city": "杭州", "type": "主题乐园",
             "content": "杭州乐园是长三角地区著名的主题乐园，位于杭州市萧山区。"
                       "园区分为冒险岛、玛雅部落、失落丛林等主题区域，"
                       "拥有过山车、大摆锤等刺激项目，也有适合儿童的亲子游乐区。"
                       "建议安排全天游览，门票190元。亲子必去的游乐胜地。",
             "duration": "全天", "price": 190, "kid_friendly": True},
        ]

    # ========== 检索接口 ==========

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """执行混合检索

        Args:
            query: 搜索查询，如 '北京 亲子 景点'
            top_k: 返回结果数量

        Returns:
            排序后的文档列表，每项附带 _bm25_score 和 _vector_score
        """
        if not self.documents:
            return []

        self._ensure_vectors()
        n_docs = len(self._doc_texts)
        scores = np.zeros(n_docs)

        # 1. BM25 分数
        for i in range(n_docs):
            scores[i] = self._bm25.score(query, i)

        # 2. 向量语义分数
        if self._doc_vectors is not None and len(self._doc_vectors) > 0:
            try:
                query_vec = self._embedding.encode_query(query)
                vec_scores = EmbeddingService.batch_similarity(
                    query_vec, self._doc_vectors
                )
                # 将余弦相似度 [-1, 1] 映射到 [0, 1]
                vec_scores = (vec_scores + 1) / 2
                scores = (
                    self.bm25_weight * self._normalize_scores(scores)
                    + self.vector_weight * vec_scores
                )
            except Exception:
                # 向量检索失败，仅用 BM25
                pass

        # 排序取 top_k
        idxs = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in idxs:
            if scores[idx] > 0:
                doc = dict(self.documents[idx])
                doc["_score"] = round(float(scores[idx]), 4)
                doc["_bm25_weight"] = self.bm25_weight
                doc["_vector_weight"] = self.vector_weight
                doc["_using_embeddings"] = self._doc_vectors is not None
                results.append(doc)

        return results

    @staticmethod
    def _normalize_scores(scores: np.ndarray) -> np.ndarray:
        """将分数归一化到 [0, 1]"""
        smax = scores.max()
        if smax > 0:
            return scores / smax
        return scores

    # ========== 状态查询 ==========

    @property
    def using_embeddings(self) -> bool:
        """是否正在使用向量检索"""
        return self._doc_vectors is not None

    @property
    def backend_name(self) -> str:
        """当前使用的 embedding 后端"""
        if self._embedding:
            return self._embedding.backend
        return "none"

    def stats(self) -> Dict:
        """检索器统计数据"""
        return {
            "total_documents": len(self.documents),
            "using_embeddings": self.using_embeddings,
            "embedding_backend": self.backend_name,
            "embedding_model": self.embedding_model,
            "bm25_weight": self.bm25_weight,
            "vector_weight": self.vector_weight,
        }
