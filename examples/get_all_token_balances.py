import asyncio
from pprint import pprint

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import ChainId


async def main():
    """
    本示例演示如何获取一个地址在多个链上的所有资产明细。
    """
    print("配置加载成功。")
    client = OkxDexClient(settings)

    # 您可以替换成自己的地址
    # 注意：为了演示，我们这里使用同一个地址，但实际应用中，
    # 不同链的地址格式可能不同。OKX API 支持传入任意格式的地址。
    address_to_query = "0xc04e9f61091c0f6ea7c4c1d1ac5c4e9b3f68fb09"

    # 要查询的链ID列表
    chains_to_query = [
        str(ChainId.ETHEREUM.value),
        str(ChainId.BSC.value),
    ]

    print(f"\n--- 正在查询地址 {address_to_query} 在 Solana 和 Base 链上的所有资产 ---")

    try:
        response = await client.api.get_all_token_balances(
            address=address_to_query,
            chains=chains_to_query,
            exclude_risk_token=True,
        )

        if response.code == "0" and response.data:
            print(f"成功获取地址 {address_to_query} 的资产明-细:")
            total_value = 0.0
            for chain_data in response.data:
                for asset in chain_data.token_assets:
                    print(f"  - 链: {asset.chain_index}")
                    print(f"    - 代币: {asset.symbol.upper()}")
                    print(f"    - 余额: {asset.balance}")
                    print(f"    - 美元单价: ${asset.token_price}")
                    # 计算并累计总价值
                    try:
                        value = float(asset.balance) * float(asset.token_price)
                        total_value += value
                        print(f"    - 美元总值: ${value:.4f}")
                    except ValueError:
                        print("    - 无法计算美元总值")

            print(f"\n--- 预估总资产价值: ${total_value:.4f} ---")

        else:
            print(f"获取资产明细失败: {response.msg}")
            pprint(response.model_dump())

    except Exception as e:
        print(f"查询资产明细时发生错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
