import os
from dotenv import load_dotenv
import datetime
import json

class MySQLMemoryBackend:
    def __init__(self, db_connection):
        """
        Initialize the MySQLMemoryBackend with a DbConnection instance.
        :param db_connection: An instance of DbConnection.
        """
        self.db_connection = db_connection
        self.connection = None
        self.cursor = None
        self._ensure_table_exists()

    def _ensure_connection(self):
        """Ensure that the raw connection and cursor are initialized."""
        try:
            # Check if the connection is None
            if self.connection is None:
                self.connection = self.db_connection.engine.raw_connection()
                self.cursor = self.connection.cursor()
                print("Database connection and cursor initialized.")
        except Exception as e:
            print(f"Failed to ensure connection: {str(e)}")
            raise

    def _ensure_table_exists(self):
        """Ensure that the 'crew_memory' table exists and has the required columns."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS crew_memory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `metadata` text,
            `datetime` float DEFAULT NULL,
            `score` float DEFAULT NULL
        );
        """
        try:
            self._ensure_connection()
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("Table 'crew_memory' ensured to exist.")
        except Exception as e:
            print(f"Failed to ensure table exists: {str(e)}")
            raise


    def save(self, task_description=None, score=None, metadata=None, datetime=None):
        """Save a task_description to the database, with optional metadata."""
        # Serialize metadata to JSON if it is a dictionary
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata)  
        
        query = "INSERT INTO crew_memory (task_description, score, metadata, datetime) VALUES (%s, %s, %s, %s)"
        try:
            self._ensure_connection()
            self.cursor.execute(query, (task_description, score, metadata, datetime))
            self.connection.commit()
            print(f"Data saved: task_description={task_description}, score={score}, metadata={metadata}, datetime={datetime}")
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"Failed to save data: {str(e)}")
            raise



    def load(self, task, latest_n=1):
        """
        Load long-term memory data for the given task.
        
        Args:
            task: The task (as a string) for which to load memory.
            latest_n: The number of most recent memory entries to load.
        
        Returns:
            List of memory entries (can be rows or a custom data structure).
        """
        query = """
        SELECT task_description, score, metadata, created_at FROM crew_memory
        ORDER BY created_at DESC
        LIMIT %s
        """
        try:
            self._ensure_connection()
            self.cursor.execute(query, (latest_n,))
            results = self.cursor.fetchall()
            
            # Deserialize metadata from JSON strings to dictionaries
            deserialized_results = []
            for row in results:
                task_description, score, metadata, datetime = row  
                if metadata:
                    metadata = json.loads(metadata)  # Convert JSON string back to dictionary
                deserialized_results.append({
                    "task_description": task_description,
                    "score": score,
                    "metadata": metadata,
                    "datetime": datetime
                })
            
            print(f"Memory loaded successfully for the latest {latest_n} entries.")
            return deserialized_results
        except Exception as e:
            print(f"Failed to load data for task {task}: {str(e)}")
            raise



    def close(self):
        """Close the cursor and connection."""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("MySQLMemoryBackend connection closed successfully.")
        except Exception as e:
            print(f"Failed to close MySQLMemoryBackend connection: {str(e)}")
            raise
