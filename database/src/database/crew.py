import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv
from connect_db import DbConnection
from crewai_tools import SerperDevTool
from crewai_tools import WebsiteSearchTool ,VisionTool
import os
from tools.custom_tool import GoogleKeywordIdeaGeneratorTool

load_dotenv()

class CustomShortTermMemory:
    """Custom short-term memory to store and retrieve data."""
    def __init__(self):
        self.memory_store = {}

    def store(self, key, value):
        self.memory_store[key] = value

    def retrieve(self, key):
        return self.memory_store.get(key)

@CrewBase
class Database:
    """Database crew"""

    def __init__(self):
        self.agents_config = self.load_yaml('config/agents.yaml')
        self.tasks_config = self.load_yaml('config/tasks.yaml')

        self.db_connection = DbConnection()
        self.db_connection.get_server_connection()

        self.memory_backend = CustomShortTermMemory()

        self.serper_tool = SerperDevTool()
        self.website_tool = WebsiteSearchTool()
        self.vision_tool = VisionTool()
        self.google_keyword_tool = GoogleKeywordIdeaGeneratorTool()

    def load_yaml(self, path: str):
        if not os.path.exists(path):
            print(f"Warning: YAML config file {path} not found.")
            return {}
        with open(path, 'r') as file:
            return yaml.safe_load(file)

    @agent
    def product_information_gatherer(self) -> Agent:
        search_tools = [self.website_tool, self.serper_tool, self.vision_tool]

        def gather_product_info(context):
            # Extract product details from the context
            product = context.get('Products') or context.get('product')
            description = context.get('Description', '')
            price = context.get('Price', 'Price not available')
            url = context.get('Url', '')
            image = context.get('Image', '')

            if not product:
                raise ValueError("Product name missing in context.")

            print(f"[Agent] Gathering information for product: {product}")
            
            # Use Serper tool to gather additional product info (description)
            serper_results = self.serper_tool.run({"search_query": product})
            if serper_results and isinstance(serper_results, dict):
                description = serper_results.get("snippet", description)

            # Use Website Tool if a URL is provided to enrich the description
            if url:
                print(f"[Agent] Using WebsiteSearchTool to extract content from: {url}")
                website_data = self.website_tool.run({"search_query": product, "website": url})
                print(f"[Agent] WebsiteSearchTool returned: {website_data}")
                if website_data and isinstance(website_data, dict):
                    site_text = website_data.get("text", '')
                    if site_text:
                        description = f"{description}\n\nWebsite Extracted Text: {site_text[:500]}"

            # Use Vision Tool if an image URL is provided to gather insights
            if image:
                print(f"[Agent] Using VisionTool to analyze image: {image}")
                vision_result = self.vision_tool.run({"image_path_url": image})
                if vision_result and isinstance(vision_result, dict):
                    image_summary = vision_result.get("description") or vision_result.get("tags", [])
                    if isinstance(image_summary, list):
                        image_summary = ", ".join(image_summary)
                    description = f"{description}\n\nImage Insights: {image_summary}"

            # Ensure a full product info dictionary is returned
            product_info = {
                'product': product,
                'description': description or 'No description provided.',
                'price': price,
                'url': url or 'URL not provided.',
                'image': image or 'Image not available.',
                'features': ['Feature 1', 'Feature 2', 'Feature 3'],  # Can be improved with dynamic data
                'specifications': ['Specification 1', 'Specification 2'],  # As above
                'benefits': ['Benefit 1', 'Benefit 2'],  # As above
            }

            # Store the product information in memory
            self.memory_backend.store('product_info', product_info)
            
            return product_info

        return Agent(
            config=self.agents_config.get('product_information_gatherer', {}),
            verbose=True,
            tools=search_tools,
            process=gather_product_info
        )

    @agent
    def keyword_researcher(self) -> Agent:
        search_tools = [self.google_keyword_tool]

        def fetch_keywords(context):
            product_info = self.memory_backend.retrieve('product_info')
            if not product_info:
                raise ValueError("Product information not found in memory.")

            query = f"Keywords related to {product_info['product']}"
            print(f"[Agent] Searching for keywords with query: {query}")
            search_results = search_tools.run({"query": query})
            print("[Agent] Raw search results:", search_results)

            keywords = []
            if isinstance(search_results, list):
                keywords = [result['title'] for result in search_results if 'title' in result]

            print("[Agent] Extracted keywords:", keywords)
            self.memory_backend.store('keywords', keywords)

            return keywords

        return Agent(
            config=self.agents_config.get('keyword_researcher', {}),
            verbose=True,
            tools=search_tools,
            process=fetch_keywords
        )

    @agent
    def blog_writer(self) -> Agent:
        def write_blog(context):
            keywords = self.memory_backend.retrieve('keywords')
            if not keywords:
                raise ValueError("Keywords not found in memory.")

            blog_content = f"Blog Content based on keywords: {', '.join(keywords)}"
            print("[Agent] Generated blog content:", blog_content)
            self.memory_backend.store('blog_content', blog_content)
            return blog_content

        return Agent(
            config=self.agents_config.get('blog_writer', {}),
            verbose=True,
            process=write_blog
        )

    @agent
    def seo_agent(self) -> Agent:
        def optimize_blog(context):
            blog_content = self.memory_backend.retrieve('blog_content')
            if not blog_content:
                raise ValueError("Blog content not found in memory.")

            keywords = self.memory_backend.retrieve('keywords')
            if not keywords:
                raise ValueError("Keywords not found in memory.")

            missing_keywords = [kw for kw in keywords if kw.lower() not in blog_content.lower()]

            if missing_keywords:
                print(f"[Agent] Missing keywords in blog content: {missing_keywords}")
                self.memory_backend.store('retry', True)
                return f"Missing keywords: {missing_keywords}"
            else:
                optimized_content = f"SEO Optimized Version:\n\n{blog_content}"
                print("[Agent] Optimized blog content:", optimized_content)
                self.memory_backend.store('optimized_blog', optimized_content)
                self.memory_backend.store('retry', False)
                return optimized_content

        return Agent(
            config=self.agents_config.get('seo_agent', {}),
            verbose=True,
            process=optimize_blog
        )

    @agent
    def final_writer(self) -> Agent:
        def refine_blog(context):
            optimized_blog = self.memory_backend.retrieve('optimized_blog')
            if not optimized_blog:
                raise ValueError("Optimized blog not found in memory.")

            final_content = optimized_blog + "\n\n-- Final refined version with edits."
            print("[Agent] Final blog content:", final_content)
            self.memory_backend.store('final_blog', final_content)
            return final_content

        return Agent(
            config=self.agents_config.get('final_writer', {}),
            verbose=True,
            process=refine_blog
        )

    @task
    def product_information_gather_task(self) -> Task:
        return Task(
            config=self.tasks_config.get('product_information_gather_task', {}),
            agent=self.product_information_gatherer(),
        )

    @task
    def keyword_research_task(self) -> Task:
        return Task(
            config=self.tasks_config.get('keyword_research_task', {}),
            agent=self.keyword_researcher(),
            output_file='keywords.md',
        )

    @task
    def blog_writing_task(self) -> Task:
        return Task(
            config=self.tasks_config.get('blog_writing_task', {}),
            agent=self.blog_writer(),
        )

    @task
    def seo_optimization_task(self) -> Task:
        return Task(
            config=self.tasks_config.get('seo_optimization_task', {}),
            agent=self.seo_agent(),
            output_file='seo_blog.md',
        )

    @task
    def final_write_task(self) -> Task:
        return Task(
            config=self.tasks_config.get('final_write_task', {}),
            agent=self.final_writer(),
            output_file='final_blog.md',
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.product_information_gatherer(),
                self.keyword_researcher(),
                self.blog_writer(),
                self.seo_agent(),
                self.final_writer(),
            ],
            tasks=[
                self.product_information_gather_task(),
                self.keyword_research_task(),
                self.blog_writing_task(),
                self.seo_optimization_task(),
                self.final_write_task(),
            ],
            process=Process.sequential,
            verbose=True,
            memory=True,
            # manager_agent=
            long_term_memory=None,
        )