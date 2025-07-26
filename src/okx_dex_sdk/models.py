from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Chain(BaseModel):
    chain_id: int = Field(..., alias="chainId")
    chain_name: str = Field(..., alias="chainName")
    dex_token_approve_address: str = Field(..., alias="dexTokenApproveAddress")

    model_config = {
        "populate_by_name": True,
    }


class Token(BaseModel):
    decimals: str
    token_contract_address: str = Field(..., alias="tokenContractAddress")
    token_logo_url: str = Field(..., alias="tokenLogoUrl")
    token_name: str = Field(..., alias="tokenName")
    token_symbol: str = Field(..., alias="tokenSymbol")

    model_config = {
        "populate_by_name": True,
    }


class LiquiditySource(BaseModel):
    id: str
    logo: str
    name: str


class OKXResponse(BaseModel):
    code: str
    msg: str


class ChainsResponse(OKXResponse):
    data: List[Chain]


class TokensResponse(OKXResponse):
    data: List[Token]


class LiquiditySourcesResponse(OKXResponse):
    data: List[LiquiditySource]


class ApproveTransaction(BaseModel):
    data: str
    dex_contract_address: str = Field(..., alias="dexContractAddress")
    gas_limit: str = Field(..., alias="gasLimit")
    gas_price: str = Field(..., alias="gasPrice")

    model_config = {
        "populate_by_name": True,
    }


class ApproveResponse(OKXResponse):
    data: List[ApproveTransaction]


class TokenInfo(BaseModel):
    decimal: str
    is_honey_pot: bool = Field(..., alias="isHoneyPot")
    tax_rate: str = Field(..., alias="taxRate")
    token_contract_address: str = Field(..., alias="tokenContractAddress")
    token_symbol: str = Field(..., alias="tokenSymbol")
    token_unit_price: str = Field(..., alias="tokenUnitPrice")

    model_config = {
        "populate_by_name": True,
    }

    @property
    def price(self) -> Decimal:
        """Get token price in USD"""
        return Decimal(self.token_unit_price)


class DexProtocol(BaseModel):
    dex_name: str = Field(..., alias="dexName")
    percent: str

    model_config = {
        "populate_by_name": True,
    }


class SubRouter(BaseModel):
    dex_protocol: List[DexProtocol] = Field(..., alias="dexProtocol")
    from_token: TokenInfo = Field(..., alias="fromToken")
    to_token: TokenInfo = Field(..., alias="toToken")

    model_config = {
        "populate_by_name": True,
    }


class DexRouter(BaseModel):
    router: str
    router_percent: str = Field(..., alias="routerPercent")
    sub_router_list: List[SubRouter] = Field(..., alias="subRouterList")

    model_config = {
        "populate_by_name": True,
    }


class QuoteCompare(BaseModel):
    amount_out: str = Field(..., alias="amountOut")
    dex_logo: str = Field(..., alias="dexLogo")
    dex_name: str = Field(..., alias="dexName")
    trade_fee: str = Field(..., alias="tradeFee")

    model_config = {
        "populate_by_name": True,
    }

    def get_output_amount(self) -> Decimal:
        """Get output amount as Decimal with proper decimals"""
        return Decimal(self.amount_out)

    def get_price(self, input_amount: Decimal) -> Decimal:
        """Calculate price (output per input) for this venue"""
        output_amount = self.get_output_amount()
        if input_amount == 0:
            return Decimal("0")
        return input_amount / output_amount  # Price in terms of input/output


class RouterResult(BaseModel):
    chain_id: str = Field(..., alias="chainId")
    dex_router_list: List[DexRouter] = Field(..., alias="dexRouterList")
    estimate_gas_fee: str = Field(..., alias="estimateGasFee")
    from_token: TokenInfo = Field(..., alias="fromToken")
    from_token_amount: str = Field(..., alias="fromTokenAmount")
    price_impact_pct: Optional[str] = Field(None, alias="priceImpactPercentage")
    quote_compare_list: List[QuoteCompare] = Field(..., alias="quoteCompareList")
    to_token: TokenInfo = Field(..., alias="toToken")
    to_token_amount: str = Field(..., alias="toTokenAmount")
    trade_fee: str = Field(..., alias="tradeFee")
    origin_to_token_amount: Optional[str] = Field(None, alias="originToTokenAmount")

    model_config = {
        "populate_by_name": True,
    }

    @property
    def from_amount_decimal(self) -> Decimal:
        """Get from amount as Decimal"""
        return Decimal(self.from_token_amount) / Decimal(
            10 ** int(self.from_token.decimal)
        )

    @property
    def to_amount_decimal(self) -> Decimal:
        """Get to amount as Decimal"""
        return Decimal(self.to_token_amount) / Decimal(10 ** int(self.to_token.decimal))

    @property
    def execution_price(self) -> Decimal:
        """Calculate execution price (output per input)"""
        if self.to_amount_decimal == 0:
            return Decimal("0")
        return self.to_amount_decimal / self.from_amount_decimal

    @property
    def value_in_usd(self) -> Decimal:
        """Calculate the USD value of the trade"""
        return self.from_amount_decimal * self.from_token.price

    @property
    def price_impact(self) -> Optional[Decimal]:
        """Get price impact as a decimal (if available)"""
        return Decimal(self.price_impact_pct) if self.price_impact_pct else None

    @property
    def best_venue(self) -> QuoteCompare:
        """Get the venue offering the best price"""
        return min(
            self.quote_compare_list, key=lambda x: x.get_price(self.from_amount_decimal)
        )

    def get_venue_prices(self) -> Dict[str, Decimal]:
        """Get a mapping of venue names to their prices (input/output)"""
        return {
            quote.dex_name: quote.get_price(self.from_amount_decimal)
            for quote in self.quote_compare_list
        }

    def get_price_comparison(self) -> str:
        """Get a formatted string comparing prices across venues"""
        prices = self.get_venue_prices()
        if not prices:
            return "No prices available"

        best_price = min(
            prices.values()
        )  # Lower price is better when measuring input/output

        comparison = f"Best price: {best_price:.8f} {self.from_token.token_symbol}/{self.to_token.token_symbol}\n"
        comparison += "Prices by venue:\n"
        for venue, price in sorted(prices.items(), key=lambda x: x[1]):
            diff = ((price / best_price) - 1) * 100
            comparison += f"  {venue}: {price:.8f} ({diff:+.2f}%)\n"
        return comparison


class SwapTransaction(BaseModel):
    data: str
    from_address: str = Field(..., alias="from")
    gas: str
    gas_price: str = Field(..., alias="gasPrice")
    max_priority_fee_per_gas: Optional[str] = Field(None, alias="maxPriorityFeePerGas")
    to: str
    value: str
    min_receive_amount: Optional[str] = Field(None, alias="minReceiveAmount")

    model_config = {
        "populate_by_name": True,
    }


class SwapInfo(BaseModel):
    router_result: RouterResult = Field(..., alias="routerResult")
    tx: SwapTransaction


class SwapResponse(OKXResponse):
    data: List[SwapInfo]


class SwapResult(RouterResult):
    """
    Represents the final result of a swap, combining the quote information
    with the transaction hash of the executed swap.
    """

    tx_hash: str


class QuoteResponse(OKXResponse):
    data: List[RouterResult]

    @property
    def result(self) -> RouterResult:
        """Get the first (and usually only) result"""
        return self.data[0]


class BroadcastTransactionData(BaseModel):
    order_id: str = Field(..., alias="orderId")


class BroadcastTransactionResponse(OKXResponse):
    data: List[BroadcastTransactionData]


class TransactionOrder(BaseModel):
    chain_index: str = Field(..., alias="chainIndex")
    address: str
    account_id: Optional[str] = Field(None, alias="accountId")
    order_id: str = Field(..., alias="orderId")
    tx_status: str = Field(..., alias="txStatus")
    tx_hash: str = Field(..., alias="txHash")

    model_config = {
        "populate_by_name": True,
    }


class TokenBalanceRequestItem(BaseModel):
    """
    Represents an item for the token balance request.
    """

    chain_index: str = Field(..., alias="chainIndex")
    token_contract_address: str = Field(..., alias="tokenContractAddress")

    model_config = {
        "populate_by_name": True,
    }


class TokenAsset(BaseModel):
    """
    Represents the balance details of a specific token asset.
    """

    chain_index: str = Field(..., alias="chainIndex")
    token_contract_address: str = Field(..., alias="tokenContractAddress")
    symbol: str
    balance: str
    token_price: str = Field(..., alias="tokenPrice")
    is_risk_token: bool = Field(..., alias="isRiskToken")
    raw_balance: Optional[str] = Field(None, alias="rawBalance")
    address: str

    model_config = {
        "populate_by_name": True,
    }


class TokenBalancesData(BaseModel):
    """
    Container for a list of token assets in the balance response.
    """

    token_assets: List[TokenAsset] = Field(..., alias="tokenAssets")

    model_config = {
        "populate_by_name": True,
    }


class TokenBalancesResponse(OKXResponse):
    """
    Response model for the get_token_balances API call.
    """

    data: List[TokenBalancesData]


class TransactionOrdersResponse(OKXResponse):
    data: List[TransactionOrder]


class TokenPriceData(BaseModel):
    chain_index: str = Field(..., alias="chainIndex")
    token_contract_address: str = Field(..., alias="tokenContractAddress")
    time: str = Field(..., alias="time")
    price: str = Field(..., alias="price")

    model_config = {
        "populate_by_name": True,
    }


class TokenPriceResponse(BaseModel):
    code: int
    data: TokenPriceData

    @property
    def price(self) -> Decimal:
        """Get token price as Decimal"""
        return Decimal(self.data.price)

    model_config = {
        "populate_by_name": True,
    }


class TokenDetails(BaseModel):
    """代币详情模型"""

    symbol: str
    amount: str
    token_address: str = Field(..., alias="tokenAddress")

    model_config = {
        "populate_by_name": True,
    }


class SwapHistoryData(BaseModel):
    """交易历史数据模型"""

    chain_id: str = Field(..., alias="chainId")
    tx_hash: str = Field(..., alias="txHash")
    height: str
    tx_time: str = Field(..., alias="txTime")
    status: str
    tx_type: str = Field(..., alias="txType")
    from_address: str = Field(..., alias="fromAddress")
    dex_router: str = Field(..., alias="dexRouter")
    to_address: str = Field(..., alias="toAddress")
    from_token_details: TokenDetails = Field(..., alias="fromTokenDetails")
    to_token_details: TokenDetails = Field(..., alias="toTokenDetails")
    referral_amount: str = Field(..., alias="referralAmount")
    error_msg: str = Field(..., alias="errorMsg")
    gas_limit: str = Field(..., alias="gasLimit")
    gas_used: str = Field(..., alias="gasUsed")
    gas_price: str = Field(..., alias="gasPrice")
    tx_fee: str = Field(..., alias="txFee")

    model_config = {
        "populate_by_name": True,
    }

    @property
    def gas_fee(self) -> Decimal:
        """Get gas fee as raw value"""
        return Decimal(self.gas_used) * Decimal(self.gas_price)


class SwapHistoryResponse(OKXResponse):
    """交易历史查询响应模型"""

    data: Optional[SwapHistoryData]
