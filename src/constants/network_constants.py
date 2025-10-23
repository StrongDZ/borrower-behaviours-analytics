class NetworkType:
    ETH = "ethereum"
    BASE = "base"


class Chains:
    ETH = "0x1"
    BASE = "0x2105"

    network_mapping: dict[str, str] = {ETH: NetworkType.ETH, BASE: NetworkType.BASE}

    mapping: dict[str, str] = {NetworkType.ETH: ETH, NetworkType.BASE: BASE}
