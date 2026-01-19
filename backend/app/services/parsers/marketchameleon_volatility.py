from app.services.parsers.base import BaseParser


class MarketChameleonVolatilityParser(BaseParser):
    name = "mc_volatility"
    expected_headers = [
        "Symbol",
        "Name",
        "Stock Price",
        "% Chg",
        "Market Cap",
        "Current IV30",
        "Volatility % Chg",
        "20-Day Historical Vol",
        "1-Year Historical Vol",
        "IV30 % Rank",
        "IV30 52-Week Position",
        "Current Option Volume",
        "Open Interest % Rank",
        "Earnings",
    ]
    column_order = [
        "symbol",
        "name",
        "stock_price",
        "PriceChgPct",
        "market_cap",
        "IV30",
        "IV30ChgPct",
        "HV20",
        "HV1Y",
        "IVR",
        "IV_52W_P",
        "Volume",
        "OI_PctRank",
        "Earnings",
    ]
