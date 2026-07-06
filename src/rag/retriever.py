"""混合检索器 — BM25 + 向量检索，从景小游 RAG 模块复用"""

import json
import os
from typing import List, Dict, Optional


class HybridRetriever:
    """混合检索器：结合 BM25 关键词匹配和向量语义搜索

    这是景小游 RAG 模块的独立副本，作为 TripAgent 的景点搜索后端。
    V1 版本使用简化的关键词匹配；后续可升级为真正的 BM25 + embedding。
    """

    def __init__(
        self,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        embedding_model: str = "BAAI/bge-small-zh-v1.5"
    ):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.embedding_model = embedding_model
        self.documents: List[Dict] = []
        self._load_data()

    def _load_data(self):
        """加载景区知识库数据"""
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        # 尝试加载 JSON 数据文件
        json_files = [
            os.path.join(data_dir, "attractions.json"),
            os.path.join(data_dir, "attractions.csv"),
        ]
        for f in json_files:
            if os.path.exists(f):
                if f.endswith(".json"):
                    with open(f, "r", encoding="utf-8") as fp:
                        self.documents = json.load(fp)
                break

        # 如果没有外部数据，使用内置数据
        if not self.documents:
            self.documents = self._get_builtin_data()

    def _get_builtin_data(self) -> List[Dict]:
        """内置景区知识库（当没有外部数据文件时使用）"""
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

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """执行混合检索

        Args:
            query: 搜索查询，如 '北京 亲子 景点'
            top_k: 返回结果数量

        Returns:
            排序后的文档列表
        """
        if not self.documents:
            return []

        query_lower = query.lower()
        scored = []

        for doc in self.documents:
            score = self._compute_score(query_lower, doc)
            if score > 0:
                scored.append((score, doc))

        # 按分数降序排列，取 top_k
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    def _compute_score(self, query: str, doc: Dict) -> float:
        """计算文档与查询的相关性分数

        使用简化的 TF 匹配（V1 版本），后续可升级为 BM25 + 向量相似度。
        """
        # 检查各字段的匹配情况
        fields = [
            doc.get("title", ""),
            doc.get("city", ""),
            doc.get("type", ""),
            doc.get("content", ""),
        ]
        combined = " ".join(fields).lower()

        # 简单的关键词匹配分数
        score = 0.0
        keywords = query.split()
        for kw in keywords:
            if kw in combined:
                # 标题匹配权重更高
                if kw in doc.get("title", "").lower():
                    score += 3.0
                elif kw in doc.get("type", "").lower():
                    score += 2.0
                else:
                    score += 1.0

        return score
