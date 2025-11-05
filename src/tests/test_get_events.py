from src.databases.BlockchainEtlDB import BlockchainEtlDB
from src.constants.network_constants import Chains
import pandas as pd
import json
from configs import DATA_DIR
from os.path import join


def test_get_events():
    db = BlockchainEtlDB(chain_id=Chains.BASE)
    events = db.get_events_by_type(
        "BORROW", 100, projections={"event_type": 1, "project": 1, "transaction_hash": 1, "block_number": 1, "wallet": 1, "caller": 1, "onBehalf": 1, "receiver": 1}
    )

    human_events = []
    for event in events:
        if event.get("wallet") == event.get("receiver"):
            human_events.append(event)

    events_path = join(DATA_DIR, "events.json")
    human_events_path = join(DATA_DIR, "human_events.json")

    with open(events_path, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=4, ensure_ascii=False)

    with open(human_events_path, "w", encoding="utf-8") as f:
        json.dump(human_events, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    test_get_events()
