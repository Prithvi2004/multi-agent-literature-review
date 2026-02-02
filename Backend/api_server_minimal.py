# api_server_minimal.py
"""
Minimal Flask API Server for Multi-Agent Literature Review System
Production-ready version with lazy imports and proper error handling
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Configure logging BEFORE any other imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize Flask app FIRST
app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://malrs.vercel.app",
            "https://*.vercel.app",
            "http://localhost:5000",
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

logger.info("Flask app initialized successfully")

# Lazy import function - only import when needed
def get_analysis_modules():
    """Lazy import of analysis modules to avoid startup issues"""
    try:
        logger.info("Importing analysis modules...")
        from main import (
            retrieve_and_index_papers,
            index_uploaded_paper,
            rag_pipeline,
            llm,
            MetricsTracker
        )
        from tasks import create_tasks
        from crewai import Crew, Process
        from research_context import ResearchContext
        from output_formatter import format_and_save_report
        
        # Import agents
        from agents import (
            retrieval_agent,
            decomposition_agent,
            reasoning_agent,
            gap_novelty_agent,
            synthesis_agent,
            quality_control_agent
        )
        
        # Import tools
        from tools import (
            rag_tool,
            rag_tool_instance,
            citation_verifier_tool,
            evidence_validator,
            validate_output_tool,
            read_context_tool,
            log_insight_tool,
            context_tool_wrapper
        )
        
        from main import evidence_store, query_rewriter
        
        logger.info("All analysis modules imported successfully")
        
        return {
            'retrieve_and_index_papers': retrieve_and_index_papers,
            'index_uploaded_paper': index_uploaded_paper,
            'rag_pipeline': rag_pipeline,
            'llm': llm,
            'MetricsTracker': MetricsTracker,
            'create_tasks': create_tasks,
            'Crew': Crew,
            'Process': Process,
            'ResearchContext': ResearchContext,
            'format_and_save_report': format_and_save_report,
            'agents': {
                'retrieval': retrieval_agent,
                'decomposition': decomposition_agent,
                'reasoning': reasoning_agent,
                'gap_novelty': gap_novelty_agent,
                'synthesis': synthesis_agent,
                'quality_control': quality_control_agent
            },
            'tools': {
                'rag_tool': rag_tool,
                'rag_tool_instance': rag_tool_instance,
                'citation_verifier_tool': citation_verifier_tool,
                'evidence_validator': evidence_validator,
                'validate_output_tool': validate_output_tool,
                'read_context_tool': read_context_tool,
                'log_insight_tool': log_insight_tool,
                'context_tool_wrapper': context_tool_wrapper
            },
            'evidence_store': evidence_store,
            'query_rewriter': query_rewriter
        }
    except Exception as e:
        logger.error(f"Error importing analysis modules: {e}", exc_info=True)
        raise

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Multi-Agent Literature Review API"
    })

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information"""
    return jsonify({
        "service": "Multi-Agent Literature Review API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "analyze": "/api/analyze (POST)"
        }
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Main analysis endpoint - imports modules only when called"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        research_idea = data.get('research_idea', '').strip()
        selected_domains = data.get('selected_domains', [])
        
        if not research_idea or not selected_domains:
            return jsonify({
                "status": "error",
                "message": "research_idea and selected_domains are required"
            }), 400
        
        logger.info(f"Analysis request received: {research_idea[:50]}...")
        
        # Lazy import modules
        modules = get_analysis_modules()
        
        # Run analysis (simplified version)
        logger.info("Starting analysis...")
        
        # This is a placeholder - you'll need to implement the full analysis logic
        # For now, return a success response to test deployment
        return jsonify({
            "status": "success",
            "message": "Analysis endpoint is working. Full implementation pending.",
            "data": {
                "research_idea": research_idea,
                "domains": selected_domains
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in /api/analyze: {e}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Determine if running in production
    is_production = os.environ.get('RENDER', False)
    
    logger.info("="*80)
    logger.info("Starting Flask API Server for Multi-Agent Literature Review")
    logger.info(f"Environment: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
    logger.info("="*80)
    logger.info(f"API will be available at: http://0.0.0.0:{port}")
    logger.info(f"Health check: http://0.0.0.0:{port}/api/health")
    logger.info("="*80)
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=not is_production,
        threaded=True
    )
