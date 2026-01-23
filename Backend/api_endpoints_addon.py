# Additional API endpoints for validation and chat
# Add these to api_server.py before if __name__ == '__main__':

from validation_service import validate_research_idea, validate_domains
from chat_service import chat_with_context

@app.route('/api/validate-input', methods=['POST'])
def validate_input_endpoint():
    """Validate research input and provide suggestions."""
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        research_idea = data.get('research_idea', '')
        selected_domains = data.get('selected_domains', [])
        
        idea_validation = validate_research_idea(research_idea)
        domain_validation = None
        if selected_domains:
            domain_validation = validate_domains(selected_domains, research_idea)
        
        return jsonify({
            "status": "success",
            "validation": idea_validation,
            "domain_validation": domain_validation
        }), 200
    except Exception as e:
        logger.error(f"Error validating input: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """AI research assistant chat endpoint."""
    try:
        if not request.is_json:
            return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context')
        history = data.get('conversation_history', [])
        
        if not message:
            return jsonify({"status": "error", "message": "Message is required"}), 400
        
        result = chat_with_context(message, context, history)
        
        return jsonify({
            "status": "success",
            **result
        }), 200
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
