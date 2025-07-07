from typing import Literal

from .constants import ChainType


def get_wallet_address(chain: ChainType, private_key: str) -> str:
    """
    根据私钥和链类型派生钱包地址。

    Args:
        chain: 链类型枚举 (ChainType.EVM 或 ChainType.SOLANA)。
        private_key: 相应的私钥。对于 EVM，是十六进制字符串；对于 Solana，是 base58 字符串。

    Returns:
        钱包地址字符串。
    """
    if chain == ChainType.EVM:
        from web3 import Web3

        account = Web3().eth.account.from_key(private_key)
        return account.address
    elif chain == ChainType.SOLANA:
        from base58 import b58decode
        from solders.keypair import Keypair

        return str(Keypair.from_bytes(b58decode(private_key)).pubkey())
    else:
        raise ValueError(f"不支持的链类型: {chain}")
