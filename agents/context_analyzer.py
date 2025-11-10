"""Context Analyzer Agent for parsing and validating input context."""

import logging
import json
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config import get_config
from utils.validators import validate_input

logger = logging.getLogger(__name__)


class ValidatedContext(BaseModel):
    """Validated context structure."""
    
    theme: str = Field(description="Story theme")
    characters: List[Dict[str, Any]] = Field(description="List of characters with names, types, and traits")
    setting: str = Field(description="Story setting")
    moral_lesson: str = Field(description="Moral lesson to convey")
    age_group: str = Field(description="Target age group")
    duration_minutes: int = Field(description="Target video duration in minutes", default=3)
    search_queries: List[str] = Field(description="Generated search queries for knowledge enrichment")


class ContextAnalyzerAgent:
    """Agent for analyzing and validating input context."""
    
    def __init__(self):
        """Initialize context analyzer agent."""
        self.config = get_config()
        self.llm = ChatOpenAI(
            model_name=self.config.llm.model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key
        )
        self.output_parser = PydanticOutputParser(pydantic_object=ValidatedContext)
        
        # System prompt for context analysis
        self.system_prompt = """You are a context analyzer for a moral story video generation system.

Your role is to:
1. Parse and validate input context for story generation
2. Extract key elements: theme, characters, setting, moral lesson, age group
3. Generate search queries for knowledge enrichment about:
   - The moral theme and its importance
   - Age-appropriate storytelling techniques
   - Cultural references if relevant
   - Character archetypes and traits

Ensure all information is child-safe and age-appropriate.

Output a structured JSON with validated context and search queries."""

        self.human_prompt = """Analyze the following input context and generate validated context with search queries:

Input Context:
{input_context}

{format_instructions}

Provide validated context with search queries for knowledge enrichment."""

    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze and validate input context.
        
        Args:
            input_data: Input dictionary with 'context' and 'preferences' keys
            
        Returns:
            Dictionary with validated context and search queries
            
        Raises:
            ValueError: If input validation fails
        """
        # First validate input structure
        is_valid, error_message = validate_input(input_data)
        if not is_valid:
            raise ValueError(f"Input validation failed: {error_message}")
        
        context = input_data.get("context", {})
        
        try:
            logger.info("Analyzing input context")
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template(self.human_prompt)
            ])
            
            # Format prompt with input
            formatted_prompt = prompt.format_messages(
                input_context=json.dumps(context, indent=2),
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Call LLM
            response = self.llm.invoke(formatted_prompt)
            
            # Parse response
            validated_context = self.output_parser.parse(response.content)
            
            # Convert to dictionary
            result = {
                "theme": validated_context.theme,
                "characters": validated_context.characters,
                "setting": validated_context.setting,
                "moral_lesson": validated_context.moral_lesson,
                "age_group": validated_context.age_group,
                "duration_minutes": validated_context.duration_minutes,
                "search_queries": validated_context.search_queries,
            }
            
            logger.info(f"Context analyzed successfully. Generated {len(result['search_queries'])} search queries")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing context: {e}")
            # Fallback: return basic validated context without LLM
            logger.warning("Falling back to basic validation")
            return {
                "theme": context.get("theme", ""),
                "characters": context.get("characters", []),
                "setting": context.get("setting", ""),
                "moral_lesson": context.get("moral_lesson", ""),
                "age_group": context.get("age_group", "6-8"),
                "duration_minutes": context.get("duration_minutes", 3),
                "search_queries": self._generate_fallback_queries(context),
            }
    
    def _generate_fallback_queries(self, context: Dict[str, Any]) -> List[str]:
        """
        Generate fallback search queries without LLM.
        
        Args:
            context: Input context
            
        Returns:
            List of search queries
        """
        queries = []
        
        theme = context.get("theme", "")
        if theme:
            queries.append(f"moral stories about {theme} for children")
            queries.append(f"teaching {theme} to kids")
        
        age_group = context.get("age_group", "6-8")
        if age_group:
            queries.append(f"age-appropriate stories for {age_group} year olds")
        
        moral_lesson = context.get("moral_lesson", "")
        if moral_lesson:
            queries.append(f"children's stories about {moral_lesson}")
        
        return queries

