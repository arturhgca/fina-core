from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict

import yaml
from pandas import DataFrame, read_csv, Series


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


class Portfolio:
    MAIN_CURRENCY = 'BRL'

    def __init__(self, config_file_path: str, ledger_file_path: str, currency_exchanges_file_path: str):
        self.config: PortfolioConfig = PortfolioConfig(file_path=config_file_path)
        self.ledger: DataFrame = read_csv(ledger_file_path)
        self.currency_exchanges: DataFrame = read_csv(currency_exchanges_file_path)
        self.currency_exchanges = self.currency_exchanges.set_index('name')

    def calculate_balance(self) -> DataFrame:
        df = DataFrame(columns=[
            'symbol',
            'avg_price',
            'target',
            'holding',
            # 'current_price',
            # 'gain',
            # 'current_percent',
            # 'to_invest_percent',
            # 'total_current_value',
            # 'to_invest',
            # 'units_to_buy'
        ])
        df = df.set_index('symbol')

        symbols = self.config.df.index.tolist()
        for symbol in symbols:
            target = self.config.df['allocation'][symbol]
            operations = self.ledger.loc[self.ledger['symbol'] == symbol]
            total_prices = Series(operations['quantity'] * operations['unit_price'])
            if self.config.df['currency'][symbol] != self.MAIN_CURRENCY and not total_prices.empty:
                exchanges = operations['currency_exchange'].values
                rates = self.currency_exchanges['exchange_rate'][exchanges].values
                total_prices = total_prices.multiply(rates)
            total_price = total_prices.sum()
            holding = operations['quantity'].sum()
            avg_price = total_price / holding
            df.loc[symbol] = [avg_price, target, holding]

        return df
