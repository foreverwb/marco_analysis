from app.services.parsers.base import BaseParser


class MarketChameleonVolumeParser(BaseParser):
    name = "mc_volume"
    expected_headers = [
        "Symbol",
        "Name",
        "Price",
        "% Chg",
        "Trades",
        "Total Volume",
        "90-Day Avg Volume",
        "Relative Volume to 90-Day Avg",
        "Call Volume",
        "Put Volume",
        "Put %",
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
        "total_volume",
        "avg90_volume",
        "RelVolTo90D",
        "CallVolume",
        "PutVolume",
        "PutPct",
        "SingleLegPct",
        "MultiLegPct",
        "ContingentPct",
    ]
