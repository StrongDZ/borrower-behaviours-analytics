
import time
from db.aggregator_db import AggregatorDB
from aggregator.borrower_aggregator import aggregate_batch, get_tip_block

if __name__ == "__main__":
    db = AggregatorDB()
    last_block = db.get_last_block()
    print(f"Last block: {last_block}")
    tip_block = get_tip_block(db)
    print(f"Tip block: {tip_block}")
    if last_block >= tip_block:
        print("Caught up!")
        db.close()
        exit(0)
    BATCH_SIZE = 1000
    start = last_block
    end = min(start + BATCH_SIZE, tip_block + 1)
    print(f"\nTESTING: {start} → {end}")
    start_time = time.time()
    aggregate_batch(db, start, end)
    batch_users = db.borrowers.count_documents({
        "updatedAt": {"$gte": int(time.time()) - 60}
    })
    elapsed = time.time() - start_time
    print(f"\nDONE!")
    print(f"Processed: {start} → {end}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Users in batch: {batch_users}")
    print(f"Total users: {db.borrowers.count_documents({})}")
    print("\nCHECK IN COMPASS:")
    print("use borrower_analytics")
    print('db.borrowers.find({"updatedAt": {"$gte": Date.now() - 60000}}).limit(5).pretty()')
    db.save_last_block(end)
    db.close()
