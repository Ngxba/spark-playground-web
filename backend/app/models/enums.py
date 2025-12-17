from enum import Enum

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class ConceptTag(str, Enum):
    SHUFFLE = "shuffle"
    GROUPBY = "groupby"
    JOIN = "join"
    BROADCAST = "broadcast"
    AGGREGATION = "aggregation"
    FILTER = "filter"
    OPTIMIZATION = "optimization"
    CACHE = "cache"
    PARTITIONING = "partitioning"
    SKEW = "skew"
