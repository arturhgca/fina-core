from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

import yaml


@dataclass
class AllocationMixin:
    allocation: Decimal


@dataclass
class Item(AllocationMixin):
    currency: str
    symbol: str


@dataclass
class Wallet(AllocationMixin):
    items: Dict[str, Item]
    name: str


@dataclass
class ItemView(AllocationMixin):
    currency: str
    symbol: str
    wallet: str


@dataclass
class Portfolio:
    wallets: Dict[str, Wallet]

    def flatten(self) -> List[ItemView]:
        return [
            ItemView(symbol=item.symbol,
                     allocation=item.allocation * wallet.allocation,
                     currency=item.currency,
                     wallet=wallet.name)
            for wallet in self.wallets.values()
            for item in wallet.items.values()
        ]

    @classmethod
    def load(cls, file_path: str) -> Portfolio:
        raw_portfolio = yaml.full_load(open(file_path))
        wallets = {}
        for wallet_name, wallet_attributes in raw_portfolio.items():
            items = {}
            for item_symbol, item_attributes in wallet_attributes['items'].items():
                item = Item(symbol=item_symbol,
                            allocation=item_attributes['allocation'],
                            currency=item_attributes['currency'])
                items[item_symbol] = item
            wallet = Wallet(name=wallet_name,
                            allocation=wallet_attributes['allocation'],
                            items=items)
            wallets[wallet_name] = wallet
        return cls(wallets=wallets)
