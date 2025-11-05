from pymongo import MongoClient
from databases.BlockchainEtlDB import BlockchainEtlDB
from constants.mongodb_constants import MongoDBConnectionURL, BorrowerAnalyticsDatabase, Chains
import time

class AggregatorDB(BlockchainEtlDB):
    def __init__(self, chain_id: str = Chains.BASE):
        super().__init__(chain_id, MongoDBConnectionURL.EtlReader)
        self.analytics_client = MongoClient(MongoDBConnectionURL.AnalyticsDB)
        self.analytics_db = self.analytics_client[BorrowerAnalyticsDatabase.db_name]
        self.borrowers = self.analytics_db[BorrowerAnalyticsDatabase.borrowers]
        self.configs = self.analytics_db[BorrowerAnalyticsDatabase.configs]
        self.borrowers.create_index([("actions.timestamp", -1)])

    def get_last_block(self) -> int:
        config = self.configs.find_one({"_id": "aggregator"})
        return config.get("last_block_number", 37401400) if config else 37401400

    def save_last_block(self, block: int):
        self.configs.update_one(
            {"_id": "aggregator"},
            {"$set": {"last_block_number": block, "updatedAt": int(time.time())}},
            upsert=True
        )

    def close(self):
        self.analytics_client.close()