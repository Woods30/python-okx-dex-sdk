import asyncio
from pprint import pprint

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import ChainId
from okx_dex_sdk.models import TokenBalanceRequestItem


async def main():
    """
    本示例演示如何获取给定地址的特定代币余额。
    """
    print("配置加载成功。")
    client = OkxDexClient(settings)

    # --- Solana 示例 ---
    print("\n--- 正在查询 Solana 链上的余额 ---")
    # 您可以替换成自己的 Solana 地址
    solana_address = "8z9oPDBPU6iMhkqisS4cDAmx878p9Yd6Uth5eCHsZg9b"

    # 要查询的 Solana 代币列表
    # 1. SOL (原生代币, tokenContractAddress 留空)
    # 2. USDC (代币地址: EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v)
    tokens_to_query_solana = [
        TokenBalanceRequestItem(
            chain_index=str(ChainId.SOLANA.value),
            token_contract_address="",
        ),
        TokenBalanceRequestItem(
            chain_index=str(ChainId.SOLANA.value),
            token_contract_address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        ),
    ]

    try:
        balance_response = await client.api.get_token_balances(
            address=solana_address,
            token_contract_addresses=tokens_to_query_solana,
        )

        if balance_response.code == "0" and balance_response.data:
            print(f"成功获取地址 {solana_address} 的余额:")
            for balance_data in balance_response.data:
                for asset in balance_data.token_assets:
                    print(f"  - 代币: {asset.symbol.upper()}")
                    print(f"    - 余额: {asset.balance}")
                    print(f"    - 美元单价: ${asset.token_price}")
                    print(f"    - 是否为风险代币: {asset.is_risk_token}")
        else:
            print(f"获取余额失败: {balance_response.msg}")
            pprint(balance_response.model_dump())

    except Exception as e:
        print(f"查询余额时发生错误: {e}")

    # --- EVM 链 (以 Base 为例) 示例 ---
    print("\n--- 正在查询 Base 链上的余额 ---")
    if ChainId.BASE in settings.chains and settings.chains[ChainId.BASE].private_key:
        from okx_dex_sdk.constants import ChainType
        from okx_dex_sdk.utils import get_wallet_address

        base_address = get_wallet_address(
            ChainType.EVM, settings.chains[ChainId.BASE].private_key
        )
        print(f"使用 .env 文件中配置的私钥派生出地址: {base_address}")

        # 要查询的 Base 链代币列表
        # 1. ETH (原生代币)
        # 2. USDC (地址: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
        tokens_to_query_base = [
            TokenBalanceRequestItem(
                chain_index=str(ChainId.BASE.value),
                token_contract_address="",
            ),
            TokenBalanceRequestItem(
                chain_index=str(ChainId.BASE.value),
                token_contract_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            ),
        ]

        try:
            balance_response_base = await client.api.get_token_balances(
                address=base_address,
                token_contract_addresses=tokens_to_query_base,
                exclude_risk_token=False,  # 示例：不排除风险代币
            )

            if balance_response_base.code == "0" and balance_response_base.data:
                print(f"成功获取地址 {base_address} 的余额:")
                for balance_data in balance_response_base.data:
                    for asset in balance_data.token_assets:
                        print(f"  - 代币: {asset.symbol.upper()}")
                        print(f"    - 余额: {asset.balance}")
                        print(f"    - 美元单价: ${asset.token_price}")
            else:
                print(f"获取余额失败: {balance_response_base.msg}")
                pprint(balance_response_base.model_dump())

        except Exception as e:
            print(f"查询余额时发生错误: {e}")

    else:
        print("Base 链未在 .env 文件中配置私钥，跳过该示例。")


if __name__ == "__main__":
    asyncio.run(main())
