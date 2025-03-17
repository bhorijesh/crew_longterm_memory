from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from connect_db import DbConnection
from memorybackend import MySQLMemoryBackend
from crewai.memory import LongTermMemory

load_dotenv()

@CrewBase
class Database():
    """Database crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        """
        Initialize the Database crew with a shared memory backend.
        """
        # Initialize DbConnection
        db_connection = DbConnection()
        db_connection.get_server_connection()
        self.memory_backend = MySQLMemoryBackend(db_connection)

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            verbose=True,
        )

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'],
            verbose=True,  
        )

    @task
    def research_task(self) -> Task:
        print("Creating research task...")
        return Task(
            config=self.tasks_config['research_task'],  
            agent=self.researcher(),
        )

    @task
    def reporting_task(self) -> Task:
        print("Creating reporting task...")
        return Task(
            config=self.tasks_config['reporting_task'],  
            agent=self.reporting_analyst(),
            output_file='report.md', 
        )


    @crew
    def crew(self) -> Crew:
        """Creates the Database crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            memory=True,
            long_term_memory=LongTermMemory(
                storage=self.memory_backend  
            )
        )
