from enum import StrEnum


class ChainType(StrEnum):
    """
    链的通用类型
    """

    EVM = "evm"
    SOLANA = "solana"
    SUI = "sui"
    TRON = "tron"
    TON = "ton"


class ChainId(StrEnum):
    """
    OKX 支持的部分链 ID
    """

    # EVM Chains
    ETHEREUM = "1"
    OKTC = "66"
    BSC = "56"
    POLYGON = "137"
    FANTOM = "250"
    AVALANCHE = "43114"
    ARBITRUM = "42161"
    OPTIMISM = "10"
    BASE = "8453"

    # Solana
    SOLANA = "501"

    # Sui
    SUI = "784"

    # Tron
    TRON = "195"

    # Ton
    TON = "607"


NATIVE_TOKEN_ADDRESS = {
    ChainType.EVM: "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
    ChainType.SOLANA: "11111111111111111111111111111111",
    ChainType.SUI: "0x2::sui::SUI",
    ChainType.TRON: "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb",
    ChainType.TON: "EQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAM9c",
}

# Example usage:
# chain_type = ChainType.EVM
# chain_id = ChainId.ETHEREUM
