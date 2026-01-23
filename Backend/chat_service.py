# chat_service.py
"""
Chat Service for AI Research Assistant
Handles conversational Q&A with RAG context
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try importing LLM client
try:
    from llm_client import llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM client not available. Chat will be limited.")

def chat_with_context(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Process chat message with research context.
    
    Args:
        message: User's question
        context: Research analysis context (papers, report, etc.)
        conversation_history: Previous messages in conversation
        
    Returns:
        Dictionary with response and citations
    """
    if not LLM_AVAILABLE:
        return {
            "response": "Chat service is currently unavailable. Please ensure the LLM is configured.",
            "citations": []
        }
    
    try:
        # Build context-aware prompt
        prompt = build_chat_prompt(message, context, conversation_history)
        
        # Generate response
        response = llm.generate(prompt)
        
        # Extract citations from response
        citations = extract_citations(response)
        
        return {
            "response": response,
            "citations": citations
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "response": "I encountered an error processing your question. Please try again.",
            "citations": []
        }

def build_chat_prompt(
    message: str,
    context: Optional[Dict[str, Any]],
    history: Optional[List[Dict[str, str]]]
) -> str:
    """Build prompt with context and history."""
    prompt_parts = []
    
    # System instruction
    prompt_parts.append(
        "You are a helpful research assistant. Answer questions about the research analysis "
        "based on the provided context. Always cite sources using [P#] format when referencing papers."
    )
    
    # Add research context
    if context:
        prompt_parts.append("\n\nRESEARCH CONTEXT:")
        
        if context.get('research_idea'):
            prompt_parts.append(f"Research Idea: {context['research_idea']}")
        
        if context.get('final_report'):
            # Truncate if too long
            report = context['final_report'][:2000]
            prompt_parts.append(f"\nAnalysis Report:\n{report}")
        
        if context.get('papers'):
            prompt_parts.append("\nRetrieved Papers:")
            for paper in context['papers'][:5]:  # Limit to 5 papers
                prompt_parts.append(
                    f"[{paper.get('handle', 'P?')}] {paper.get('title', 'Unknown')} "
                    f"({paper.get('year', 'N/A')})"
                )
    
    # Add conversation history
    if history:
        prompt_parts.append("\n\nCONVERSATION HISTORY:")
        for msg in history[-5:]:  # Last 5 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            prompt_parts.append(f"{role.upper()}: {content}")
    
    # Add current question
    prompt_parts.append(f"\n\nUSER QUESTION: {message}")
    prompt_parts.append("\nASSISTANT:")
    
    return "\n".join(prompt_parts)

def extract_citations(text: str) -> List[str]:
    """Extract [P#] citations from text."""
    import re
    citations = re.findall(r'\[P\d+\]', text)
    return list(set(citations))  # Remove duplicates
