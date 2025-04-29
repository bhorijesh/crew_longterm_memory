#!/usr/bin/env python
import sys
import warnings
from datetime import datetime

from crew import Database

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    # Gather user inputs dynamically
    Products = input("Enter a product: ")
    Description = input("Enter a description: ")
    Price = input("Enter a price: ")
    Url = input("Enter a URL: ")
    Image= input("Enter Image: ")
    Tone = input("Enter a tone: ")
    Language = input("Enter a language: ")
    inputs = {
        'Products': Products,
        'Description': Description,
        'Price': Price,
        'Url': Url,
        'Image': Image,
        'Tone': Tone,
        'Language': Language,
        'current_year': str(datetime.now().year)
    }

    try:
        # Initialize Database crew
        database_crew = Database()
        print("Database crew initialized successfully.")
        result = database_crew.crew().kickoff(inputs=inputs)
        print(f"Crew execution completed successfully")
    except Exception as e:
        print(f"An error occurred while running the crew: {e}")
        raise

run()
