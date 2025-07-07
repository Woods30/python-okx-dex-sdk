import asyncio
from decimal import Decimal
from pprint import pprint

from okx_dex_sdk.client import OkxDexClient
from okx_dex_sdk.config import settings
from okx_dex_sdk.constants import ChainId


async def main():
    """
    本示例演示如何获取 Solana 链上的交易报价。
    """
    # 配置在导入 `settings` 时已自动加载并验证。
    # 如果配置失败，程序会在执行到这里之前就退出。
    print("配置加载成功。")

    client = OkxDexClient(settings)

    chain_id = ChainId.SOLANA
    from_token = "So11111111111111111111111111111111111111112"  # SOL
    to_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
    amount_to_swap = "0.01"  # 兑换 0.01 SOL

    # 准备：获取支持的代币列表以供后续查询（例如小数位数）
    # 在实际应用中，您应该缓存此信息
    print("正在获取代币列表...")
    await client.get_tokens(chain_id=chain_id)

    # 获取报价 (SOL -> USDC)
    print(f"正在获取 {amount_to_swap} {from_token} -> {to_token} 的报价...")
    quote_params = {
        "chain_id": chain_id,
        "from_token_address": from_token,
        "to_token_address": to_token,
        "amount": amount_to_swap,
    }
    try:
        quote_response = await client.get_quote(**quote_params)
        if quote_response and quote_response.data:
            print("报价成功！")
            # 使用 .result 属性可以方便地访问第一个报价结果
            result = quote_response.result
            print("报价结果详情:")
            pprint(result.model_dump())
            print(
                f"  - 预计可得到: {result.to_amount_decimal:.6f} {result.to_token.token_symbol}"
            )

            # 计算价格 (output/input)，即 1 个源代币可以换多少个目标代币
            print(
                f"  - 价格 (Token): 1 {result.from_token.token_symbol} = {result.execution_price:.6f} {result.to_token.token_symbol}"
            )
            print(f"  - 价格 (USD): ${result.value_in_usd:.4f}")
            print(f"  - 最佳交易所: {result.best_venue.dex_name}")
            print(
                f"  - 最佳交易所价格: {result.best_venue.get_price(result.from_amount_decimal):.6f}"
            )
            print(
                f"  - from token price usd: ${Decimal(result.from_token.token_unit_price):.6f}"
            )
            print(
                f"  - to token price usd: ${Decimal(result.to_token.token_unit_price):.6f}"
            )
            print(f"  - 滑点: {result.price_impact_pct}%")
            print(f"  - 交易手续费: {result.trade_fee}")
        else:
            print(f"获取报价失败: {quote_response.msg}")

    except Exception as e:
        print(f"获取报价时发生错误: {e}")
        return


if __name__ == "__main__":
    asyncio.run(main())
