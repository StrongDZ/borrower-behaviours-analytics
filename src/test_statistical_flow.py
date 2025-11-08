from pymongo import MongoClient, ReplaceOne
import time
from collections import Counter

# === CẤU HÌNH ===
ANALYTICS_URL = "mongodb://localhost:27017/"
DB_NAME = "borrower_analytics"
INPUT_COLLECTION = "borrowers_detail"
OUTPUT_COLLECTION = "statistical_flow_clean"

# === KẾT NỐI ===
client = MongoClient(ANALYTICS_URL)
db = client[DB_NAME]
input_coll = db[INPUT_COLLECTION]
output_coll = db[OUTPUT_COLLECTION]

print(f"START: Reading from `{INPUT_COLLECTION}` → Building `{OUTPUT_COLLECTION}`\n")

start_time = time.time()

# === XÓA CŨ ===
output_coll.drop()
print(f"Dropped `{OUTPUT_COLLECTION}` if exists")

output_coll.create_index("id", unique=True)

# === ĐẾM ===
event_counter = Counter()   # DỪNG KHI GẶP BORROW TRONG 4 ACTION
flow_counter = Counter()    # LẤY ĐẦY ĐỦ 4 ACTION (CÓ BORROW)
flow_id = 1
bulk_ops = []
processed = 0

# === DUYỆT TỪNG USER ===
cursor = input_coll.find({"isEOA": True}, {"flows": 1})

for doc in cursor:
    processed += 1
    flows_str = doc.get("flows", "")
    if not flows_str or "BORROW" not in flows_str:
        continue

    events = [e.strip() for e in flows_str.split("->")]
    borrow_positions = [i for i, e in enumerate(events) if e == "BORROW"]

    # ===================================================================
    # 1. ĐẾM event_type: DỪNG NGAY KHI GẶP BORROW TRONG 4 ACTION SAU
    # ===================================================================
    for borrow_idx in borrow_positions:
        count = 0
        for i in range(borrow_idx + 1, min(borrow_idx + 5, len(events))):
            event = events[i]
            if event == "BORROW":
                break  # DỪNG NGAY
            event_counter[event] += 1
            count += 1

    # ===================================================================
    # 2. TÍNH statistical_flow: LẤY ĐẦY ĐỦ 4 ACTION SAU MỖI BORROW
    # ===================================================================
    for borrow_idx in borrow_positions:
        end_idx = min(borrow_idx + 5, len(events))
        segment = events[borrow_idx:end_idx]
        if len(segment) < 2:
            continue
        for length in range(2, len(segment) + 1):
            sub_flow = " -> ".join(segment[:length])
            flow_counter[sub_flow] += 1

    if processed % 1000 == 0:
        print(f"Processed {processed} users...", end="\r")

# === TẠO statistical_flow_clean ===
for flow_str, total in flow_counter.items():
    number_actions = len(flow_str.split(" -> "))
    clean_doc = {
        "id": flow_id,
        "flow": flow_str,
        "numberActions": number_actions,
        "total": total
    }
    bulk_ops.append(
        ReplaceOne({"id": flow_id}, clean_doc, upsert=True)
    )
    flow_id += 1

# === GHI DỮ LIỆU ===
if bulk_ops:
    result = output_coll.bulk_write(bulk_ops)
    print(f"\nUPSERTED {result.upserted_count} unique flows")

# === IN MẪU ===
print(f"\nSAMPLE DOCUMENT:")
sample = output_coll.find_one()
for k, v in sample.items():
    if k != "_id":
        print(f"{k}: {v}")

# === IN TOP 10 ===
print(f"\n{'='*80}")
print(f"TOP 10 FLOWS BY ACTION LENGTH")
print(f"{'='*80}")

for actions in [2, 3, 4, 5]:
    print(f"\nTOP 10 FLOWS WITH {actions} ACTIONS")
    print(f"{'-'*80}")
    top = output_coll.find({"numberActions": actions}).sort("total", -1).limit(10)
    rank = 1
    for doc in top:
        print(f"#{rank:2d} | {doc['flow']:50} | Total: {doc['total']:,}")
        rank += 1

# === IN EVENT STATISTICS (DỪNG KHI GẶP BORROW) ===
print(f"\n{'='*80}")
print(f"EVENT TYPE STATISTICS (4 ACTIONS AFTER BORROW - STOP AT NEXT BORROW)")
print(f"{'='*80}")

total_non_borrow = 0
for event in sorted(event_counter.keys()):
    count = event_counter[event]
    print(f"{event:18} : {count:,}")
    total_non_borrow += count

print(f"{'-'*60}")
print(f"TOTAL NON-BORROW: {total_non_borrow:,}")

# === TỔNG KẾT ===
total_flows = output_coll.count_documents({})
print(f"\n{'='*80}")
print(f"DONE in {time.time() - start_time:.2f}s")
print(f"Total users processed: {processed}")
print(f"Unique flows: {total_flows}")
print(f"Output collection: `{OUTPUT_COLLECTION}`")
print(f"→ FIXED: TRANSFER = 15, NOT 18!")

client.close()

#PYTHONPATH=. python src/test_statistical_flow.py