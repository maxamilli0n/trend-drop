import random
from typing import List
from pytrends.request import TrendReq

SEED_TOPICS = [
    "desk lamp","pickleball paddle","massage gun","wireless charger",
    "rgb lamp","pet hair trimmer","mechanical keyboard","bike light",
    "cordless vacuum","air fryer","smart light strip","portable monitor"
]

def clean_topic(t: str) -> str:
    t = t.strip()
    bad = ["vs","score","how to","meaning","lyrics","who is","age","net worth"]
    if any(b in t.lower() for b in bad): 
        return ""
    return t

def top_topics(limit: int = 8, geo: str = "US") -> List[str]:
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        df = pytrends.trending_searches(pn='united_states' if geo.upper()=="US" else 'united_kingdom')
        topics = [clean_topic(x) for x in df[0].tolist()]
        topics = [x for x in topics if x]
        if not topics:
            topics = SEED_TOPICS[:]
    except Exception:
        topics = SEED_TOPICS[:]
    random.shuffle(topics)
    return topics[:limit]
