import asyncio
from datetime import date

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import ChainId


async def main():
    """
    演示如何使用 get_tokens 方法获取指定链上支持的所有代币信息。
    """
    print("配置加载成功。")

    client = OkxDexClient(settings)

    # 您可以修改为您想要查询的任何EVM或Solana链
    chain_id = ChainId.BSC
    print(f"准备获取链 '{chain_id}' 上的代币价格...")

    try:
        token_price_response = await client.get_historical_price(
            chain_id=chain_id,
            token_contract_address="0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
            target_date=date(2025, 7, 10),
        )
        print(token_price_response)

    except Exception as e:
        print(f"获取代币时发生错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
