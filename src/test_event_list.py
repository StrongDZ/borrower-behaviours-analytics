from src.databases.BlockchainEtlDB import BlockchainEtlDB
from src.constants.network_constants import Chains

db = BlockchainEtlDB(chain_id=Chains.BASE)

print("events CÓ:")
print(sorted(db.events.distinct("event_type")))

print("\ndex_events CÓ:")
print(sorted(db.dex_events.distinct("event_type")))

print("\nXONG!")
#PYTHONPATH=. python src/test_event_list.py