from pymongo import MongoClient, ReplaceOne
from constants.event_map import EVENT_COLLECTION_MAP
import time

# === CẤU HÌNH ===
ANALYTICS_URL = "mongodb://localhost:27017/"
DB_NAME = "borrower_analytics"
INPUT_COLLECTION = "borrowers"
OUTPUT_COLLECTION = "borrowers_detail"

# === KẾT NỐI ===
client = MongoClient(ANALYTICS_URL)
db = client[DB_NAME]
input_coll = db[INPUT_COLLECTION]
output_coll = db[OUTPUT_COLLECTION]

# === VALID EVENT TYPES ===
VALID_EVENTS = set(EVENT_COLLECTION_MAP.keys())
EVENTS_EXCLUDE_BORROW = VALID_EVENTS - {"BORROW"}

# === ĐẾM TỔNG ===
event_counter = {event: 0 for event in EVENTS_EXCLUDE_BORROW}

print(f"START: Reading from `{INPUT_COLLECTION}` → Saving to `{OUTPUT_COLLECTION}`\n")

start_time = time.time()
total_users = input_coll.count_documents({})
processed = 0
valid_users = 0
skipped_contracts = 0

# === XÓA CŨ ===
output_coll.drop()
print(f"Dropped old `{OUTPUT_COLLECTION}`")

# === DUYỆT USER ===
cursor = input_coll.find({}, {"userAddress": 1, "totalActions": 1, "actions": 1})
bulk_ops = []

for doc in cursor:
    user = doc.get("userAddress")
    total_actions = doc.get("totalActions", 0)
    actions = doc.get("actions", [])

    processed += 1

    # === BƯỚC 1: KIỂM TRA BORROW ĐẦU TIÊN (actions[0]) ===
    if not actions or actions[0].get("event_type") != "BORROW":
        # Không có BORROW đầu → bỏ qua
        if processed % 1000 == 0 or processed == total_users:
            print(f"Processed: {processed}/{total_users} | Valid: {valid_users} | Skipped: {skipped_contracts}...", end="\r")
        continue

    first_borrow = actions[0]
    wallet = first_borrow.get("wallet")
    receiver = first_borrow.get("receiver")

    # === KIỂM TRA: wallet != receiver → CONTRACT → BỎ QUA ===
    if wallet and receiver and str(wallet).lower() != str(receiver).lower():
        skipped_contracts += 1
        if processed % 1000 == 0 or processed == total_users:
            print(f"Processed: {processed}/{total_users} | Valid: {valid_users} | Skipped: {skipped_contracts}...", end="\r")
        continue

    # === NGƯỜI DÙNG THẬT → TIẾP TỤC XỬ LÝ ===
    valid_users += 1

    # === TẠO FLOW ===
    flow_events = []
    for act in actions:
        etype = act.get("event_type")
        if etype in VALID_EVENTS:
            flow_events.append(etype)
            if etype != "BORROW":
                event_counter[etype] += 1

    flow_str = " -> ".join(flow_events) if flow_events else "NO_ACTIONS"

    # === TẠO DOC MỚI ===
    detail_doc = {
        "userAddress": user,
        "totalActions": total_actions,
        "flows": flow_str,
        "actionCount": len(flow_events),
        "isEOA": True,
        "createdAt": int(time.time())
    }

    bulk_ops.append(
        ReplaceOne({"userAddress": user}, detail_doc, upsert=True)
    )

    # === CẬP NHẬT LOG ===
    if processed % 1000 == 0 or processed == total_users:
        print(f"Processed: {processed}/{total_users} | Valid: {valid_users} | Skipped: {skipped_contracts}...", end="\r")

# === GHI TOÀN BỘ ===
if bulk_ops:
    result = output_coll.bulk_write(bulk_ops)
    print(f"\nSAVED {len(bulk_ops)} EOA users to `{OUTPUT_COLLECTION}`")

# === IN TỔNG KẾT ===
print(f"\nDONE in {time.time() - start_time:.2f}s")
print(f"Total users processed: {processed}")
print(f"Valid EOA users: {valid_users}")
print(f"Skipped (contract): {skipped_contracts}")
print(f"Output collection: `{OUTPUT_COLLECTION}`\n")

print("EVENT TYPE STATISTICS (from EOA users only):")
print("-" * 60)
for event in sorted(EVENTS_EXCLUDE_BORROW):
    count = event_counter[event]
    print(f"{event:18} : {count:,}")
print("-" * 60)
total_non_borrow = sum(event_counter.values())
print(f"TOTAL NON-BORROW: {total_non_borrow:,}")

client.close()

#PYTHONPATH=. python src/test_borrowers_detail.py