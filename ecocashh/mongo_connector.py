from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging

logger = logging.getLogger(__name__)

class MongoConnector:
    """
    A simple MongoDB connector class that takes a MongoDB URL and provides
    methods to connect and access databases and collections.
    """

    def __init__(self, mongo_url: str):
        """
        Initialize the MongoDB connector with the provided URL.

        Args:
            mongo_url (str): The MongoDB connection URL (e.g., 'mongodb://localhost:27017/')
        """
        self.mongo_url = mongo_url
        self.client = None

    def connect(self):
        """
        Establish a connection to MongoDB using the provided URL.

        Raises:
            ConnectionFailure: If unable to connect to MongoDB.
        """
        try:
            self.client = MongoClient(self.mongo_url)
            # Test the connection
            self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def disconnect(self):
        """
        Close the MongoDB connection.
        """
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
            self.client = None

    def get_database(self, db_name: str):
        """
        Get a database object.

        Args:
            db_name (str): The name of the database.

        Returns:
            Database: The MongoDB database object.
        """
        if not self.client:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        return self.client[db_name]

    def get_collection(self, db_name: str, collection_name: str):
        """
        Get a collection object from the specified database.

        Args:
            db_name (str): The name of the database.
            collection_name (str): The name of the collection.

        Returns:
            Collection: The MongoDB collection object.
        """
        db = self.get_database(db_name)
        return db[collection_name]

    def list_databases(self):
        """
        List all databases in the MongoDB instance.

        Returns:
            list: List of database names.
        """
        if not self.client:
            raise ConnectionError("Not connected to MongoDB. Call connect() first.")
        return self.client.list_database_names()

    def list_collections(self, db_name: str):
        """
        List all collections in the specified database.

        Args:
            db_name (str): The name of the database.

        Returns:
            list: List of collection names.
        """
        db = self.get_database(db_name)
        return db.list_collection_names()