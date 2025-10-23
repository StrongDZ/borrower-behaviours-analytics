from pymongo import MongoClient
from src.constants.mongodb_constants import MongoDBConnectionURL, BlockchainETLDatabase, DBPrefix


class BlockchainEtlDB:
    def __init__(self, chain_id: str, connection_url: str = None):
        db_prefix = DBPrefix.mapping.get(chain_id)
        if not connection_url:
            connection_url = MongoDBConnectionURL.EtlReader

        self.client = MongoClient(connection_url)
        self.db = self.client[db_prefix + "_" + BlockchainETLDatabase.db_name]
        self.collectors = self.db[BlockchainETLDatabase.collectors]
        self.dex_events = self.db[BlockchainETLDatabase.dex_events]
        self.events = self.db[BlockchainETLDatabase.events]
        self.projects = self.db[BlockchainETLDatabase.projects]

    ################
    ## Collectors ##
    ################

    def get_all_collectors(self) -> list[dict]:
        return list(self.collectors.find({}))

    def get_collector(self, collector_id: str) -> dict:
        return self.collectors.find_one({"_id": collector_id})

    ############
    ## Events ##
    ############

    def get_all_events(self) -> list[dict]:
        return list(self.events.find({}))

    def get_events_by_type(self, event_type: str, limit: int = None, projections: dict = None) -> list[dict]:
        query = {"event_type": event_type}
        cursor = self.events.find(query, projections).sort("block_number", -1)

        if limit and limit > 0:
            cursor = cursor.limit(limit)

        return list(cursor)
