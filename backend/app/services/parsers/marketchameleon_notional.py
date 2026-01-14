from app.services.parsers.base import BaseParser


class MarketChameleonNotionalParser(BaseParser):
    name = "mc_notional"
    expected_headers = [
        "Symbol",
        "Name",
        "Price",
        "% Chg",
        "Trades",
        "Total $ Notional",
        "90-Day Avg $ Notional",
        "Relative Notional to 90-Day Avg",
        "Call $ Notional",
        "Put $ Notional",
        "% Single-Leg",
        "% Multi Leg",
        "% Contingent",
    ]
    column_order = [
        "symbol",
        "name",
        "price",
        "PriceChgPct",
        "trade_count",
        "total_notional",
        "avg90_notional",
        "RelNotionalTo90D",
        "CallNotional",
        "PutNotional",
        "SingleLegPct",
        "MultiLegPct",
        "ContingentPct",
    ]
