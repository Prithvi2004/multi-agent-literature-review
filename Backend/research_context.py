import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ResearchContext:
    """
    Persistent memory manager for the research session. 
    Allows agents to share insights, contradictions, and validation states.
    """
    
    def __init__(self, session_folder: str):
        self.file_path = os.path.join(session_folder, "research_context.json")
        self.data = {
            "session_start": datetime.now().isoformat(),
            "key_insights": [],
            "methodologies_identified": [],
            "contradictions_found": [],
            "research_gaps": [],
            "novelty_score": 0,
            "quality_checks": []
        }
        self._load()

    def add_insight(self, content: str, source_agent: str, citations: List[str] = None):
        entry = {
            "content": content,
            "agent": source_agent,
            "citations": citations or [],
            "timestamp": datetime.now().isoformat()
        }
        self.data["key_insights"].append(entry)
        self._save()
        logger.info(f"Insight added by {source_agent}")

    def add_gap(self, description: str, valid: bool = False):
        entry = {
            "description": description,
            "validated": valid,
            "timestamp": datetime.now().isoformat()
        }
        self.data["research_gaps"].append(entry)
        self._save()

    def log_quality_check(self, agent: str, status: str, comments: str):
        entry = {
            "agent": agent,
            "status": status, # PASS / FAIL / WARN
            "comments": comments,
            "timestamp": datetime.now().isoformat()
        }
        self.data["quality_checks"].append(entry)
        self._save()

    def get_context_summary(self) -> str:
        """Return a string summary of current knowns/unknowns."""
        summary = ["### Research Context Snapshot"]
        
        if self.data["key_insights"]:
            summary.append(f"**Insights ({len(self.data['key_insights'])}):**")
            for i in self.data["key_insights"][-5:]: # Last 5
                summary.append(f"- {i['content']} (Source: {i['agent']})")
        
        if self.data["research_gaps"]:
            summary.append(f"**Identified Gaps:**")
            for g in self.data["research_gaps"]:
                summary.append(f"- {g['description']} (Valid: {g['validated']})")
                
        return "\n".join(summary)

    def _save(self):
        try:
            with open(self.file_path, "w", encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save context: {e}")

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding='utf-8') as f:
                    self.data = json.load(f)
            except Exception:
                pass
