import asyncio
import traceback

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import NATIVE_TOKEN_ADDRESS, ChainId, ChainType
from okx_dex_sdk.utils import get_wallet_address


async def main():
    # 配置在导入 `settings` 时已自动加载并验证。
    print("配置加载成功。")

    client = OkxDexClient(settings)

    chain_id = ChainId.BSC

    # 检查 EVM 配置
    if chain_id not in settings.chains:
        print(f"请在 .env 文件中配置 chain_id='{chain_id}' 的 RPC 和私钥")
        print(
            f"例如: CHAINS__{chain_id}__RPC_URL=https://mainnet.base.org 和 CHAINS__{chain_id}__PRIVATE_KEY=..."
        )
        return

    wallet_address = get_wallet_address(
        ChainType.EVM, settings.chains[chain_id].private_key
    )
    print(f"使用钱包地址: {wallet_address}")

    to_token_address = NATIVE_TOKEN_ADDRESS[ChainType.EVM]  # BNB on BSC
    from_token_address = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"  # USDC on BSC
    amount_to_swap = "0.6409"  # 兑换 0.001 BNB
    from_token_decimals = 18  # BNB 的小数位数为 18

    print(
        f"准备从 {from_token_address} (Decimals: {from_token_decimals}) "
        f"兑换到 {to_token_address}"
    )

    # 1. 获取报价 (BNB -> USDC)
    # 由于我们已知 BNB 的小数位数，可以直接传入 from_token_decimals，无需先调用 get_tokens
    print("\n1. 正在获取报价...")
    quote_response = await client.get_quote(
        chain_id=chain_id,
        from_token_address=from_token_address,
        to_token_address=to_token_address,
        amount=amount_to_swap,
    )
    if quote_response and quote_response.data:
        print("   报价成功！")
        result = quote_response.result
        print("   报价结果详情:")
        print(
            f"     - 预计可得到: {result.to_amount_decimal:.6f} {result.to_token.token_symbol}"
        )
        print(
            f"     - 价格: 1 {result.from_token.token_symbol} = {result.execution_price:.6f} {result.to_token.token_symbol}"
        )
        print(f"     - 美金价值: ${result.value_in_usd:.4f}")
    else:
        print(
            f"   获取报价失败: {quote_response.msg if quote_response else 'No response'}"
        )
        return


if __name__ == "__main__":
    asyncio.run(main())
