import os
from dotenv import load_dotenv
from src.constants.network_constants import Chains

load_dotenv()


class MongoDBConnectionURL:
    EtlReader = os.getenv("ETL_READER_CONNECTION_URL", "")
    AnalyticsDB = os.getenv("ANALYTICS_DB_CONNECTION_URL", "mongodb://localhost:27017")


class BorrowerAnalyticsDatabase:
    db_name = "borrower_analytics"

    borrowers = "borrowers"
    configs = "configs"


class AnalyticsClusters:
    borrower_analytics = BorrowerAnalyticsDatabase.db_name


class BlockchainETLDatabase:
    db_name = "blockchain_etl"
    
    collectors = "collectors"
    dex_events = "dex_events"
    events = "events"
    projects = "projects"


class DBPrefix:
    mapping = {
        Chains.ETH: "ethereum",
        Chains.BASE: "base",
    }
