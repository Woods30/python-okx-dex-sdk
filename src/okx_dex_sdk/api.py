import base64
import hmac
import json
import urllib.parse
from datetime import date, datetime
from typing import Dict, List, Optional

import aiohttp

from .models import (
    ApproveResponse,
    BroadcastTransactionResponse,
    Chain,
    ChainsResponse,
    LiquiditySource,
    LiquiditySourcesResponse,
    QuoteResponse,
    SwapResponse,
    Token,
    TokenBalanceRequestItem,
    TokenBalancesResponse,
    TokenPriceResponse,
    TokensResponse,
    TransactionOrdersResponse,
)


class OKXDexAPI:
    """
    OKX DEX API 客户端，实现了 RESTful API 的认证。
    """

    # API 端点
    SUPPORTED_CHAINS = "api/v5/dex/aggregator/supported/chain"
    ALL_TOKENS = "api/v5/dex/aggregator/all-tokens"
    GET_LIQUIDITY = "api/v5/dex/aggregator/get-liquidity"
    APPROVE_TRANSACTION = "api/v5/dex/aggregator/approve-transaction"
    GET_QUOTE = "api/v5/dex/aggregator/quote"
    SWAP = "api/v5/dex/aggregator/swap"
    GET_TOKEN_BALANCES = "api/v5/dex/balance/token-balances-by-address"
    GET_ALL_TOKEN_BALANCES = "api/v5/dex/balance/all-token-balances-by-address"
    BROADCAST_TRANSACTION = "api/v5/wallet/pre-transaction/broadcast-transaction"
    GET_TRANSACTION_ORDERS = "api/v5/wallet/post-transaction/orders"
    GET_TOKEN_PRICE = "api/v5/dex/market/price"
    GET_HISTORICAL_PRICE = "api/v5/dex/index/historical-price"

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        passphrase: str,
        access_project: Optional[str] = None,
        base_url: str = "https://web3.okx.com",
        http_proxy: Optional[str] = None,
    ):
        """
        初始化 OKX DEX API 客户端。

        Args:
            api_key: OKX 开发者门户申请的 API key。
            secret_key: OKX 开发者门户申请的 Secret key。
            passphrase: 创建 API key 时指定的 passphrase。
            access_project: (可选) 访问项目名称。
            base_url: API 基础 URL，默认为生产环境。
            http_proxy: (可选) 用于请求的 HTTP/HTTPS 代理。
        """
        self.api_key = api_key
        self.secret_key = secret_key.encode()
        self.passphrase = passphrase
        self.access_project = access_project
        self.base_url = base_url.rstrip("/")
        self.http_proxy = http_proxy
        self.tokens: List[Token] = []
        self.liquidity_sources: List[LiquiditySource] = []
        self.chains: List[Chain] = []

    def _generate_signature(
        self, timestamp: str, method: str, request_path: str, body: str = ""
    ) -> str:
        """
        生成 API 认证所需的签名。

        Args:
            timestamp: ISO 格式的时间戳。
            method: HTTP 方法 (GET/POST)。
            request_path: API 端点路径，包含查询参数。
            body: POST 请求的请求体。

        Returns:
            Base64 编码的签名。
        """
        message = timestamp + method + request_path + body
        mac = hmac.new(self.secret_key, message.encode(), digestmod="sha256")
        return base64.b64encode(mac.digest()).decode()

    def _get_timestamp(self) -> str:
        """获取 ISO 格式的时间戳。"""
        return datetime.utcnow().isoformat()[:-3] + "Z"

    def _get_headers(
        self, method: str, request_path: str, body: str = ""
    ) -> Dict[str, str]:
        """
        生成 API 认证所需的请求头。

        Args:
            method: HTTP 方法 (GET/POST)。
            request_path: API 端点路径，包含查询参数。
            body: POST 请求的请求体。

        Returns:
            包含所需请求头的字典。
        """
        timestamp = self._get_timestamp()
        # print(
        #     f"timestamp: {timestamp}, method: {method}, request_path: {request_path}, body: {body}"
        # )
        request_path = request_path.replace("%2C", ",")

        headers = {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": self._generate_signature(
                timestamp, method, request_path, body
            ),
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
        }
        if self.access_project:
            headers["OK-ACCESS-PROJECT"] = self.access_project
        return headers

    async def get(self, path: str, params: Optional[Dict] = None) -> Dict:
        """
        向 API 发送 GET 请求。

        Args:
            path: API 端点路径。
            params: (可选) 查询参数。

        Returns:
            API 响应的字典。
        """
        # 构建包含查询参数的完整请求路径
        request_path = f"/{path}"
        if params:
            query_string = urllib.parse.urlencode(params)
            request_path = f"{request_path}?{query_string}"

        url = f"{self.base_url}{request_path}"
        # 确保将包含查询字符串的完整路径用于签名
        headers = self._get_headers("GET", request_path)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url, headers=headers, proxy=self.http_proxy
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"错误: {response.status} - {await response.text()}")
                        return {
                            "status": response.status,
                            "error": await response.text(),
                        }
            except Exception as e:
                print(f"请求失败: {str(e)}")
                return {"error": str(e)}

    async def post(self, path: str, data: Dict) -> Dict:
        """
        向 API 发送 POST 请求。

        Args:
            path: API 端点路径。
            data: 请求体数据。

        Returns:
            API 响应的字典。
        """
        request_path = f"/{path}"
        url = f"{self.base_url}{request_path}"

        # 将请求体转换为 JSON 字符串
        body = json.dumps(data)
        headers = self._get_headers("POST", request_path, body)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url, headers=headers, json=data, proxy=self.http_proxy
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"错误: {response.status} - {await response.text()}")
                        return {
                            "status": response.status,
                            "error": await response.text(),
                        }
            except Exception as e:
                print(f"请求失败: {str(e)}")
                return {"error": str(e)}

    async def get_supported_chains(self) -> ChainsResponse:
        """
        获取支持单链交易的链列表。

        Returns:
            支持的链及其详细信息列表。
        """
        response = await self.get(self.SUPPORTED_CHAINS)
        chains = ChainsResponse(**response)
        self.chains = chains.data
        return chains

    async def get_tokens(self, chain_id: str) -> TokensResponse:
        """
        获取 OKX 聚合协议中可用于交易的代币列表。

        Args:
            chain_id: 链 ID (例如, "1" 代表以太坊)。

        Returns:
            支持的代币及其详细信息列表。
        """
        params = {"chainId": chain_id}
        response = await self.get(self.ALL_TOKENS, params)
        tokens = TokensResponse(**response)
        self.tokens = tokens.data
        return tokens

    async def get_liquidity_sources(self, chain_id: str) -> LiquiditySourcesResponse:
        """
        获取 OKX 聚合协议中可用的流动性来源。

        Args:
            chain_id: 链 ID (例如, "1" 代表以太坊)。

        Returns:
            流动性来源及其详细信息列表。
        """
        params = {"chainId": chain_id}
        response = await self.get(self.GET_LIQUIDITY, params)
        liquidity_sources = LiquiditySourcesResponse(**response)
        self.liquidity_sources = liquidity_sources.data
        return liquidity_sources

    async def approve_transaction(
        self, chain_id: str, token_contract_address: str, approve_amount: str
    ) -> ApproveResponse:
        """
        为 EVM 链生成授权交易数据。

        Args:
            chain_id: 链 ID (例如, "1" 代表以太坊)。
            token_contract_address: 需要授权的代币合约地址。
            approve_amount: 以最小可分割单位表示的授权数量。

        Returns:
            用于授权的交易数据。
        """
        params = {
            "chainId": chain_id,
            "tokenContractAddress": token_contract_address,
            "approveAmount": approve_amount,
        }
        response = await self.get(self.APPROVE_TRANSACTION, params)
        return ApproveResponse(**response)

    async def get_quote(
        self,
        chain_id: str,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        fee_percent: Optional[str] = None,
    ) -> QuoteResponse:
        """
        获取代币兑换的报价。

        Args:
            chain_id: 链 ID (例如, "1" 代表以太坊)。
            from_token_address: 源代币的合约地址。
            to_token_address: 目标代币的合约地址。
            amount: 兑换数量 (将转换为最小可分割单位)。
            fee_percent: (可选) 交易费率。

        Returns:
            包含价格影响和路由信息的报价。
        """

        params = {
            "chainId": chain_id,
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "amount": amount,
        }
        if fee_percent:
            params["feePercent"] = fee_percent
        response = await self.get(self.GET_QUOTE, params)
        return QuoteResponse(**response)

    async def get_all_token_balances(
        self, address: str, chains: List[str], exclude_risk_token: bool = True
    ) -> TokenBalancesResponse:
        """
        获取指定地址在多个链上的所有代币余额。
        https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-balance-total-token-balances

        Args:
            address: 钱包地址。
            chains: 要查询的链ID列表，将被合并为逗号分隔的字符串。
            exclude_risk_token: 是否排除风险代币，默认为 True。

        Returns:
            所有代币的余额列表。
        """
        params = {
            "address": address,
            "chains": ",".join(chains),
        }
        if not exclude_risk_token:
            params["excludeRiskToken"] = "1"

        response = await self.get(self.GET_ALL_TOKEN_BALANCES, params)
        return TokenBalancesResponse(**response)

    async def get_token_balances(
        self,
        address: str,
        token_contract_addresses: List[TokenBalanceRequestItem],
        exclude_risk_token: bool = True,
    ) -> TokenBalancesResponse:
        """
        获取指定地址下特定代币的余额。
        https://web3.okx.com/zh-hans/build/dev-docs/dex-api/dex-balance-specific-token-balance

        Args:
            address: 钱包地址。
            token_contract_addresses: 要查询的代币和链的列表。

        Returns:
            代币余额列表。
        """
        token_addresses_data = [
            item.model_dump(by_alias=True) for item in token_contract_addresses
        ]

        data = {
            "address": address,
            "tokenContractAddresses": token_addresses_data,
        }
        if not exclude_risk_token:
            data["excludeRiskToken"] = "1"
        response = await self.post(self.GET_TOKEN_BALANCES, data)
        return TokenBalancesResponse(**response)

    async def get_token_price(
        self, chain_id: str, token_contract_address: str
    ) -> TokenPriceResponse:
        """
        获取代币价格。
        """
        params = {
            "chainIndex": chain_id,
            "tokenContractAddress": token_contract_address,
        }
        response = await self.post(self.GET_TOKEN_PRICE, params)
        print(response)
        return TokenPriceResponse(**response)

    async def swap(
        self,
        chain_id: str,
        from_token_address: str,
        to_token_address: str,
        amount: str,
        slippage: str,
        user_wallet_address: str,
    ) -> SwapResponse:
        """
        获取执行兑换所需的交易数据。

        Args:
            chain_id: 链 ID (例如, "1" 代表以太坊)。
            from_token_address: 源代币的合约地址。
            to_token_address: 目标代币的合约地址。
            amount: 兑换数量 (将转换为最小可分割单位)。
            slippage: 最大可接受的滑点 (例如, "0.05" 代表 5%)。
            user_wallet_address: 用户的钱包地址。

        Returns:
            包含交易数据的响应。
        """

        params = {
            "chainId": chain_id,
            "fromTokenAddress": from_token_address,
            "toTokenAddress": to_token_address,
            "amount": amount,
            "slippage": slippage,
            "userWalletAddress": user_wallet_address,
        }
        response = await self.get(self.SWAP, params)
        return SwapResponse(**response)

    async def broadcast_transaction(
        self,
        signed_tx: str,
        chain_index: str,
        address: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> str:
        """
        通过 OKX 广播已签名的交易。

        Args:
            signed_tx: 已签名的交易数据。
            chain_index: 链标识符 (例如 "501" 代表 Solana)。
            address: (可选) 钱包地址。
            account_id: (可选) 账户 ID。

        Returns:
            交易订单 ID。
        """
        data = {
            "signedTx": signed_tx,
            "chainIndex": chain_index,
        }
        if address:
            data["address"] = address
        if account_id:
            data["accountId"] = account_id

        response = await self.post(self.BROADCAST_TRANSACTION, data)
        broadcast_response = BroadcastTransactionResponse(**response)
        return broadcast_response.data[0].order_id

    async def get_transaction_orders(
        self,
        address: Optional[str] = None,
        account_id: Optional[str] = None,
        chain_index: Optional[str] = None,
        tx_status: Optional[str] = None,
        order_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[str] = None,
    ) -> TransactionOrdersResponse:
        """
        从 OKX 获取交易订单列表。

        Args:
            address: 按钱包地址过滤。
            account_id: 按账户 ID 过滤。
            chain_index: 按链索引过滤。
            tx_status: 按状态过滤 (1: 待处理, 2: 成功, 3: 失败)。
            order_id: 按订单 ID 过滤。
            cursor: 分页游标。
            limit: 记录数量 (默认 20, 最大 100)。

        Returns:
            交易订单列表。
        """
        params = {}
        if address:
            params["address"] = address
        if account_id:
            params["accountId"] = account_id
        if chain_index:
            params["chainIndex"] = chain_index
        if tx_status:
            params["txStatus"] = tx_status
        if order_id:
            params["orderId"] = order_id
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit

        response = await self.get(self.GET_TRANSACTION_ORDERS, params)
        return TransactionOrdersResponse(**response)

    async def get_historical_price(
        self, chain_index: str, token_contract_address: str, target_date: date
    ) -> Optional[str]:
        """
        获取指定代币在特定日期的历史收盘价。
        使用OKX GET /api/v5/dex/index/historical-price 接口。
        """
        path = self.GET_HISTORICAL_PRICE

        begin_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())

        begin_ms = str(int(begin_dt.timestamp() * 1000))
        end_ms = str(int(end_dt.timestamp() * 1000))

        params = {
            "chainIndex": chain_index,
            "tokenContractAddress": token_contract_address,
            "begin": begin_ms,
            "end": end_ms,
            "period": "1d",
            "limit": "1",
        }

        response = await self.get(path, params=params)

        if response and response.get("code") == "0" and response.get("data"):
            data_list = response["data"]
            if data_list and data_list[0].get("prices"):
                price_info = data_list[0]["prices"][0]
                price_str = price_info.get("price")
                if price_str:
                    return price_str

        print(
            f"[OKX_DEX] 未能从接口获取 {token_contract_address} 在 {target_date} 的价格。"
        )
        return None
