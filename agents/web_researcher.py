"""Web Research Agent for gathering supplementary information."""

import logging
from typing import Dict, Any, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from config import get_config
from tools.search_tool import WebSearchTool
from utils.helpers import sanitize_text

logger = logging.getLogger(__name__)


class WebResearchAgent:
    """Agent for gathering supplementary information through web search."""
    
    def __init__(self):
        """Initialize web research agent."""
        self.config = get_config()
        self.llm = ChatOpenAI(
            model_name=self.config.llm.model,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
            api_key=self.config.llm.api_key,
            base_url=self.config.llm.base_url
        )
        self.search_tool = WebSearchTool()
        
        # System prompt for research summarization
        self.system_prompt = """You are a research curator for a moral story video generation system.

Your role is to:
1. Analyze web search results related to moral themes, storytelling techniques, and age-appropriate content
2. Curate and summarize relevant information
3. Extract key insights that can enhance story generation
4. Ensure all content is child-safe and age-appropriate

Focus on:
- Moral themes and their importance
- Age-appropriate storytelling techniques
- Character development best practices
- Cultural references if relevant
- Visual storytelling elements

Output a structured summary of curated research findings."""

        self.human_prompt = """Analyze the following search results and create a curated research summary:

Context:
{context}

Search Results:
{search_results}

Create a comprehensive research summary that can be used to enhance story generation.
Focus on actionable insights for creating an engaging, age-appropriate moral story."""

    def research(
        self,
        context: Dict[str, Any],
        search_queries: List[str],
        age_group: str = "6-8"
    ) -> Dict[str, Any]:
        """
        Execute web research and curate findings.
        
        Args:
            context: Validated context from context analyzer
            search_queries: List of search queries
            age_group: Target age group
            
        Returns:
            Dictionary with research results and summary
        """
        try:
            logger.info(sanitize_text(f"Executing web research with {len(search_queries)} queries"))
            
            # Execute searches
            all_results = {}
            for query in search_queries:
                logger.info(sanitize_text(f"Searching: {query}"))
                results = self.search_tool.search(
                    query=query,
                    age_group=age_group,
                    filter_child_safe=True
                )
                all_results[query] = results
            
            # If no results, return empty research
            if not any(all_results.values()):
                logger.warning("No search results found, returning empty research")
                return {
                    "research_results": {},
                    "research_summary": "No additional research information available."
                }
            
            # Summarize results using LLM
            search_results_text = self._format_search_results(all_results)
            
            # Create prompt
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(self.system_prompt),
                HumanMessagePromptTemplate.from_template(self.human_prompt)
            ])
            
            formatted_prompt = prompt.format_messages(
                context=self._format_context(context),
                search_results=search_results_text
            )
            
            # Call LLM for summarization
            response = self.llm.invoke(formatted_prompt)
            research_summary = sanitize_text(response.content)
            
            logger.info(sanitize_text("Research completed successfully"))
            
            return {
                "research_results": all_results,
                "research_summary": research_summary
            }
            
        except Exception as e:
            logger.error(sanitize_text(f"Error in web research: {e}"))
            # Graceful degradation: return empty research
            logger.warning("Falling back to empty research due to error")
            return {
                "research_results": {},
                "research_summary": "Research information unavailable. Proceeding with context only."
            }
    
    def _format_search_results(self, all_results: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Format search results for LLM summarization.
        
        Args:
            all_results: Dictionary mapping queries to results
            
        Returns:
            Formatted text of search results
        """
        formatted = []
        
        for query, results in all_results.items():
            if not results:
                continue
            
            formatted.append(f"Query: {query}\n")
            formatted.append(f"Results ({len(results)}):\n")
            
            for i, result in enumerate(results[:3], 1):  # Top 3 results per query
                title = sanitize_text(result.get("title", "Untitled"))
                content = sanitize_text(result.get("content", "")[:300])  # First 300 chars
                formatted.append(f"{i}. {title}\n   {content}...\n")
            
            formatted.append("\n")
        
        return "\n".join(formatted)
    

    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context for prompt.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        parts = []
        
        if "theme" in context:
            parts.append(f"Theme: {context['theme']}")
        
        if "moral_lesson" in context:
            parts.append(f"Moral Lesson: {context['moral_lesson']}")
        
        if "age_group" in context:
            parts.append(f"Age Group: {context['age_group']}")
        
        if "setting" in context:
            parts.append(f"Setting: {context['setting']}")
        
        if "characters" in context:
            char_names = [char.get("name", "") for char in context["characters"]]
            parts.append(f"Characters: {', '.join(char_names)}")
        
        return "\n".join(parts)

