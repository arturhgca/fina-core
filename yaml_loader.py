import datetime
from argparse import ArgumentParser, Namespace

import yaml
from sqlalchemy import exists
from sqlalchemy.orm import Session

import wallet
from config.db import SessionLocal

db: Session = SessionLocal()


def main():
    args = parse_args()
    allocations = load_yaml(args.allocations)
    operations = load_yaml(args.operations)
    load_allocations(allocations)
    load_operations(operations)


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        '--allocations',
        type=str,
        required=True
    )
    parser.add_argument(
        '--operations',
        type=str,
        required=True
    )
    return parser.parse_args()


def load_yaml(file_path: str) -> dict:
    with open(file_path) as file:
        return yaml.full_load(file.read())


def load_allocations(allocations_map: dict):
    for region, region_attributes in allocations_map['regions'].items():
        region_record = _create_region(region, region_attributes)
        db.commit()
        for category, category_attributes in region_attributes['categories'].items():
            category_record = _create_category(category, category_attributes, region_record)
            db.commit()
            for asset, asset_attributes in category_attributes['assets'].items():
                _create_asset(asset, asset_attributes, category_record, region)
            db.commit()


def _create_region(region: str, region_attributes: dict) -> wallet.Region:
    region_record = wallet.Region()
    region_record.iso_code = region
    region_record.allocation = region_attributes['allocation']
    db.add(region_record)
    return region_record


def _create_category(category: str, category_attributes: dict, region_record: wallet.Region) -> wallet.Category:
    category_record = wallet.Category()
    category_record.name = category
    category_record.allocation = category_attributes['allocation']
    category_record.region = region_record
    db.add(category_record)
    return category_record


def _create_asset(asset: str, asset_attributes: dict, category_record: wallet.Category, region: str):
    asset_record = wallet.Asset()
    asset_record.symbol = asset
    asset_record.allocation = asset_attributes['allocation']
    asset_record.country_iso_code = region
    asset_record.category = category_record
    db.add(asset_record)


def load_operations(operations_map: dict):
    for exchange in operations_map['currency_exchanges']:
        _create_currency_exchange(exchange)
    db.commit()
    for operation in operations_map['operations']:
        _create_operation(operation)
    db.commit()


def _create_currency_exchange(exchange):
    exchange_record = wallet.CurrencyExchange()
    exchange_record.name = exchange['name']
    exchange_record.source_currency = exchange['source_currency']
    exchange_record.target_currency = exchange['target_currency']
    exchange_record.exchange_rate_cents = exchange['exchange_rate'] * 100
    exchange_record.timestamp = datetime.datetime.strptime(exchange['date'], '%d/%m/%Y')
    db.add(exchange_record)


def _create_operation(operation: dict):
    operation_record = wallet.Operation()
    operation_record.timestamp = datetime.datetime.strptime(operation['date'], '%d/%m/%Y')
    operation_record.quantity_cents = operation['quantity'] * 100
    operation_record.unit_price_cents = operation['unit_price'] * 100
    operation_record.cost_cents = operation['cost'] * 100
    operation_record.asset = db.query(wallet.Asset).filter(wallet.Asset.symbol == operation['symbol']).first()
    operation_record.broker = _get_broker(operation)
    if 'currency_exchange' in operation:
        currency_exchange = db.query(wallet.CurrencyExchange).filter(
            wallet.CurrencyExchange.name == operation['exchange']).first()
        operation_record.currency_exchange = currency_exchange
    db.add(operation_record)


def _get_broker(operation):
    if not _broker_exists(broker=operation['broker']):
        _create_broker(operation)
        db.commit()
    return db.query(wallet.Broker).filter(wallet.Broker.name == operation['broker']).first()


def _broker_exists(broker: str) -> bool:
    return db.query(exists().where(wallet.Broker.name == broker)).scalar()


def _create_broker(operation: dict):
    broker_record = wallet.Broker()
    broker_record.name = operation['broker']
    broker_record.country_iso_code = operation['currency'][0:2]
    db.add(broker_record)


if __name__ == '__main__':
    main()
