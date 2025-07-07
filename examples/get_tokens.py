import asyncio

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
    print(f"准备获取链 '{chain_id}' 上的代币列表...")

    try:
        # get_tokens 方法会返回一个包含 Token 对象的列表
        # 该方法也会将结果缓存到 client.api.tokens 中
        tokens_response = await client.get_tokens(chain_id=chain_id)

        if tokens_response and tokens_response.data:
            tokens_list = tokens_response.data
            print(f"成功获取到 {len(tokens_list)} 个代币。")
            print("部分代币信息展示 (前5个):")

            for i, token in enumerate(tokens_list[:5]):
                print(
                    f"  {i+1}. {token.token_symbol:<8} "
                    f"({token.token_name}) - "
                    f"地址: {token.token_contract_address}"
                )
        else:
            print(
                f"获取代币列表失败: {tokens_response.msg if tokens_response else '无响应'}"
            )

    except Exception as e:
        print(f"获取代币时发生错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
