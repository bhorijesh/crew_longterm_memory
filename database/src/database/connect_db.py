from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

class DbConnection:
    def __init__(self):
        self.engine = None

    def get_database_connection(self):
        """Establish a simple database connection"""
        try:
            # Load environment variables from .env file
            load_dotenv()

            # Get database connection details from environment variables
            connection_string = (
                f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}@"
                f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_DATABASE')}?connect_timeout=600"
            )
            self.engine = create_engine(connection_string, pool_pre_ping=True)
            print("Database connection established successfully.")
        except Exception as e:
            print(f"Failed to establish database connection: {str(e)}")
            raise

    def get_server_connection(self):
        """Initialize a database connection and return the DbConnection instance"""
        try:
            self.get_database_connection()
            print("Server connection initialized successfully.")
            return self  # Return the instance with the engine connected
        except Exception as e:
            print(f"Failed to get server connection: {str(e)}")
            raise