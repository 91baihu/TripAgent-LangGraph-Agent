"""新功能测试 — 高德地图 API / BGE Embedding / Token 追踪 / 酒店搜索"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestAmapService:
    """高德地图服务测试"""

    def test_fallback_geocode(self):
        """测试地理编码 fallback（无 API Key 时使用本地坐标）"""
        from tools.amap_service import amap_service, FALLBACK_COORDS

        coords = amap_service.geocode("故宫", "北京")
        assert coords is not None
        lat, lng = coords
        assert 39 < lat < 41  # 北京纬度范围
        assert 115 < lng < 118  # 北京经度范围

    def test_fallback_geocode_unknown(self):
        """测试未知地点的地理编码"""
        from tools.amap_service import amap_service
        coords = amap_service.geocode("火星基地Alpha", "火星")
        assert coords is None

    def test_haversine_distance(self):
        """测试 Haversine 距离计算"""
        from tools.amap_service import amap_service

        dist, dur = amap_service._haversine(
            (39.9163, 116.3972), (39.9054, 116.3976)
        )
        assert 0.5 < dist < 2.0
        assert dur > 0

    def test_plan_route_fallback(self):
        """测试路线规划 fallback"""
        from tools.amap_service import amap_service

        result = amap_service.plan_route("故宫", "颐和园", "北京")
        assert result.distance_km > 0
        assert result.duration_min > 0
        assert result.transport in ("地铁", "打车/驾车", "骑行/公交")
        assert result.source == "fallback"

    def test_plan_route_unknown_spot(self):
        """测试未知景点的路线规划"""
        from tools.amap_service import amap_service

        result = amap_service.plan_route("火星乐园", "月球基地")
        assert "未找到" in result.route_detail


class TestHotelTool:
    """酒店搜索工具测试"""

    def test_search_beijing(self):
        """测试北京酒店搜索"""
        from tools.hotels import search_hotels

        result = search_hotels.invoke({"city": "北京"})
        assert "酒店" in result or "北京" in result
        assert len(result) > 50

    def test_search_near_spot(self):
        """测试景点附近酒店搜索"""
        from tools.hotels import search_hotels

        result = search_hotels.invoke({"city": "北京", "near_spot": "故宫"})
        assert "故宫" in result or "北京" in result

    def test_search_with_dates(self):
        """测试带日期的酒店搜索"""
        from tools.hotels import search_hotels

        result = search_hotels.invoke({
            "city": "杭州",
            "near_spot": "西湖",
            "check_in": "2026-07-10",
            "check_out": "2026-07-12",
        })
        assert "杭州" in result or "西湖" in result

    def test_search_budget_economy(self):
        """测试经济型酒店搜索"""
        from tools.hotels import search_hotels

        result = search_hotels.invoke({"city": "北京", "budget_level": "经济"})
        assert "北京" in result


class TestTokenTracker:
    """Token 追踪器测试"""

    def test_count_tokens_chinese(self):
        """测试中文 token 计数（字符估算模式）"""
        from server.token_tracker import token_tracker

        text = "你好，帮我规划一次北京旅行"
        count = token_tracker.count_tokens(text)
        assert count > 0
        # 中文约 1.5 chars/token → 大约 8-20 tokens
        assert 5 < count < 30

    def test_count_tokens_english(self):
        """测试英文 token 计数（字符估算模式）"""
        from server.token_tracker import token_tracker

        text = "Hello, help me plan a trip to Beijing"
        count = token_tracker.count_tokens(text)
        assert count > 0

    def test_calculate_cost(self):
        """测试成本计算"""
        from server.token_tracker import token_tracker

        input_cost, output_cost = token_tracker.calculate_cost(
            "deepseek-chat", input_tokens=1000, output_tokens=500
        )
        # ¥1/1M input, ¥2/1M output
        # input_cost = 1000/1M * 1.0 = 0.001
        assert 0.0005 < input_cost < 0.002
        assert 0.0005 < output_cost < 0.002

    def test_record_call(self):
        """测试记录调用"""
        from server.token_tracker import token_tracker

        usage = token_tracker.record_call(
            model="deepseek-chat",
            input_tokens=500,
            output_tokens=200,
            session_id="test_new_features_001",
            user_id="test_user",
        )
        assert usage is not None
        assert usage.total_tokens == 700
        assert usage.total_cost > 0

        stats = token_tracker.get_session_stats("test_new_features_001")
        assert stats is not None
        assert stats.call_count >= 1

    def test_format_cost_report(self):
        """测试成本报告格式化"""
        from server.token_tracker import token_tracker

        report = token_tracker.format_cost_report(session_id="test_new_features_001")
        assert "📊" in report

    def test_get_summary(self):
        """测试用量摘要"""
        from server.token_tracker import token_tracker

        summary = token_tracker.get_summary()
        assert "total_cost_yuan" in summary
        assert "alert_threshold_yuan" in summary


class TestEmbeddingService:
    """Embedding 服务测试 — 仅测试降级 TF-IDF 模式（无需下载模型）"""

    def test_backend_detection(self):
        """测试后端检测"""
        from rag.embeddings import EmbeddingService
        # 创建新实例避免被全局单例状态影响
        svc = EmbeddingService()
        backend = svc.backend
        assert backend in ("flagembedding", "sentence_transformers", "tfidf")

    def test_tfidf_encoding_fallback(self):
        """测试 TF-IDF 向量编码（强制使用降级模式）"""
        from rag.embeddings import EmbeddingService

        # 创建新实例，手动设置为 tfidf 后端，跳过模型加载
        svc = EmbeddingService()
        svc._backend = "tfidf"  # 强制降级模式
        svc._model = object()    # 非 None，跳过 _ensure_model 加载

        texts = ["北京故宫", "杭州西湖", "亲子科技馆"]
        vectors = svc.encode(texts)
        assert vectors.shape[0] == 3
        assert vectors.shape[1] > 0

    def test_cosine_similarity(self):
        """测试余弦相似度"""
        from rag.embeddings import EmbeddingService
        import numpy as np

        a = np.array([1.0, 0.0, 0.0])
        b = np.array([1.0, 0.0, 0.0])
        c = np.array([0.0, 1.0, 0.0])

        assert EmbeddingService.cosine_similarity(a, b) > 0.99
        assert EmbeddingService.cosine_similarity(a, c) < 0.01

    def test_batch_similarity(self):
        """测试批量相似度"""
        from rag.embeddings import EmbeddingService
        import numpy as np

        query = np.array([1.0, 0.0])
        docs = np.array([[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]])
        scores = EmbeddingService.batch_similarity(query, docs)
        assert len(scores) == 3
        assert scores[0] > 0.99
        assert scores[1] < 0.01


class TestHybridRetrieverV2:
    """混合检索器 V2 测试（BGE 升级版）"""

    def test_search_with_bm25(self):
        """测试 BM25 关键词检索"""
        from rag.retriever import HybridRetriever

        retriever = HybridRetriever()
        results = retriever.search("北京 亲子")
        assert len(results) > 0

    def test_stats(self):
        """测试检索器统计"""
        from rag.retriever import HybridRetriever

        retriever = HybridRetriever()
        stats = retriever.stats()
        assert stats["total_documents"] > 0
        assert "using_embeddings" in stats
        assert "embedding_backend" in stats


class TestRouteTool:
    """路线工具 V2 测试（高德 API 版）"""

    def test_route_format(self):
        """测试新版路线输出格式"""
        from tools.route import plan_route

        result = plan_route.invoke({"spot_a": "故宫", "spot_b": "颐和园"})
        assert "故宫" in result
        assert "颐和园" in result
        assert "km" in result
        assert "数据来源" in result

    def test_route_with_city(self):
        """测试指定城市的路线规划"""
        from tools.route import plan_route

        result = plan_route.invoke({"spot_a": "西湖", "spot_b": "灵隐寺", "city": "杭州"})
        assert "西湖" in result
        assert "灵隐寺" in result
