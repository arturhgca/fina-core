from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict

import yaml
from pandas import DataFrame


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


class PortfolioConfig:
    def __init__(self, file_path: str):
        self.wallets: Dict[str, Wallet] = {}
        self._parse_allocations_file(file_path)
        self.df: DataFrame = DataFrame()
        self.flatten()

    def flatten(self):
        list_of_dicts = [
            {'symbol': item.symbol,
             'allocation': item.allocation * wallet.allocation,
             'currency': item.currency,
             'wallet': wallet.name}
            for wallet in self.wallets.values()
            for item in wallet.items.values()
        ]
        self.df = DataFrame(list_of_dicts, columns=['symbol', 'allocation', 'currency', 'wallet'])
        self.df = self.df.set_index('symbol')

    def _parse_allocations_file(self, file_path: str):
        raw_portfolio = yaml.full_load(open(file_path))
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
            self.wallets[wallet_name] = wallet
