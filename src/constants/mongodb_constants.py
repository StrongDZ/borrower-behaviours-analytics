import os
from dotenv import load_dotenv
from constants.network_constants import Chains
load_dotenv()

class MongoDBConnectionURL:
    EtlReader = "mongodb://etlReader:etl_readerBlockChain341@178.128.85.210:27017,104.248.148.66:27017,103.253.146.224:27017/"
    AnalyticsDB = "mongodb://localhost:27017/"

class BorrowerAnalyticsDatabase:
    db_name = "borrower_analytics"
    borrowers = "borrowers"
    configs = "configs"

class BlockchainETLDatabase:
    db_name = "blockchain_etl"
    collectors = "collectors"
    dex_events = "dex_events"
    events = "events"
    projects = "projects"

class DBPrefix:
    mapping = {Chains.BASE: "base"}