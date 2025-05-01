from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field
import yaml
import json
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.v18.services.types.keyword_plan_idea_service import (
    GenerateKeywordIdeaResponse,
    GenerateKeywordIdeasRequest,
)

# Load configs properly
with open("keys/google-ads.yaml", "r") as f:
    google_ads_config = yaml.safe_load(f)

with open("keys/google-analytics-keys.json", "r") as f:
    google_analytics_keys = json.load(f)

GOOGLE_ADS_YAML_FILE = "keys/google-ads.yaml"
GOOGLE_ADS_CUSTOMER_ID = google_ads_config.get("customer_id")


# Input Schema
class GoogleKeywordIdeaGeneratorInput(BaseModel):
    """Input schema for GoogleKeywordIdeaGenerator."""
    location_id: str = Field(..., description="Geo target location ID (e.g., 2840 for US).")
    keywords: Optional[str] = Field(None, description="Comma-separated keywords, optional if URL is provided.")
    url: Optional[str] = Field(None, description="Landing page URL, optional if keywords are provided.")


# CrewAI Tool
class GoogleKeywordIdeaGeneratorTool(BaseTool):
    name: str = "Google Keyword Idea Generator Tool"
    description: str = "Generates keyword ideas based on keywords or a landing page URL for a specific location."
    args_schema: Type[BaseModel] = GoogleKeywordIdeaGeneratorInput

    def _run(self, location_id: str, keywords: Optional[str] = None, url: Optional[str] = None) -> List[dict]:
        generator = _GoogleKeywordIdeaGenerator(location_id=location_id, keywords=keywords, url=url)
        return generator.get_results()


# Internal Helper Class (not a CrewAI tool)
class _GoogleKeywordIdeaGenerator:
    __client = GoogleAdsClient.load_from_storage(GOOGLE_ADS_YAML_FILE, version="v18")

    def __init__(self, location_id: str, keywords: Optional[str] = None, url: Optional[str] = None):
        self.page_size = 10
        self.next_page_token = None
        if not keywords and not url:
            raise ValueError("Either keywords or url must be provided.")
        
        self.location_id = location_id
        self.keywords = keywords.split(",") if keywords else None
        self.url = url if url else None

    def __configure_request(self) -> GenerateKeywordIdeasRequest:
        language_rn = self.__client.get_service("GoogleAdsService").language_constant_path(1000)

        keyword_plan_network = self.__client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH

        request: GenerateKeywordIdeasRequest = self.__client.get_type("GenerateKeywordIdeasRequest")
        request.language = language_rn
        request.page_size = self.page_size
        request.customer_id = GOOGLE_ADS_CUSTOMER_ID
        request.include_adult_keywords = False
        request.keyword_plan_network = keyword_plan_network
        request.historical_metrics_options.include_average_cpc = True

        if self.location_id:
            request.geo_target_constants.append(f"geoTargetConstants/{self.location_id}")

        if self.url and not self.keywords:
            request.url_seed.url = self.url
        elif self.keywords and not self.url:
            request.keyword_seed.keywords.extend(self.keywords)
        elif self.keywords and self.url:
            request.keyword_and_url_seed.url = self.url
            request.keyword_and_url_seed.keywords.extend(self.keywords)

        return request

    def __generate_keyword_ideas(self):
        keyword_plan_idea_service = self.__client.get_service("KeywordPlanIdeaService")
        request = self.__configure_request()
        keyword_ideas: GenerateKeywordIdeaResponse = keyword_plan_idea_service.generate_keyword_ideas(request=request)
        response = keyword_ideas.results
        next_page_token = getattr(keyword_ideas, "next_page_token", None)
        return response, next_page_token

    def get_results(self) -> List[dict]:
        self.response, self.next_page_token = self.__generate_keyword_ideas()
        results = []
        for item in self.response:
            results.append(self.__get_metric(item))
        return results

    def __get_metric(self, item) -> dict:
        metrics = item.keyword_idea_metrics
        return {
            "text": item.text,
            "competition": metrics.competition,
            "low_top_of_page_bid_cpc": int(getattr(metrics, "low_top_of_page_bid_micros", 0)) / 1_000_000,
            "high_top_of_page_bid_cpc": int(getattr(metrics, "high_top_of_page_bid_micros", 0)) / 1_000_000,
            "average_cpc": int(getattr(metrics, "average_cpc_micros", 0)) / 1_000_000,
            "avg_month_searches": metrics.avg_monthly_searches,
        }
