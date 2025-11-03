# python3 src/tests/test_get_events.py
import os
import json
from pymongo import MongoClient
from os.path import join
from collections import defaultdict

# --- Cấu hình lưu dữ liệu ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = join(SRC_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# --- MongoDB ---
MONGO_URL = (
    "mongodb://etlReader:etl_readerBlockChain341@"
    "178.128.85.210:27017,"
    "104.248.148.66:27017,"
    "103.253.146.224:27017/"
)
DB_NAME = "base_blockchain_etl"
COLLECTION_NAME = "dex_events"  # 👉 DEX events

# --- Cấu hình batch ---
BATCH_SIZE = 200
START_BLOCK = 37401400 #3704400 37300000
END_BLOCK = 37552704 # 37372314 37552704

# --- Danh sách event cần theo dõi ---
TARGET_EVENTS = {
    "SUPPLY",
    "SUPPLYCOLLATERAL",
    "COLLATERALADDED",
    "COLLATERALREMOVED",
}

def fetch_dex_events():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    found_events = defaultdict(list)
    current_block = START_BLOCK

    while current_block < END_BLOCK:
        print(f"\n🔎 Fetching DEX events for blocks {current_block} → {current_block + BATCH_SIZE}")

        # Lấy tất cả các trường
        events_cursor = collection.find(
            {"block_number": {"$gte": current_block, "$lt": current_block + BATCH_SIZE}}
        )

        batch_events = list(events_cursor)
        print(f"  → Number of events: {len(batch_events)}")

        batch_types = set()
        for e in batch_events:
            etype = e.get("event_type", "").upper()
            if etype in TARGET_EVENTS:
                found_events[etype].append(e)
                batch_types.add(etype)

        if batch_types:
            print(f"  ✅ Found DEX event types in this batch: {', '.join(sorted(batch_types))}")
        else:
            print(f"  ⚪ No target DEX events found in this batch.")

        # Lưu ra file mỗi batch
        events_path = join(DATA_DIR, "detected_full_dex_events.json")
        with open(events_path, "w", encoding="utf-8") as f:
            json.dump(found_events, f, indent=4, ensure_ascii=False)

        current_block += BATCH_SIZE

    print("\n📊 Summary of detected DEX event types:")
    for etype, items in found_events.items():
        print(f"  - {etype}: {len(items)} occurrences")

    return found_events


def test_fetch_dex_events():
    found_events = fetch_dex_events()
    assert any(found_events.values()), "No DEX target events found at all!"


if __name__ == "__main__":
    fetch_dex_events()

