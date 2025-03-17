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

        database_crew = Database()
        print("Database crew initialized successfully.")
        result = database_crew.crew().kickoff(inputs=inputs)
        print(f"Crew execution completed successfully")
    except Exception as e:
        print(f"An error occurred while running the crew: {e}")
        raise

run()