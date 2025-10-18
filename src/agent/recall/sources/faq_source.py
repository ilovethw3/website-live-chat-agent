"""
FAQ召回源适配器

实现FAQ数据访问的召回源，支持关键词匹配和向量检索。
"""

import logging
from typing import Any

from src.agent.recall.schema import RecallHit, RecallRequest
from src.agent.recall.sources.base import RecallSource

logger = logging.getLogger(__name__)


class FAQRecallSource(RecallSource):
    """FAQ召回源适配器"""

    def __init__(self):
        # FAQ数据存储（实际项目中可能从数据库或文件加载）
        self._faq_data = [
            {
                "id": "faq_001",
                "question": "你们的退货政策是什么？",
                "answer": "我们提供30天无理由退货服务，商品需保持原包装和标签完整。",
                "category": "退货政策",
                "keywords": ["退货", "退款", "退换", "30天", "无理由"]
            },
            {
                "id": "faq_002",
                "question": "如何联系客服？",
                "answer": "您可以通过在线客服、电话400-123-4567或邮件support@example.com联系我们。",
                "category": "联系方式",
                "keywords": ["客服", "联系", "电话", "邮箱", "在线"]
            },
            {
                "id": "faq_003",
                "question": "配送时间需要多久？",
                "answer": "标准配送3-5个工作日，加急配送1-2个工作日，偏远地区可能需要额外1-2天。",
                "category": "配送",
                "keywords": ["配送", "发货", "快递", "时间", "工作日"]
            },
            {
                "id": "faq_004",
                "question": "支持哪些支付方式？",
                "answer": "我们支持支付宝、微信支付、银行卡支付和货到付款等多种支付方式。",
                "category": "支付",
                "keywords": ["支付", "支付宝", "微信", "银行卡", "货到付款"]
            }
        ]

    @property
    def source_name(self) -> str:
        """召回源名称"""
        return "faq"

    async def acquire(self, request: RecallRequest) -> list[RecallHit]:
        """
        执行FAQ召回
        
        Args:
            request: 召回请求
            
        Returns:
            召回命中结果列表
        """
        try:
            query = request.query.lower()
            hits = []

            # 关键词匹配策略
            for faq in self._faq_data:
                score = self._calculate_faq_score(query, faq)

                if score > 0.3:  # 设置最低匹配阈值
                    hit = RecallHit(
                        source=self.source_name,
                        score=score,
                        confidence=min(score * 1.2, 1.0),  # 稍微提高置信度
                        reason=f"FAQ关键词匹配 (匹配度: {score:.3f})",
                        content=f"Q: {faq['question']}\nA: {faq['answer']}",
                        metadata={
                            "faq_id": faq["id"],
                            "question": faq["question"],
                            "answer": faq["answer"],
                            "category": faq["category"],
                            "match_type": "keyword"
                        }
                    )
                    hits.append(hit)

            # 按分数排序
            hits.sort(key=lambda x: x.score, reverse=True)

            # 限制返回数量
            hits = hits[:request.top_k]

            top_score = hits[0].score if hits else 0.0
            logger.info(
                f"FAQ recall: found {len(hits)} results for '{request.query}' "
                f"(top score: {top_score:.3f})"
            )

            return hits

        except Exception as e:
            logger.error(f"FAQ recall failed for '{request.query}': {e}")
            return []

    def _calculate_faq_score(self, query: str, faq: dict[str, Any]) -> float:
        """
        计算FAQ匹配分数
        
        Args:
            query: 查询文本
            faq: FAQ数据
            
        Returns:
            匹配分数 (0-1)
        """
        score = 0.0

        # 1. 问题匹配（权重最高）
        question = faq["question"].lower()
        if any(word in question for word in query.split()):
            score += 0.4

        # 2. 关键词匹配
        keywords = faq["keywords"]
        matched_keywords = sum(1 for keyword in keywords if keyword in query)
        if matched_keywords > 0:
            score += (matched_keywords / len(keywords)) * 0.4

        # 3. 答案内容匹配
        answer = faq["answer"].lower()
        if any(word in answer for word in query.split()):
            score += 0.2

        # 4. 完全匹配奖励
        if query in question or any(keyword in query for keyword in keywords):
            score += 0.2

        return min(score, 1.0)
