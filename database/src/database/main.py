#!/usr/bin/env python
import sys
import warnings
from datetime import datetime

from crew import Database

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'History of Nepal',
        'current_year': str(datetime.now().year)
    }
    
    try:
        # Initialize the Database crew
        database_crew = Database()
        
        # Print a message to confirm initialization
        print("Database crew initialized successfully.")
        
        # Run the crew with the provided inputs
        result = database_crew.crew().kickoff(inputs=inputs)
        
        # Print the result of the crew execution
        print(f"Crew execution completed successfully")
    except Exception as e:
        print(f"An error occurred while running the crew: {e}")
        raise

run()