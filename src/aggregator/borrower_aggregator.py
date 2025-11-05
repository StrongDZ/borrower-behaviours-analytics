# aggregator/borrower_aggregator.py
import time
from collections import defaultdict
import pymongo
from jobs.base.cli_job import CLIJob
from db.aggregator_db import AggregatorDB
from utils.logger_utils import get_logger
from utils.hex_utils import to_int, to_str
from constants.event_map import EVENT_COLLECTION_MAP

logger = get_logger("BorrowerAggregator")

BATCH_SIZE = 1000
MAX_ACTIONS = 500  # Giới hạn 500 actions mới nhất

# === FIELD MAP ĐÃ CẬP NHẬT ĐỦ CHO TẤT CẢ EVENT ===
FIELD_MAP = {
    # === events collection ===
    "BORROW": ["receiver", "onBehalf", "wallet", "assets", "project", "contract_address"],
    "REPAY": ["caller", "onBehalf", "wallet", "assets", "shares", "project", "contract_address"],
    "DEPOSIT": ["provider", "wallet", "depositType", "locktime", "value", "tokenId", "prevSupply", "supply", "project", "contract_address"],
    "FLASHLOAN": ["wallet", "caller", "contract_address", "project", "token", "assets"],
    "BUYCOLLATERAL": ["wallet", "buyer", "project", "asset", "baseAmount", "collateralAmount", "contract_address"],
    "LOGOPERATE": ["user", "wallet", "supplyAmount", "borrowAmount", "token", "borrowTo", "withdrawTo", "totalAmounts", "exchangePricesAndConfig", "project", "contract_address", "log_index"],
    "POSITIONOPENED": ["wallet", "trader", "project", "currency", "collateralCurrency", "principal", "collateralAmount", "downPayment", "feesToBePaid", "contract_address"],
    "POSITIONINCREASED": ["wallet", "trader", "project", "principalAdded", "collateralAdded", "downPaymentAdded", "feesAdded", "contract_address"],

    # === dex_events collection ===
    "SWAP": ["wallet", "sender", "amount0", "amount1", "contract_address", "project", "fee"],
    "TRANSFER": ["from", "to", "tokenId", "wallet", "contract_address"],
    "MODIFYLIQUIDITY": ["wallet", "sender", "tickLower", "tickUpper", "liquidityDelta", "project", "id", "contract_address"],
    "INCREASELIQUIDITY": ["wallet", "pool", "amount0", "amount1", "actualLiquidity", "liquidityDesired", "tokenId", "project", "contract_address"],
    "LIQUIDITYADDED": ["wallet", "liquidityProvider", "pool", "amountsAddedRaw", "totalSupply", "project", "contract_address"],
    "TOKENEXCHANGE": ["wallet", "buyer", "contract_address", "sold_id", "bought_id", "tokens_sold", "tokens_bought"],
}

def build_action(event, etype):
    common = {
        "txHash": to_str(event.get("transaction_hash") or event.get("tx_hash")),
        "block_number": to_int(event.get("block_number")),
        "block_timestamp": to_int(event.get("block_timestamp") or event.get("timestamp")),
        "project": event.get("project", ""),
        "contract_address": to_str(event.get("contract_address")),
        "event_type": etype,
        "timestamp": to_int(event.get("block_timestamp") or event.get("timestamp")),
    }
    if not common["txHash"]: return None

    # Thêm amountInUSD/OutUSD cho SWAP
    if etype == "SWAP":
        common["token_in"] = event.get("token0", "UNKNOWN")
        common["token_out"] = event.get("token1", "UNKNOWN")
        common["amountInUSD"] = event.get("amountInUSD", 0.0)
        common["amountOutUSD"] = event.get("amountOutUSD", 0.0)

    extra = {}
    for field in FIELD_MAP.get(etype, []):
        val = event.get(field)
        if val is not None:
            if isinstance(val, (str, bytes)) and str(val).startswith("0x"):
                extra[field] = to_str(val)
            else:
                extra[field] = val
    common.update(extra)
    return common

def extract_user(event, etype):
    # ƯU TIÊN: user (LOGOPERATE), wallet, sender, from, ...
    priority = [
        "receiver", "wallet", "sender", "from", "trader", "onBehalf", "owner", "buyer",
        "provider", "caller", "user", "liquidityProvider", "to"
    ]
    for f in priority:
        val = event.get(f)
        if val:
            return to_str(val).lower()
    return None

def analyze_behavior(actions):
    tags = []
    borrow_idx = next((i for i, a in enumerate(actions) if a["event_type"] == "BORROW"), -1)
    if borrow_idx != -1:
        post_actions = actions[borrow_idx + 1:]
        seq = " -> ".join(a["event_type"] for a in post_actions[:5])
        if any(a["event_type"] in ["DEPOSIT", "INCREASELIQUIDITY"] for a in post_actions):
            tags.append("leveraged_lending")
        if any(a["event_type"] in ["SWAP", "TOKENEXCHANGE"] for a in post_actions):
            tags.append("swap_invest")
        if any(a["event_type"] in ["POSITIONOPENED", "POSITIONINCREASED"] for a in post_actions):
            tags.append("futures_perps")
        if seq.startswith("BORROW -> REPAY") and len(post_actions) <= 2:
            tags.append("flash_loan")
        if seq:
            tags.append(f"post_flow: {seq}")
    return tags

def aggregate_batch(db: AggregatorDB, start_block: int, end_block: int):
    user_actions = defaultdict(list)
    total_events = 0
    for event_type, coll_name in EVENT_COLLECTION_MAP.items():
        coll = db.events if coll_name == "events" else db.dex_events
        cursor = coll.find({
            "block_number": {"$gte": start_block, "$lt": end_block},
            "event_type": event_type
        }).sort("block_number", pymongo.ASCENDING)
        count = 0
        for event in cursor:
            count += 1
            user = extract_user(event, event_type)
            if not user: continue
            # Chỉ thêm nếu là BORROW hoặc user đã tồn tại
            if event_type == "BORROW" or db.borrowers.count_documents({"_id": f"base_{user.lower()}"}) > 0:
                action = build_action(event, event_type)
                if action: user_actions[user].append(action)
        total_events += count
        if count > 0:
            logger.info(f"Found {count} {event_type} events in {coll_name}")
    logger.info(f"Total events scanned: {total_events}")

    if not user_actions:
        logger.info(f"No users to aggregate in batch {start_block}-{end_block}")
        return

    bulk_ops = []
    for user, actions in user_actions.items():
        _id = f"base_{user.lower()}"
        # SẮP XẾP CŨ → MỚI (ASC)
        actions.sort(key=lambda a: a["timestamp"])
        tags = analyze_behavior(actions)
        bulk_ops.append(pymongo.UpdateOne({"_id": _id}, {
            "$push": {
                "actions": {
                    "$each": actions,
                    "$sort": {"timestamp": 1},      # CŨ Ở TRÊN, MỚI Ở DƯỚI
                    "$slice": -MAX_ACTIONS          # LẤY 500 MỚI NHẤT
                }
            },
            "$inc": {"totalActions": len(actions)},
            "$set": {"updatedAt": int(time.time()), "chainId": "base", "userAddress": user, "behaviorTags": tags},
            "$setOnInsert": {"createdAt": int(time.time())}
        }, upsert=True))
    if bulk_ops:
        db.borrowers.bulk_write(bulk_ops)
        logger.info(f"Aggregated {len(bulk_ops)} users (batch {start_block}-{end_block})")

def get_tip_block(db: AggregatorDB):
    max_events = db.events.find_one(sort=[("block_number", pymongo.DESCENDING)])
    max_dex = db.dex_events.find_one(sort=[("block_number", pymongo.DESCENDING)])
    block_events = max_events.get("block_number", 0) if max_events else 0
    block_dex = max_dex.get("block_number", 0) if max_dex else 0
    tip = max(block_events, block_dex)
    logger.info(f"Tip block from cluster: {tip} (events: {block_events}, dex: {block_dex})")
    return tip

class BorrowerAggregatorJob(CLIJob):
    def __init__(self):
        super().__init__(interval=60)
        self.db = AggregatorDB()

    def _execute(self):
        last_block = self.db.get_last_block()
        tip_block = get_tip_block(self.db)
        if last_block >= tip_block:
            logger.info("Caught up!")
            return
        for start in range(last_block, tip_block, BATCH_SIZE):
            end = min(start + BATCH_SIZE, tip_block + 1)
            aggregate_batch(self.db, start, end)
        self.db.save_last_block(tip_block)

    def _follow_end(self):
        self.db.close()