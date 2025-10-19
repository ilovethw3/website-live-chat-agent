"""
关键词召回源适配器

实现基于关键词/规则的召回，支持分词、同义词匹配、正则表达式等策略。
"""

import logging
import re
from typing import Any

from src.agent.recall.schema import RecallHit, RecallRequest
from src.agent.recall.sources.base import RecallSource

logger = logging.getLogger(__name__)


class KeywordRecallSource(RecallSource):
    """关键词召回源适配器"""

    def __init__(self):
        # 关键词规则库（实际项目中可能从数据库或配置文件加载）
        self._keyword_rules = [
            {
                "id": "rule_001",
                "keywords": ["价格", "多少钱", "费用", "收费", "成本"],
                "content": "我们的产品价格信息：\n- 基础版：¥99/月\n- 专业版：¥299/月\n- 企业版：¥999/月\n\n具体价格请咨询销售团队。",
                "category": "价格咨询",
                "priority": 0.9,
                "patterns": [r"价格|多少钱|费用|收费|成本"]
            },
            {
                "id": "rule_002",
                "keywords": ["技术支持", "帮助", "问题", "故障", "bug"],
                "content": "技术支持服务：\n- 工作时间：周一至周五 9:00-18:00\n- 联系方式：support@example.com\n- 在线客服：7x24小时\n- 响应时间：2小时内",
                "category": "技术支持",
                "priority": 0.8,
                "patterns": [r"技术支持|帮助|问题|故障|bug"]
            },
            {
                "id": "rule_003",
                "keywords": ["登录", "密码", "账号", "注册", "认证"],
                "content": "账号相关服务：\n- 忘记密码：点击登录页面的'忘记密码'链接\n- 账号注册：访问注册页面完成注册\n- 账号安全：建议定期更换密码\n- 多因素认证：支持短信和邮箱验证",
                "category": "账号管理",
                "priority": 0.7,
                "patterns": [r"登录|密码|账号|注册|认证"]
            },
            {
                "id": "rule_004",
                "keywords": ["API", "接口", "开发", "文档", "SDK"],
                "content": "开发者资源：\n- API文档：https://docs.example.com/api\n- SDK下载：支持Python、Java、Node.js\n- 开发者社区：https://dev.example.com\n- 技术支持：dev-support@example.com",
                "category": "开发者",
                "priority": 0.6,
                "patterns": [r"API|接口|开发|文档|SDK"]
            }
        ]

        # 同义词映射
        self._synonyms = {
            "价格": ["费用", "收费", "成本", "价钱"],
            "帮助": ["支持", "协助", "指导"],
            "问题": ["故障", "错误", "bug", "异常"],
            "登录": ["登入", "进入", "访问"],
            "API": ["接口", "服务", "端点"]
        }

    @property
    def source_name(self) -> str:
        """召回源名称"""
        return "keyword"

    async def acquire(self, request: RecallRequest) -> list[RecallHit]:
        """
        执行关键词召回

        Args:
            request: 召回请求

        Returns:
            召回命中结果列表
        """
        try:
            query = request.query.lower()
            hits = []

            # 关键词匹配策略
            for rule in self._keyword_rules:
                score = self._calculate_keyword_score(query, rule)

                if score > 0.3:  # 设置最低匹配阈值
                    hit = RecallHit(
                        source=self.source_name,
                        score=score,
                        confidence=min(score * 1.1, 1.0),  # 稍微提高置信度
                        reason=f"关键词规则匹配 (规则: {rule['id']}, 匹配度: {score:.3f})",
                        content=rule["content"],
                        metadata={
                            "rule_id": rule["id"],
                            "category": rule["category"],
                            "priority": rule["priority"],
                            "keywords": rule["keywords"],
                            "match_type": "keyword_rule"
                        }
                    )
                    hits.append(hit)

            # 按分数排序
            hits.sort(key=lambda x: x.score, reverse=True)

            # 限制返回数量
            hits = hits[:request.top_k]

            top_score = hits[0].score if hits else 0.0
            logger.info(
                f"Keyword recall: found {len(hits)} results for '{request.query}' "
                f"(top score: {top_score:.3f})"
            )

            return hits

        except Exception as e:
            logger.error(f"Keyword recall failed for '{request.query}': {e}")
            return []

    def _calculate_keyword_score(self, query: str, rule: dict[str, Any]) -> float:
        """
        计算关键词匹配分数

        Args:
            query: 查询文本
            rule: 规则配置

        Returns:
            匹配分数 (0-1)
        """
        score = 0.0

        # 1. 直接关键词匹配
        keywords = rule["keywords"]
        matched_keywords = sum(1 for keyword in keywords if keyword in query)
        if matched_keywords > 0:
            score += (matched_keywords / len(keywords)) * 0.4

        # 2. 正则表达式匹配
        patterns = rule.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, query, re.IGNORECASE):
                score += 0.3
                break

        # 3. 同义词匹配
        synonym_matches = 0
        for keyword in keywords:
            if keyword in self._synonyms:
                synonyms = self._synonyms[keyword]
                if any(syn in query for syn in synonyms):
                    synonym_matches += 1

        if synonym_matches > 0:
            score += (synonym_matches / len(keywords)) * 0.2

        # 4. 规则优先级加权
        priority = rule.get("priority", 0.5)
        score *= priority

        # 5. 完全匹配奖励
        if any(keyword in query for keyword in keywords):
            score += 0.1

        return min(score, 1.0)
