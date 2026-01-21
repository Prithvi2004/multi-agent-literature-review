# api_server.py
"""
Flask API Server for Multi-Agent Literature Review System
Exposes REST API endpoints for the Streamlit frontend to interact with the backend.
"""

import os
import sys
import json
import logging
import queue
import threading
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import traceback

# Save original stdout/stderr before main.py modifies them
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import analysis functions from main
from main import (
    retrieve_and_index_papers,
    index_uploaded_paper,
    rag_pipeline,
    evidence_store,
    query_rewriter,
    rag_tool,
    rag_tool_instance,
    citation_verifier_tool,
    evidence_validator,
    validate_output_tool,
    read_context_tool,
    log_insight_tool,
    context_tool_wrapper,
    retrieval_agent,
    decomposition_agent,
    reasoning_agent,
    gap_novelty_agent,
    synthesis_agent,
    quality_control_agent,
    llm,
    MetricsTracker
)
from tasks import create_tasks
from crewai import Crew, Process
from research_context import ResearchContext
import time

# Restore original stdout/stderr for Flask
sys.stdout = _original_stdout
sys.stderr = _original_stderr

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global log queue for SSE streaming
log_queue = queue.Queue(maxsize=5000)

class LogBroadcaster:
    """Broadcaster for sending logs from global queue to multiple SSE clients."""
    def __init__(self):
        self.clients = []
        self._lock = threading.Lock()
    
    def subscribe(self):
        """Register a new client queue."""
        q = queue.Queue(maxsize=1000)
        with self._lock:
            self.clients.append(q)
        return q
    
    def unsubscribe(self, q):
        """Remove a client queue."""
        with self._lock:
            if q in self.clients:
                self.clients.remove(q)
    
    def broadcast(self, message):
        """Send message to all registered clients."""
        with self._lock:
            # Send to all clients, remove if full (stale)
            for q in list(self.clients):
                try:
                    q.put_nowait(message)
                except queue.Full:
                    self.clients.remove(q)

broadcaster = LogBroadcaster()

def log_broadcaster_worker():
    """Background thread that drains log_queue and broadcasts to clients."""
    logger.info("Starting log broadcaster worker thread")
    while True:
        try:
            # Block until message is available
            message = log_queue.get()
            broadcaster.broadcast(message)
            log_queue.task_done()
        except Exception as e:
            logger.error(f"Error in log broadcaster worker: {e}")
            time.sleep(0.1)

# Start broadcaster thread as daemon
broadcaster_thread = threading.Thread(target=log_broadcaster_worker, daemon=True)
broadcaster_thread.start()

class QueueHandler(logging.Handler):
    """Custom logging handler that pushes logs to a queue for SSE streaming."""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        try:
            log_entry = self.format(record)
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            # Create structured log message
            log_message = {
                'timestamp': timestamp,
                'level': record.levelname,
                'message': log_entry,
                'raw': record.getMessage()
            }
            
            # Add to queue (non-blocking)
            try:
                self.log_queue.put_nowait(json.dumps(log_message))
            except queue.Full:
                try:
                    self.log_queue.get_nowait()
                    self.log_queue.put_nowait(json.dumps(log_message))
                except:
                    pass
        except Exception:
            pass

# Import analysis functions from main
from main import (
    retrieve_and_index_papers,
    index_uploaded_paper,
    rag_pipeline,
    evidence_store,
    query_rewriter,
    rag_tool,
    rag_tool_instance,
    citation_verifier_tool,
    evidence_validator,
    validate_output_tool,
    read_context_tool,
    log_insight_tool,
    context_tool_wrapper,
    retrieval_agent,
    decomposition_agent,
    reasoning_agent,
    gap_novelty_agent,
    synthesis_agent,
    quality_control_agent,
    llm,
    MetricsTracker,
    TeeOutput  # Import TeeOutput for terminal logging
)
from tasks import create_tasks
from crewai import Crew, Process
from research_context import ResearchContext
from output_formatter import format_and_save_report  # Import output formatter
import time

def run_analysis_api(user_idea: str, selected_domains: list, paper_data: dict = None):
    """
    Run the multi-agent analysis and return structured results.
    This is the API-friendly version of run_analysis from main.py.
    
    Args:
        user_idea: Research idea/question
        selected_domains: List of research domains
        paper_data: Optional paper upload data
        
    Returns:
        dict: Structured analysis results
    """
    logger.info(f"="*80)
    logger.info(f"API ANALYSIS REQUEST")
    logger.info(f"Research Idea: {user_idea}")
    logger.info(f"Domains: {selected_domains}")
    logger.info(f"="*80)
    
    # Initialize metrics tracker
    metrics = MetricsTracker()
    metrics.log_input("research_idea", user_idea)
    metrics.log_input("selected_domains", selected_domains)
    analysis_start = time.time()
    
    # Save original stdout/stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    try:
        # 1. Initialize Context and Output Folders
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_folder = os.path.join('outputs', 'latest_research_session')  # Same as CLI
        
        # Create all output subfolders (same structure as main.py)
        review_folder = os.path.join(session_folder, 'review')
        terminal_folder = os.path.join(session_folder, 'terminal_output')
        metrics_folder = os.path.join(session_folder, 'metrics')
        final_report_folder = os.path.join(session_folder, 'final_report')
        
        os.makedirs(review_folder, exist_ok=True)
        os.makedirs(terminal_folder, exist_ok=True)
        os.makedirs(metrics_folder, exist_ok=True)
        os.makedirs(final_report_folder, exist_ok=True)
        
        # Define output files
        terminal_output_file = os.path.join(terminal_folder, 'terminal_output.txt')
        metrics_file = os.path.join(metrics_folder, 'metrics.json')
        final_report_file = os.path.join(final_report_folder, 'final_research_report.md')
        
        # Capture terminal output and push to SSE queue
        tee = TeeOutput(terminal_output_file, original_stdout, log_queue=log_queue)
        sys.stdout = tee
        sys.stderr = tee
        
        # Attach QueueHandler to root logger for SSE streaming
        queue_handler = QueueHandler(log_queue)
        queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
        
        logger.info(f"="*80)
        logger.info(f"API Session Output Folders Created")
        logger.info(f"Session folder: {session_folder}")
        logger.info(f"="*80)
        
        research_context = ResearchContext(session_folder)
        context_tool_wrapper.set_context(research_context)
        
        # 2. Index uploaded paper if provided
        if paper_data:
            logger.info("Processing uploaded paper data")
            added_paper = index_uploaded_paper(paper_data)
            if added_paper:
                logger.info(f"Indexed uploaded paper: {added_paper.get('title')}")
        
        # 3. Retrieve and index papers
        def hyde_generator(q):
            return llm.generate(f"Write a hypothetical scientific abstract for a paper about: {q}")
        
        logger.info("Starting paper retrieval and indexing")
        papers = retrieve_and_index_papers(user_idea, selected_domains)
        
        if not papers:
            return {
                "status": "error",
                "message": "No relevant papers found for the given research idea and domains.",
                "data": None
            }
        
        logger.info(f"Retrieved and indexed {len(papers)} papers")
        
        # 4. Configure RAG with HyDE
        rag_pipeline.hyde_generator = hyde_generator
        
        def augmented_search(query):
            results = rag_pipeline.hybrid_search(
                query, 
                k=5, 
                use_hyde=True, 
                generator_func=hyde_generator
            )
            if not results:
                return "INSUFFICIENT_EVIDENCE"
            
            lines = []
            for r in results:
                meta = r
                lines.append(
                    f"[{meta.get('handle', 'P?')}] {meta.get('title')} "
                    f"(Relevance: {meta.get('score', 0):.2f})\n{r.get('content')}"
                )
            return "\n\n".join(lines)
        
        rag_tool.run = augmented_search
        logger.info("Enabled HyDE for RAG Search tool")
        
        # 5. Assign tools to agents
        common_tools = [rag_tool_instance, read_context_tool, log_insight_tool]
        
        retrieval_agent.tools = common_tools
        decomposition_agent.tools = common_tools
        reasoning_agent.tools = common_tools
        gap_novelty_agent.tools = common_tools + [citation_verifier_tool]
        synthesis_agent.tools = common_tools
        quality_control_agent.tools = [
            rag_tool_instance, 
            validate_output_tool, 
            citation_verifier_tool, 
            read_context_tool
        ]
        
        # 6. Create tasks
        logger.info("Creating tasks for crew")
        tasks = create_tasks(user_idea, selected_domains)
        
        # 7. Initialize and run crew
        logger.info("Initializing crew with 6 agents")
        crew = Crew(
            agents=[
                retrieval_agent,
                decomposition_agent,
                reasoning_agent,
                gap_novelty_agent,
                synthesis_agent,
                quality_control_agent
            ],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            tracing=True
        )
        
        logger.info("Starting crew execution...")
        crew_start = time.time()
        result = crew.kickoff()
        crew_duration = time.time() - crew_start
        
        logger.info(f"Crew execution completed in {crew_duration:.2f}s")
        
        # 8. Collect task outputs
        task_outputs = {}
        for task in tasks:
            raw_out = getattr(task, 'output', None) or getattr(task, 'result', None)
            if hasattr(raw_out, 'raw'):
                raw_out = raw_out.raw
            if hasattr(raw_out, 'value'):
                raw_out = raw_out.value
            if raw_out:
                key = getattr(task.agent, 'role', task.description[:30])
                task_outputs[key] = str(raw_out)
        
        # 9. Validate output
        result_str = str(result)
        evidence_validator.validate_output(result_str)
        
        # 10. Structure agent outputs
        agent_outputs = {
            'retrieval': task_outputs.get('Retrieval Architect', ''),
            'decomposition': task_outputs.get('Literature Decomposition Specialist', ''),
            'reasoning': task_outputs.get('Cross-Paper Reasoning Analyst', ''),
            'gap_novelty': task_outputs.get('Research Gap & Novelty Auditor', ''),
            'synthesis': (
                task_outputs.get('Academic Editor & Fact Checker', '') or 
                task_outputs.get('Principal Investigator / Lead Author', '') or 
                result_str
            )
        }
        
        # 11. Get papers metadata
        papers_list = []
        if hasattr(rag_pipeline, 'metadata'):
            for handle, meta in rag_pipeline.metadata.items():
                papers_list.append({
                    'handle': handle,
                    'title': meta.get('title', ''),
                    'authors': meta.get('authors', ''),
                    'year': meta.get('year', ''),
                    'abstract': meta.get('abstract', '')
                })
        
        # 12. Save metrics
        analysis_duration = time.time() - analysis_start
        metrics.log_timing("total_analysis", analysis_duration)
        metrics.log_output("success", True)
        metrics.finalize()
        metrics.save(metrics_file)
        
        logger.info(f"Metrics saved to: {metrics_file}")
        
        # 13. Generate and save formatted report
        logger.info("Generating professionally formatted report...")
        professional_report = format_and_save_report(
            research_idea=user_idea,
            domains=selected_domains,
            agent_outputs=agent_outputs,
            output_file=final_report_file,
            available_papers=papers_list,
            metrics=metrics.metrics
        )
        
        # 14. Save detailed agent analysis (raw outputs)
        detailed_analysis_file = os.path.join(final_report_folder, 'detailed_agent_analysis.txt')
        try:
            with open(detailed_analysis_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("DETAILED AGENT ANALYSIS - RAW OUTPUTS\n")
                f.write("="*80 + "\n\n")
                
                for agent_name, output in agent_outputs.items():
                    f.write(f"\n{'='*80}\n")
                    f.write(f"AGENT: {agent_name.upper()}\n")
                    f.write(f"{'='*80}\n\n")
                    f.write(str(output) + "\n\n")
            
            logger.info(f"Detailed agent analysis saved to: {detailed_analysis_file}")
        except Exception as e:
            logger.error(f"Error saving detailed agent analysis: {e}")
        
        logger.info(f"Final report saved to: {final_report_file}")
        logger.info(f"Terminal output saved to: {terminal_output_file}")
        logger.info(f"="*80)
        logger.info(f"API ANALYSIS COMPLETE")
        logger.info(f"="*80)
        
        # Remove QueueHandler from root logger
        root_logger.removeHandler(queue_handler)
        queue_handler.close()
        
        # Restore stdout/stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        tee.close()
        
        return {
            "status": "success",
            "message": "Analysis completed successfully",
            "data": {
                "final_report": result_str,
                "agent_outputs": agent_outputs,
                "papers": papers_list,
                "metrics": {
                    "total_duration_seconds": analysis_duration,
                    "total_papers_retrieved": len(papers),
                    "total_agents": 6
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}")
        logger.error(traceback.format_exc())
        metrics.log_error("ANALYSIS_ERROR", str(e), traceback.format_exc())
        metrics.log_output("success", False)
        
        # Restore stdout/stderr on error
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        if 'tee' in locals():
            tee.close()
        
        return {
            "status": "error",
            "message": f"Analysis failed: {str(e)}",
            "data": None
        }

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Multi-Agent Literature Review API"
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Main analysis endpoint.
    
    Expected JSON payload:
    {
        "research_idea": "string",
        "selected_domains": ["string"],
        "paper_data": {
            "paper_sections": [...],
            "uploaded_papers": [...]
        }
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        research_idea = data.get('research_idea', '').strip()
        selected_domains = data.get('selected_domains', [])
        paper_data = data.get('paper_data', None)
        
        if not research_idea:
            return jsonify({
                "status": "error",
                "message": "research_idea is required"
            }), 400
        
        if not selected_domains or not isinstance(selected_domains, list):
            return jsonify({
                "status": "error",
                "message": "selected_domains must be a non-empty list"
            }), 400
        
        logger.info(f"Received analysis request: {research_idea[:50]}...")
        
        # Run analysis
        result = run_analysis_api(research_idea, selected_domains, paper_data)
        
        # Return appropriate status code
        if result["status"] == "success":
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in /api/analyze: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/api/logs/stream', methods=['GET'])
def stream_logs():
    """Server-Sent Events endpoint for real-time log streaming."""
    
    def generate():
        """Generator function that yields SSE-formatted log messages."""
        # Create a local queue for this specific client
        q = broadcaster.subscribe()
        
        # Send initial connection message immediately
        initial_msg = {
            'timestamp': datetime.now().strftime('%H:%M:%S.%f')[:-3],
            'level': 'INFO',
            'message': '=== Terminal Connected ===',
            'raw': 'Terminal Connected'
        }
        yield f"data: {json.dumps(initial_msg)}\n\n"
        
        try:
            while True:
                try:
                    # Non-blocking wait for messages with a shorter timeout for heartbeats
                    try:
                        # Shorter timeout for faster response to disconnections/heartbeats
                        log_msg = q.get(timeout=30) 
                        yield f"data: {log_msg}\n\n"
                    except queue.Empty:
                        # Send heartbeat if no message received for 1 second
                        # Using a comment format for heartbeat which is standard for SSE 
                        # to keep connection alive without triggering onmessage
                        yield ": keep-alive\n\n"
                except GeneratorExit:
                    # Client naturally disconnected (closed tab/window)
                    break
                except Exception as e:
                    # Other errors (e.g. connection reset)
                    break
        finally:
            # Always ensure the client is unsubscribed
            broadcaster.unsubscribe(q)
            # Use a slightly more descriptive log but don't spam stdout
            # logging.info("SSE client disconnected") # Already logged by broadcaster unsub
    
    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/api/outputs/agent-analysis', methods=['GET'])
def get_agent_analysis():
    """Get the detailed agent analysis file."""
    try:
        file_path = os.path.join('outputs', 'latest_research_session', 'final_report', 'detailed_agent_analysis.txt')
        
        if not os.path.exists(file_path):
            return jsonify({
                "status": "pending",
                "message": "Agent analysis not yet available"
            }), 202  # 202 Accepted (processing)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "content": content,
            "file_path": file_path
        }), 200
    except Exception as e:
        logger.error(f"Error reading agent analysis: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/outputs/final-report', methods=['GET'])
def get_final_report():
    """Get the final research report markdown file."""
    try:
        file_path = os.path.join('outputs', 'latest_research_session', 'final_report', 'final_research_report.md')
        
        if not os.path.exists(file_path):
            return jsonify({
                "status": "pending",
                "message": "Final report not yet available"
            }), 202  # 202 Accepted (processing)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "content": content,
            "file_path": file_path
        }), 200
    except Exception as e:
        logger.error(f"Error reading final report: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API information"""
    return jsonify({
        "service": "Multi-Agent Literature Review API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "analyze": "/api/analyze (POST)",
            "logs": "/api/logs/stream (GET, SSE)",
            "agent_analysis": "/api/outputs/agent-analysis (GET)",
            "final_report": "/api/outputs/final-report (GET)"
        },
        "documentation": "See README.md for API usage details"
    })

if __name__ == '__main__':
    logger.info("="*80)
    logger.info("Starting Flask API Server for Multi-Agent Literature Review")
    logger.info("="*80)
    logger.info(f"API will be available at: http://localhost:5000")
    logger.info(f"Health check: http://localhost:5000/api/health")
    logger.info(f"Analyze endpoint: http://localhost:5000/api/analyze")
    logger.info("="*80)
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,
        debug=True,  # Set to False for production
        threaded=True  # Enable threading for concurrent requests
    )
