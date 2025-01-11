import os
from dotenv import load_dotenv
from loguru import logger
from config import Config
from llm import completion
from typing import List
from pydantic import BaseModel, Field

load_dotenv()

logger.add(
    Config.LOG_FILE,
    rotation=Config.LOG_ROTATION,
    retention=Config.LOG_RETENTION,
    format=Config.LOG_FORMAT,
    level=Config.LOG_LEVEL
)

# Define your schema
class Location(BaseModel):
    name: str = Field(description="Name of the city")
    country: str = Field(description="Name of the country")
    population: int = Field(description="Population of the city")
    landmarks: List[str] = Field(description="Famous landmarks in the city")
    description: str = Field(description="Brief description of the city")

def main():
    logger.info('...let\'s get it started...')
    logger.info(f'Using LLM: {Config.LLM}')

    messages = [
        {
            "role": "system", 
            "content": "You are a helpful assistant that provides detailed city information in JSON format. Always include population, landmarks, and a brief description."
        },
        {
            "role": "user", 
            "content": "Provide information about Paris. Make sure to return valid JSON matching the required schema."
        }
    ]
    
    response = completion(
        messages=messages,
        response_format=Location,  # Pass your schema here
        enable_json_validation=True
    )
    
    # Parse the response to validate it matches our schema
    try:
        parsed_response = Location.model_validate_json(response)
        logger.info(f'Validated Response: {parsed_response.model_dump_json(indent=2)}')
    except Exception as e:
        logger.error(f'JSON validation failed: {e}')

if __name__ == "__main__":
    main()