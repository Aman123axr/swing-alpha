import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

NSE_INDEX_URL = "https://www.nseindia.com/api/equity-stockIndices?index={index}"
NSE_HOME_URL = "https://www.nseindia.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": NSE_HOME_URL,
}


def fetch_nse_index(index: str = "NIFTY 500") -> list[str]:
    session = requests.Session()
    session.headers.update(_HEADERS)

    # NSE requires a cookie from the home page before the API responds
    session.get(NSE_HOME_URL, timeout=15)

    url = NSE_INDEX_URL.format(index=requests.utils.quote(index))
    resp = session.get(url, timeout=20)
    resp.raise_for_status()

    data = resp.json().get("data", [])
    # First row is the index itself — skip it
    symbols = [row["symbol"] for row in data[1:] if row.get("symbol")]
    logger.info("NSE fetch for %s: %d symbols", index, len(symbols))
    return [s + ".NS" if "." not in s else s for s in symbols]


def get_tickers_from_screener(index: Optional[str] = None) -> list[str]:
    return fetch_nse_index(index or "NIFTY 100")
