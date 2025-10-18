"""
召回Agent节点实现

实现LangGraph节点：
- prepare_node: 处理请求，加载配置
- fanout_node: 并行调用召回源
- merge_node: 汇总、排序、去重
- fallback_node: 降级处理
- output_node: 组装RecallResult
"""

import asyncio
import logging
import time
from typing import Any

from src.agent.recall.schema import RecallHit, RecallRequest, RecallResult
from src.agent.recall.sources.faq_source import FAQRecallSource
from src.agent.recall.sources.vector_source import VectorRecallSource
from src.core.config import settings

logger = logging.getLogger(__name__)


async def prepare_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    处理请求，加载配置
    
    Args:
        state: 召回状态
        
    Returns:
        更新的状态
    """
    request: RecallRequest = state["request"]

    # 解析召回源配置
    sources = settings.recall_sources
    weights_str = settings.recall_source_weights

    # 解析权重配置
    weights = {}
    if weights_str:
        for item in weights_str.split(","):
            if ":" in item:
                source, weight = item.strip().split(":", 1)
                weights[source] = float(weight)

    # 为未配置的源设置默认权重
    for source in sources:
        if source not in weights:
            weights[source] = 1.0

    # 实验配置处理
    experiment_id = request.experiment_id
    experiment_config = {}

    if settings.recall_experiment_enabled and experiment_id:
        # 预留实验配置接口
        # 根据实验ID调整配置（如不同的召回源组合、权重等）
        logger.info(f"Prepare node: experiment enabled, experiment_id={experiment_id}")

        # 实验配置示例（预留接口）
        if experiment_id == "exp-recall-v2":
            # 实验：启用更多召回源
            experiment_config = {
                "sources": ["vector", "faq", "keyword"],
                "weights": {"vector": 0.6, "faq": 0.3, "keyword": 0.1},
                "timeout_ms": 800,  # 实验允许更长超时
            }
        elif experiment_id == "exp-weight-adjust":
            # 实验：调整权重
            experiment_config = {
                "weights": {"vector": 0.4, "faq": 0.6},
            }

    # 合并基础配置和实验配置
    config = {
        "sources": experiment_config.get("sources", sources),
        "weights": {**weights, **experiment_config.get("weights", {})},
        "timeout_ms": experiment_config.get("timeout_ms", settings.recall_timeout_ms),
        "retry": settings.recall_retry,
        "merge_strategy": settings.recall_merge_strategy,
        "degrade_threshold": settings.recall_degrade_threshold,
        "fallback_enabled": settings.recall_fallback_enabled,
        "experiment_id": experiment_id,
        "experiment_enabled": settings.recall_experiment_enabled,
    }

    logger.info(f"Prepare node: loaded config for sources {sources}")

    return {
        "config": config,
        "start_time": time.time(),
    }


async def fanout_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    并行调用召回源
    
    Args:
        state: 召回状态
        
    Returns:
        更新的状态
    """
    request: RecallRequest = state["request"]
    config = state["config"]
    sources = config["sources"]

    # 创建召回源实例
    source_instances = {}
    if "vector" in sources:
        source_instances["vector"] = VectorRecallSource()
    if "faq" in sources:
        source_instances["faq"] = FAQRecallSource()
    if "keyword" in sources:
        from src.agent.recall.sources.keyword_source import KeywordRecallSource
        source_instances["keyword"] = KeywordRecallSource()

    # 并行调用召回源
    tasks = []
    for source_name in sources:
        if source_name in source_instances:
            task = asyncio.create_task(
                _call_recall_source(source_instances[source_name], request, config)
            )
            tasks.append((source_name, task))

    # 等待所有召回源完成
    results = {}
    for source_name, task in tasks:
        try:
            hits = await asyncio.wait_for(task, timeout=config["timeout_ms"] / 1000)
            results[source_name] = hits
            logger.info(f"Fanout node: {source_name} returned {len(hits)} hits")
        except asyncio.TimeoutError:
            logger.warning(f"Fanout node: {source_name} timed out")
            results[source_name] = []
        except Exception as e:
            logger.error(f"Fanout node: {source_name} failed: {e}")
            results[source_name] = []

    return {"source_results": results}


async def merge_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    汇总、排序、去重
    
    Args:
        state: 召回状态
        
    Returns:
        更新的状态
    """
    source_results = state["source_results"]
    config = state["config"]
    weights = config["weights"]

    # 收集所有召回结果
    all_hits = []
    for source_name, hits in source_results.items():
        weight = weights.get(source_name, 1.0)
        for hit in hits:
            # 应用权重
            weighted_hit = RecallHit(
                source=hit.source,
                score=hit.score * weight,
                confidence=hit.confidence,
                reason=hit.reason,
                content=hit.content,
                metadata={
                    **hit.metadata,
                    "original_score": hit.score,
                    "weight": weight,
                }
            )
            all_hits.append(weighted_hit)

    # 去重（按内容哈希）
    deduplicated_hits = _deduplicate_hits(all_hits)

    # 排序
    sorted_hits = sorted(deduplicated_hits, key=lambda x: x.score, reverse=True)

    # 限制返回数量
    top_hits = sorted_hits[:state["request"].top_k]

    logger.info(
        f"Merge node: merged {len(all_hits)} hits into {len(top_hits)} final results"
    )

    return {"merged_hits": top_hits}


async def fallback_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    降级处理
    
    Args:
        state: 召回状态
        
    Returns:
        更新的状态
    """
    merged_hits = state.get("merged_hits", [])
    config = state["config"]

    # 检查是否需要降级
    needs_fallback = (
        len(merged_hits) == 0 or
        (merged_hits and merged_hits[0].score < config["degrade_threshold"])
    )

    if needs_fallback and config["fallback_enabled"]:
        logger.warning("Fallback node: triggering fallback due to poor results")

        # 创建兜底响应
        fallback_hit = RecallHit(
            source="fallback",
            score=0.1,
            confidence=0.1,
            reason="召回降级：未找到足够相关的结果",
            content="抱歉，我暂时无法找到相关信息。建议您：\n1. 尝试使用不同的关键词\n2. 联系人工客服获取帮助",
            metadata={
                "fallback": True,
                "degrade_reason": "low_score" if merged_hits else "no_results"
            }
        )

        return {
            "merged_hits": [fallback_hit],
            "degraded": True
        }

    return {
        "merged_hits": merged_hits,
        "degraded": False
    }


async def output_node(state: dict[str, Any]) -> dict[str, Any]:
    """
    组装RecallResult
    
    Args:
        state: 召回状态
        
    Returns:
        更新的状态
    """
    request: RecallRequest = state["request"]
    merged_hits = state["merged_hits"]
    degraded = state.get("degraded", False)
    start_time = state["start_time"]

    # 计算耗时
    latency_ms = (time.time() - start_time) * 1000

    # 创建召回结果
    result = RecallResult(
        hits=merged_hits,
        latency_ms=latency_ms,
        degraded=degraded,
        trace_id=request.trace_id,
        experiment_id=request.experiment_id,
    )

    # 记录详细的召回指标
    sources_used = list(set(hit.source for hit in merged_hits))
    avg_score = sum(hit.score for hit in merged_hits) / len(merged_hits) if merged_hits else 0.0
    max_score = merged_hits[0].score if merged_hits else 0.0

    logger.info(
        f"Output node: returning {len(merged_hits)} hits "
        f"(latency: {latency_ms:.1f}ms, degraded: {degraded}, "
        f"sources: {sources_used}, avg_score: {avg_score:.3f}, max_score: {max_score:.3f})"
    )

    # 记录结构化日志（用于监控系统）
    logger.info("召回完成", extra={
        "trace_id": request.trace_id,
        "experiment_id": request.experiment_id,
        "session_id": request.session_id,
        "query": request.query[:100],  # 截断长查询
        "sources": sources_used,
        "hits_count": len(merged_hits),
        "latency_ms": latency_ms,
        "degraded": degraded,
        "avg_score": avg_score,
        "max_score": max_score,
        "top_hit_source": merged_hits[0].source if merged_hits else None,
    })

    return {"result": result}


async def _call_recall_source(source, request: RecallRequest, config: dict[str, Any]) -> list[RecallHit]:
    """
    调用单个召回源（带重试）
    
    Args:
        source: 召回源实例
        request: 召回请求
        config: 配置
        
    Returns:
        召回结果
    """
    retry_count = config["retry"]

    for attempt in range(retry_count + 1):
        try:
            return await source.acquire(request)
        except Exception as e:
            if attempt < retry_count:
                logger.warning(f"Recall source {source.source_name} failed (attempt {attempt + 1}), retrying: {e}")
                await asyncio.sleep(0.1 * (attempt + 1))  # 指数退避
            else:
                logger.error(f"Recall source {source.source_name} failed after {retry_count + 1} attempts: {e}")
                raise


def _deduplicate_hits(hits: list[RecallHit]) -> list[RecallHit]:
    """
    去重召回结果（保留高分）
    
    Args:
        hits: 召回结果列表
        
    Returns:
        去重后的结果列表
    """
    seen_content = {}

    for hit in hits:
        # 使用内容的前100个字符作为去重键
        content_key = hit.content[:100]

        if content_key not in seen_content:
            seen_content[content_key] = hit
        else:
            # 保留分数更高的
            if hit.score > seen_content[content_key].score:
                seen_content[content_key] = hit

    return list(seen_content.values())
