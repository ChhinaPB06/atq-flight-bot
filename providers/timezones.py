"""Pinned IANA rules, independent of runner OS timezone files."""
from functools import lru_cache
from importlib.resources import files
from zoneinfo import ZoneInfo
import tzdata

RULES_VERSION = tzdata.__version__


@lru_cache(maxsize=2)
def airport_zone(iata):
    name = {'YYC': 'America/Edmonton', 'ATQ': 'Asia/Kolkata'}[iata]
    with files('tzdata.zoneinfo').joinpath(*name.split('/')).open('rb') as handle:
        return ZoneInfo.from_file(handle, key=name)
