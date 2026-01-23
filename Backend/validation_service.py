# validation_service.py
"""
Input Validation Service
Provides AI-powered validation and suggestions for research inputs
"""

import logging
from typing import Dict, List, Any
import re

logger = logging.getLogger(__name__)

# Try importing LLM client
try:
    from llm_client import llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM client not available. AI validation will be limited.")

def validate_research_idea(research_idea: str) -> Dict[str, Any]:
    """
    Validate research idea and provide suggestions.
    
    Args:
        research_idea: The research idea text to validate
        
    Returns:
        Dictionary with validation results and suggestions
    """
    issues = []
    suggestions = []
    score = 100
    
    # Basic validation
    if not research_idea or len(research_idea.strip()) < 20:
        issues.append("Research idea is too short")
        suggestions.append("Provide more details about your research question")
        score -= 40
    
    # Check for research question
    if '?' not in research_idea:
        suggestions.append("Consider framing your idea as a research question")
        score -= 10
    
    # Check for methodology
    methodology_keywords = ['using', 'applying', 'leveraging', 'implementing', 'developing', 'analyzing']
    has_methodology = any(keyword in research_idea.lower() for keyword in methodology_keywords)
    
    if not has_methodology:
        suggestions.append("Consider mentioning the methodology or approach you plan to use")
        score -= 15
    
    # Check for domain specificity
    domain_keywords = ['machine learning', 'nlp', 'computer vision', 'data science', 
                      'neural network', 'deep learning', 'ai', 'artificial intelligence']
    has_domain = any(keyword in research_idea.lower() for keyword in domain_keywords)
    
    if not has_domain:
        suggestions.append("Specify the research domain or field more clearly")
        score -= 15
    
    # AI-powered suggestions (if available)
    if LLM_AVAILABLE and len(research_idea.strip()) >= 20:
        try:
            ai_suggestions = get_ai_suggestions(research_idea)
            if ai_suggestions:
                suggestions.extend(ai_suggestions[:3])  # Limit to top 3
                score += 10  # Bonus for AI enhancement
        except Exception as e:
            logger.error(f"AI suggestion error: {e}")
    
    # Calculate final score
    score = max(0, min(100, score))
    is_valid = score >= 60
    
    return {
        "isValid": is_valid,
        "score": score,
        "issues": issues,
        "suggestions": suggestions
    }

def get_ai_suggestions(research_idea: str) -> List[str]:
    """
    Get AI-powered suggestions for improving the research idea.
    
    Args:
        research_idea: The research idea text
        
    Returns:
        List of suggestions
    """
    if not LLM_AVAILABLE:
        return []
    
    try:
        prompt = f"""Analyze this research idea and provide 2-3 specific, actionable suggestions to improve its clarity and focus:

Research Idea: "{research_idea}"

Provide suggestions in a numbered list format. Be concise and specific."""

        response = llm.generate(prompt)
        
        # Parse suggestions from response
        suggestions = []
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            # Match numbered items (1., 2., etc.) or bullet points
            if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('•'):
                # Remove numbering/bullets
                suggestion = re.sub(r'^\d+\.\s*', '', line)
                suggestion = suggestion.lstrip('-•').strip()
                if suggestion and len(suggestion) > 10:
                    suggestions.append(suggestion)
        
        return suggestions[:3]  # Return top 3
        
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        return []

def validate_domains(selected_domains: List[str], research_idea: str) -> Dict[str, Any]:
    """
    Validate selected research domains against the research idea.
    
    Args:
        selected_domains: List of selected domain names
        research_idea: The research idea text
        
    Returns:
        Dictionary with validation results
    """
    suggestions = []
    score = 100
    
    if not selected_domains:
        suggestions.append("Select at least one research domain")
        score -= 30
    elif len(selected_domains) > 5:
        suggestions.append("Too many domains selected. Focus on 2-3 most relevant domains")
        score -= 20
    
    # Check domain relevance (basic keyword matching)
    if research_idea and selected_domains:
        idea_lower = research_idea.lower()
        
        # Suggest additional domains based on keywords
        domain_keywords = {
            'Machine Learning': ['machine learning', 'ml', 'model', 'training', 'algorithm'],
            'Natural Language Processing': ['nlp', 'text', 'language', 'linguistic', 'sentiment'],
            'Computer Vision': ['vision', 'image', 'visual', 'detection', 'recognition'],
            'Deep Learning': ['deep learning', 'neural', 'cnn', 'rnn', 'transformer'],
        }
        
        suggested_domains = []
        for domain, keywords in domain_keywords.items():
            if domain not in selected_domains:
                if any(keyword in idea_lower for keyword in keywords):
                    suggested_domains.append(domain)
        
        if suggested_domains:
            suggestions.append(f"Consider adding: {', '.join(suggested_domains[:2])}")
    
    return {
        "isValid": score >= 60,
        "score": score,
        "suggestions": suggestions
    }
