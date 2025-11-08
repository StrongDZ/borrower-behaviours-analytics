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
MAX_ACTIONS = 500

# === WHITELIST: CHỈ LẤY EVENT TRONG MAP ===
VALID_EVENT_TYPES = set(EVENT_COLLECTION_MAP.keys())

FIELD_MAP = {
    "BORROW": ["receiver", "onBehalf", "wallet", "assets", "project", "contract_address"],
    "REPAY": ["caller", "onBehalf", "wallet", "assets", "shares", "project", "contract_address"],
    "DEPOSIT": ["provider", "wallet", "depositType", "locktime", "value", "tokenId", "prevSupply", "supply", "project", "contract_address"],
    "FLASHLOAN": ["wallet", "caller", "contract_address", "project", "token", "assets"],
    "BUYCOLLATERAL": ["wallet", "buyer", "project", "asset", "baseAmount", "collateralAmount", "contract_address"],
    "LOGOPERATE": ["user", "wallet", "supplyAmount", "borrowAmount", "token", "borrowTo", "withdrawTo", "totalAmounts", "exchangePricesAndConfig", "project", "contract_address", "log_index"],
    "POSITIONOPENED": ["wallet", "trader", "project", "currency", "collateralCurrency", "principal", "collateralAmount", "downPayment", "feesToBePaid", "contract_address"],
    "POSITIONINCREASED": ["wallet", "trader", "project", "principalAdded", "collateralAdded", "downPaymentAdded", "feesAdded", "contract_address"],
    "POSITIONDECREASED": ["wallet", "trader", "project", "principalRepaid", "interestPaid", "payout", "collateralReduced", "downPaymentReduced", "closeFee", "pastFees", "contract_address"],
    "SWAP": ["wallet", "sender", "amount0", "amount1", "contract_address", "project", "fee"],
    "TRANSFER": ["from", "to", "tokenId", "wallet", "contract_address"],
    "MODIFYLIQUIDITY": ["wallet", "sender", "tickLower", "tickUpper", "liquidityDelta", "project", "id", "contract_address"],
    "INCREASELIQUIDITY": ["wallet", "pool", "amount0", "amount1", "actualLiquidity", "liquidityDesired", "tokenId", "project", "contract_address"],
    "LIQUIDITYADDED": ["wallet", "liquidityProvider", "pool", "amountsAddedRaw", "totalSupply", "project", "contract_address"],
    "TOKENEXCHANGE": ["wallet", "buyer", "contract_address", "sold_id", "bought_id", "tokens_sold", "tokens_bought"],
    "ADDLIQUIDITY": ["provider", "wallet", "pool", "amountsAddedRaw", "totalSupply", "project", "contract_address", "block_number", "block_timestamp", "transaction_hash", "log_index"],
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
    if not common["txHash"]:
        return None

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
    user_field_map = {
        "BORROW": "receiver",
        "SWAP": "sender",
        "TRANSFER": "from",
        "DEPOSIT": "provider",
        "MODIFYLIQUIDITY": "sender",
        "INCREASELIQUIDITY": "wallet",
        "LIQUIDITYADDED": "liquidityProvider",
        "TOKENEXCHANGE": "buyer",
        "POSITIONOPENED": "trader",
        "POSITIONINCREASED": "trader",
        "POSITIONDECREASED": "trader",
        "LOGOPERATE": "user",
        "BUYCOLLATERAL": "buyer",
        "FLASHLOAN": "wallet",
        "REPAY": "caller",
        "ADDLIQUIDITY": "provider",  # ← ĐÚNG NHƯ BẠN YÊU CẦU
    }

    field = user_field_map.get(etype)
    if field and event.get(field):
        return to_str(event[field]).lower()

    fallback_priority = [
        "receiver", "user", "wallet", "onBehalf", "trader",
        "sender", "from", "owner", "buyer", "provider",
        "caller", "liquidityProvider", "to"
    ]
    for f in fallback_priority:
        val = event.get(f)
        if val:
            return to_str(val).lower()

    return None

def analyze_behavior(actions):
    tags = set()
    if not actions or actions[0]["event_type"] != "BORROW":
        return list(tags)

    post_actions = actions[1:]
    post_types = [a["event_type"] for a in post_actions]
    seq = " -> ".join(post_types[:5])

    if post_actions and post_actions[0]["event_type"] == "REPAY":
        tags.add("flash_loan")
    elif "REPAY" in post_types[:3]:
        tags.add("lending_repay")

    if post_types.count("BORROW") >= 1:
        tags.add("leveraged_lending")

    if any(t in ["SWAP", "TOKENEXCHANGE"] for t in post_types[:5]):
        tags.add("swap_arbitrage")

    if any(t in ["MINT", "BURN", "MODIFYLIQUIDITY", "INCREASELIQUIDITY", "LIQUIDITYADDED", "ADDLIQUIDITY"] for t in post_types):
        tags.add("lp_management")

    if any(t in ["POSITIONOPENED", "POSITIONINCREASED", "POSITIONDECREASED"] for t in post_types):
        tags.add("perp_position")

    if "BUYCOLLATERAL" in post_types:
        tags.add("liquidation_hunt")

    if seq:
        tags.add(f"flow: {seq}")

    return list(tags)

def aggregate_batch(db: AggregatorDB, start_block: int, end_block: int):
    logger.info(f"Processing batch {start_block} → {end_block}")

    all_events = []

    cursor = db.events.find({
        "block_number": {"$gte": start_block, "$lt": end_block}
    }).sort("block_number", pymongo.ASCENDING)
    batch = list(cursor)
    all_events.extend(batch)
    logger.info(f"Loaded {len(batch)} events from 'events'")

    cursor = db.dex_events.find({
        "block_number": {"$gte": start_block, "$lt": end_block}
    }).sort("block_number", pymongo.ASCENDING)
    batch = list(cursor)
    all_events.extend(batch)
    logger.info(f"Loaded {len(batch)} events from 'dex_events'")

    if not all_events:
        logger.info(f"No events in {start_block}-{end_block}")
        return

    filtered_events = [
        event for event in all_events
        if event.get("event_type") in VALID_EVENT_TYPES
    ]
    logger.info(f"Filtered down to {len(filtered_events)} relevant events")

    if not filtered_events:
        logger.info("No valid event types in batch")
        return

    user_events = defaultdict(list)
    for event in filtered_events:
        etype = event["event_type"]
        user = extract_user(event, etype)
        if not user:
            continue
        block = to_int(event["block_number"])
        user_events[user].append((block, event))

    all_users_in_batch = {}
    for user, events in user_events.items():
        events.sort(key=lambda x: x[0])
        all_users_in_batch[user] = events

    existing_users = set()
    if all_users_in_batch:
        cursor = db.borrowers.find(
            {"userAddress": {"$in": list(all_users_in_batch.keys())}},
            {"userAddress": 1}
        )
        existing_users = {doc["userAddress"] for doc in cursor}

    valid_users = {}
    for user, events in all_users_in_batch.items():
        if user in existing_users:
            valid_users[user] = events
        else:
            borrow_idx = next((i for i, e in enumerate(events) if e[1].get("event_type") == "BORROW"), None)
            if borrow_idx is not None:
                valid_users[user] = events[borrow_idx:]

    if not valid_users:
        logger.info("No users to update in this batch")
        return

    logger.info(f"Updating {len(valid_users)} users "
                f"(new: {sum(1 for u in valid_users if u not in existing_users)}, "
                f"existing: {len(existing_users & valid_users.keys())}))")

    for user, events in valid_users.items():
        events.sort(key=lambda x: x[0])
        valid_users[user] = events

    bulk_ops = []
    for user, events in valid_users.items():
        actions = []
        for _, event in events:
            action = build_action(event, event["event_type"])
            if action:
                actions.append(action)

        if not actions:
            continue
        if user not in existing_users and actions[0]["event_type"] != "BORROW":
            continue

        _id = f"base_{user}"
        tags = analyze_behavior(actions)

        bulk_ops.append(pymongo.UpdateOne(
            {"_id": _id},
            {
                "$push": {
                    "actions": {
                        "$each": actions,
                        "$sort": {"block_number": 1},
                        "$slice": -MAX_ACTIONS
                    }
                },
                "$inc": {"totalActions": len(actions)},
                "$set": {"updatedAt": int(time.time()), "userAddress": user},
                "$addToSet": {"behaviorTags": {"$each": tags}},
                "$setOnInsert": {"createdAt": int(time.time()), "chainId": "base"}
            },
            upsert=True
        ))

    if bulk_ops:
        db.borrowers.bulk_write(bulk_ops)
        logger.info(f"Aggregated {len(bulk_ops)} users")

def get_tip_block(db: AggregatorDB):
    max_events = db.events.find_one(sort=[("block_number", pymongo.DESCENDING)])
    max_dex = db.dex_events.find_one(sort=[("block_number", pymongo.DESCENDING)])
    block_events = to_int(max_events.get("block_number")) if max_events else 0
    block_dex = to_int(max_dex.get("block_number")) if max_dex else 0
    return max(block_events, block_dex)

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
            self.db.save_last_block(end)

    def _follow_end(self):
        self.db.close()
