#!/usr/bin/env python3
"""
查询交易状态示例

这个示例演示如何使用 OKX DEX SDK 查询交易状态。
"""

import asyncio
from pprint import pprint

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings


async def main():
    """主函数"""
    client = OkxDexClient(settings)

    # 示例参数
    chain_index = "501"  # Ethereum 链
    tx_hash = "4noBEDmkPs4vnyjYkEDsZ5TdLtYRxQR2HUA7ihNaw7HLcNadLcDRAb59N2WwA5pCWwnCuya9Jk3f3BcGmRVSwzRD"  # 示例交易哈希

    try:
        print(f"正在查询交易状态...")
        print(f"链索引: {chain_index}")
        print(f"交易哈希: {tx_hash}")
        print("-" * 50)

        # 查询交易状态
        response = await client.get_swap_history(
            chain_id=chain_index,
            tx_hash=tx_hash,
            is_from_my_project=False,  # 可选：只查询来自当前API Key的订单
        )
        pprint(response)

        if response.code == "0":
            data = response.data
            print("✅ 查询成功!")
            print(f"交易状态: {data.status}")
            print(f"交易类型: {data.tx_type}")
            print(f"区块高度: {data.height}")
            print(f"交易时间: {data.tx_time}")
            print(f"发送地址: {data.from_address}")
            print(f"接收地址: {data.to_address}")
            print(f"DEX路由器: {data.dex_router}")
            print(f"手续费: {data.tx_fee}")

            if data.gas_used:
                print(f"Gas消耗: {data.gas_used}")
            if data.gas_price:
                print(f"Gas价格: {data.gas_price}")

            print("\n📊 交易详情:")
            print(f"源代币: {data.from_token_details.symbol}")
            print(f"源代币数量: {data.from_token_details.amount}")
            print(f"源代币地址: {data.from_token_details.token_address}")

            print(f"目标代币: {data.to_token_details.symbol}")
            print(f"目标代币数量: {data.to_token_details.amount}")
            print(f"目标代币地址: {data.to_token_details.token_address}")

            if data.referral_amount:
                print(f"分佣金额: {data.referral_amount}")

            if data.error_msg:
                print(f"错误信息: {data.error_msg}")

        else:
            print(f"❌ 查询失败: {response.msg}")

    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
