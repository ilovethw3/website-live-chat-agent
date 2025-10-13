"""
示例数据初始化脚本

上传一些示例知识库数据，用于测试 Agent 功能。
"""

import asyncio
import logging

import httpx

# 配置
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"  # 从环境变量或 .env 读取

# 示例知识库数据
EXAMPLE_DOCUMENTS = [
    {
        "text": "我们的退货政策：收到商品后30天内可申请退货。退货条件：商品未使用且包装完好，保留原始发票，非定制商品。退货运费：商品质量问题由我们承担往返运费，非质量问题由客户承担退货运费。",
        "metadata": {
            "title": "退货政策",
            "url": "https://example.com/return-policy",
            "category": "政策",
        },
    },
    {
        "text": "iPhone 15 价格信息：iPhone 15 128GB 售价 ¥5,999，iPhone 15 256GB 售价 ¥6,999，iPhone 15 512GB 售价 ¥8,499。颜色选择：黑色、白色、蓝色、粉色、黄色。",
        "metadata": {
            "title": "iPhone 15 产品信息",
            "url": "https://example.com/products/iphone-15",
            "category": "产品",
        },
    },
    {
        "text": "配送信息：我们提供全国范围内的免费配送服务。一般情况下，订单在3-5个工作日内送达。特殊地区（如偏远山区）可能需要7-10个工作日。支持顺丰、京东物流等多家快递公司。",
        "metadata": {
            "title": "配送信息",
            "url": "https://example.com/shipping",
            "category": "服务",
        },
    },
    {
        "text": "保修政策：所有产品享有1年免费保修服务。保修期内，因产品质量问题导致的故障，我们提供免费维修或更换服务。人为损坏、进水、摔坏等情况不在保修范围内。",
        "metadata": {
            "title": "保修政策",
            "url": "https://example.com/warranty",
            "category": "政策",
        },
    },
    {
        "text": "支付方式：我们支持多种支付方式，包括微信支付、支付宝、银联卡、信用卡等。所有支付均通过加密通道，保证您的资金安全。支持分期付款服务（3期、6期、12期）。",
        "metadata": {
            "title": "支付方式",
            "url": "https://example.com/payment",
            "category": "服务",
        },
    },
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def upload_knowledge():
    """上传示例知识库"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/knowledge/upsert",
                json={"documents": EXAMPLE_DOCUMENTS},
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=30.0,
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"✅ {result['message']}")
            logger.info(f"📊 插入文档数: {result['inserted_count']}")

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP Error: {e.response.status_code}")
            logger.error(e.response.text)
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")


async def test_search():
    """测试知识库检索"""
    test_queries = [
        "退货政策",
        "iPhone 15 价格",
        "配送多久",
    ]

    async with httpx.AsyncClient() as client:
        for query in test_queries:
            logger.info(f"\n🔍 测试查询: {query}")
            try:
                response = await client.get(
                    f"{API_BASE_URL}/api/v1/knowledge/search",
                    params={"query": query, "top_k": 2},
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    timeout=10.0,
                )

                response.raise_for_status()
                result = response.json()

                logger.info(f"📊 找到 {result['total_results']} 个结果:")
                for i, r in enumerate(result["results"], 1):
                    logger.info(f"  {i}. {r['metadata'].get('title')} (分数: {r['score']:.2f})")

            except Exception as e:
                logger.error(f"❌ Search failed: {e}")


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("📦 初始化示例知识库数据")
    logger.info("=" * 50)

    # 上传知识库
    await upload_knowledge()

    # 等待索引生效
    logger.info("\n⏳ 等待 Milvus 索引生效...")
    await asyncio.sleep(2)

    # 测试检索
    await test_search()

    logger.info("\n" + "=" * 50)
    logger.info("✅ 初始化完成！")
    logger.info("=" * 50)
    logger.info("\n💡 现在可以测试 Chat API:")
    logger.info(f"   curl -X POST {API_BASE_URL}/v1/chat/completions \\")
    logger.info(f'     -H "Authorization: Bearer {API_KEY}" \\')
    logger.info('     -H "Content-Type: application/json" \\')
    logger.info("     -d '{")
    logger.info('       \"model\": \"deepseek-chat\",')
    logger.info('       \"messages\": [{\"role\": \"user\", \"content\": \"你们的退货政策是什么？\"}]')
    logger.info("     }'\n")


if __name__ == "__main__":
    asyncio.run(main())

