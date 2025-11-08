import time
from db.aggregator_db import AggregatorDB
from aggregator.borrower_aggregator import aggregate_batch

# === CẤU HÌNH === PYTHONPATH=src python src/test_aggregator_local.py
# source /home/khanh/borrower-behaviours-analytics/.venv/bin/activate
START_BLOCK = 37810097
END_BLOCK = 37856097
BATCH_SIZE = 1000
RESET_TO_START = True

if __name__ == "__main__":
    db = AggregatorDB()

    # === RESET HOẶC TIẾP TỤC ===
    if RESET_TO_START:
        db.save_last_block(START_BLOCK - 1)
        current_block = START_BLOCK
        print(f"RESET & START FROM: {current_block}")
    else:
        current_block = db.get_last_block() + 1
        print(f"CONTINUE FROM: {current_block}")

    print(f"END AT: {END_BLOCK}")
    print(f"TOTAL: {END_BLOCK - current_block + 1:,} blocks (~{(END_BLOCK - current_block) // BATCH_SIZE + 1} batch)\n")

    total_new_users = 0
    batch_count = 0
    overall_start = time.time()

    try:
        while current_block <= END_BLOCK:
            batch_start = current_block
            batch_end = min(current_block + BATCH_SIZE - 1, END_BLOCK)

            print(f"[{batch_count+1:4d}] {batch_start:>10} → {batch_end:>10}...", end=" ")

            batch_start_time = time.time()
            try:
                aggregate_batch(db, batch_start, batch_end)
            except Exception as e:
                print(f"\nERROR IN BATCH: {e}")
                raise

            # === LƯU TIẾN ĐỘ ===
            db.save_last_block(batch_end)
            current_block = batch_end + 1

            # === ĐẾM USER MỚI (CHỈ LẦN ĐẦU XUẤT HIỆN) ===
            batch_time = int(time.time())
            new_in_batch = db.borrowers.count_documents({
                "createdAt": {"$gte": batch_time - 60, "$lte": batch_time + 60}
            })
            total_new_users += new_in_batch

            elapsed = time.time() - batch_start_time
            print(f"Done in {elapsed:5.2f}s | +{new_in_batch:3d} new | Total new: {total_new_users:,}")

            batch_count += 1
            time.sleep(0.05)

    except KeyboardInterrupt:
        print(f"\nSTOPPED! Progress saved at block {current_block - 1}")
        print(f"→ Run again to continue from here.")
    finally:
        total_time = time.time() - overall_start
        final_count = db.borrowers.count_documents({})

        print(f"\nDONE!")
        print(f"   Range: {START_BLOCK} → {current_block - 1}")
        print(f"   Batches: {batch_count}")
        print(f"   Time: {total_time/60:.1f} min")
        print(f"   Total users: {final_count:,}")
        print(f"   New users: {total_new_users:,}")

        print("\nCHECK IN COMPASS:")
        print("   use borrower_analytics")
        print("   db.borrowers.count()")
        print("   db.borrowers.findOne({'actions.10': {$exists: true}})")
        print("   db.borrowers.findOne({'behaviorTags': 'flash_loan'})")
        print("   db.borrowers.count({'createdAt': {$gte: Date.now() - 3600000}})  // last hour")

        db.close()
