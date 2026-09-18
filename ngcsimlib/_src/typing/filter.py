from typing import TypeAlias, Dict, List
from .contextObject import ContextObject
from enum import Enum


QueryResult: TypeAlias = ContextObject | None
FilterResult: TypeAlias = Dict[str, QueryResult] | List[QueryResult] | QueryResult

class FilterResultFormat(Enum):
    DICT = "DICT"
    LIST = "LIST"
    SINGLE = "SINGLE"


