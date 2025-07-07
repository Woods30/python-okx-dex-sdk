import asyncio

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import NATIVE_TOKEN_ADDRESS, ChainId, ChainType


async def main():
    """
    演示如何获取不同链上代币的小数位数。
    """
    print("配置加载成功。")
    client = OkxDexClient(settings)

    # --- 测试 EVM 链 (以 BSC 为例) ---
    print("\n--- Testing EVM (BSC) Decimals ---")
    bsc_chain_id = ChainId.BSC
    if bsc_chain_id in settings.chains:
        # 1. 测试原生代币 (BNB)
        bnb_address = NATIVE_TOKEN_ADDRESS[ChainType.EVM]
        # 2. 测试一个 ERC20 代币 (USDC on BSC)
        usdc_on_bsc = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"

        try:
            bnb_decimals = await client.get_token_decimals_from_address(
                chain_id=bsc_chain_id, token_contract_address=bnb_address
            )
            print(f"✅  BNB ({bnb_address}) on BSC decimals: {bnb_decimals}")

            usdc_decimals = await client.get_token_decimals_from_address(
                chain_id=bsc_chain_id, token_contract_address=usdc_on_bsc
            )
            print(f"✅  USDC ({usdc_on_bsc}) on BSC decimals: {usdc_decimals}")

        except Exception as e:
            print(f"❌  Error getting decimals on BSC: {e}")
    else:
        print(f"⚠️  BSC (chain_id='{bsc_chain_id}') not configured in .env, skipping.")

    # --- 测试 Solana 链 ---
    print("\n--- Testing Solana Decimals ---")
    solana_chain_id = ChainId.SOLANA
    if solana_chain_id in settings.chains:
        # 1. 测试原生代币 (SOL)
        sol_address = NATIVE_TOKEN_ADDRESS[ChainType.SOLANA]
        # 2. 测试一个 SPL 代币 (USDC on Solana)
        usdc_on_sol = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

        try:
            sol_decimals = await client.get_token_decimals_from_address(
                chain_id=solana_chain_id, token_contract_address=sol_address
            )
            print(f"✅  SOL ({sol_address}) on Solana decimals: {sol_decimals}")

            usdc_sol_decimals = await client.get_token_decimals_from_address(
                chain_id=solana_chain_id, token_contract_address=usdc_on_sol
            )
            print(f"✅  USDC ({usdc_on_sol}) on Solana decimals: {usdc_sol_decimals}")

        except Exception as e:
            print(f"❌  Error getting decimals on Solana: {e}")
    else:
        print(
            f"⚠️  Solana (chain_id='{solana_chain_id}') not configured in .env, skipping."
        )


if __name__ == "__main__":
    asyncio.run(main())
