"""
Data models for DeFi Llama protocols
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class Protocol:
    """
    Protocol data model from DeFi Llama API
    """

    id: str
    name: str
    category: str
    tvl: float
    symbol: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    chain: Optional[str] = None
    logo: Optional[str] = None
    chains: Optional[List[str]] = None
    change_1h: Optional[float] = None
    change_1d: Optional[float] = None
    change_7d: Optional[float] = None
    slug: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Protocol":
        """
        Create Protocol instance from API response data
        """
        # Handle chains field - prioritize 'chains' array over single 'chain'
        chains = data.get("chains")
        if chains is None:
            # If chains is not available, try to use single chain
            single_chain = data.get("chain")
            if single_chain:
                chains = [single_chain]  # Convert single chain to array
            else:
                chains = []  # Default to empty array
        elif isinstance(chains, str):
            # If chains is a string instead of array, convert it
            chains = [chains]
        elif not isinstance(chains, list):
            # If chains is not a list, convert to empty list
            chains = []

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            category=data.get("category", ""),
            tvl=data.get("tvl", 0.0),
            symbol=data.get("symbol"),
            url=data.get("url"),
            description=data.get("description"),
            chain=data.get("chain"),
            logo=data.get("logo"),
            chains=chains,  # Use processed chains array
            change_1h=data.get("change_1h"),
            change_1d=data.get("change_1d"),
            change_7d=data.get("change_7d"),
            slug=data.get("slug"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Protocol instance to dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "tvl": self.tvl,
            "symbol": self.symbol,
            "url": self.url,
            "description": self.description,
            "chain": self.chain,
            "logo": self.logo,
            "chains": self.chains,
            "change_1h": self.change_1h,
            "change_1d": self.change_1d,
            "change_7d": self.change_7d,
            "slug": self.slug,
        }
