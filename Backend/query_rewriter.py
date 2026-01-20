# query_rewriter.py
"""
Query Rewriter - Expands user queries for better retrieval.

This module provides query expansion and rewriting to improve
paper retrieval quality by adding synonyms, domain-specific terms,
and temporal hints.
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

# Domain-specific synonym mappings
DOMAIN_SYNONYMS: Dict[str, List[str]] = {
    # NLP terms
    "transformer": ["transformer architecture", "attention mechanism", "self-attention"],
    "bert": ["BERT", "bidirectional encoder", "language model"],
    "gpt": ["GPT", "generative pre-trained", "autoregressive model"],
    "nlp": ["natural language processing", "NLP", "text processing", "language understanding"],
    "lightweight": ["efficient", "compact", "small", "compressed", "distilled"],
    "model compression": ["knowledge distillation", "pruning", "quantization", "model optimization"],
    
    # AI/ML terms
    "neural network": ["deep learning", "neural model", "artificial neural network"],
    "machine learning": ["ML", "statistical learning", "predictive modeling"],
    "deep learning": ["DL", "neural networks", "representation learning"],
    "classification": ["categorization", "detection", "prediction"],
    
    # Architecture terms
    "attention": ["self-attention", "multi-head attention", "attention mechanism"],
    "embedding": ["vector representation", "dense representation", "word embedding"],
    "fine-tuning": ["transfer learning", "domain adaptation", "model adaptation"],
    
    # Efficiency terms
    "efficient": ["lightweight", "fast", "low-latency", "resource-efficient"],
    "computational cost": ["inference time", "FLOPs", "memory usage", "latency"],
    "performance": ["accuracy", "F1 score", "benchmark results", "evaluation"],
}

# Domain keywords for expansion
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "Natural Language Processing": [
        "NLP", "text", "language model", "transformer", "BERT", "GPT",
        "tokenization", "embeddings", "sequence labeling"
    ],
    "Artificial Intelligence": [
        "AI", "machine learning", "deep learning", "neural network",
        "intelligent systems", "pattern recognition"
    ],
    "Computer Vision": [
        "image", "visual", "CNN", "object detection", "image classification",
        "computer vision", "visual recognition"
    ],
    "Machine Learning": [
        "ML", "supervised learning", "unsupervised learning", "classification",
        "regression", "clustering", "feature engineering"
    ],
    "Deep Learning": [
        "DL", "neural network", "backpropagation", "gradient descent",
        "activation function", "layer", "architecture"
    ]
}


class QueryRewriter:
    """Expands and rewrites queries for improved retrieval."""
    
    def __init__(self):
        self.synonyms = DOMAIN_SYNONYMS
        self.domain_keywords = DOMAIN_KEYWORDS
        logger.info("QueryRewriter initialized")
    
    def rewrite(self, query: str, domains: List[str] = None) -> str:
        """Rewrite query with synonym expansion and domain hints.
        
        Args:
            query: Original user query
            domains: List of selected domains for keyword injection
            
        Returns:
            Expanded query string
        """
        original_query = query
        
        # Step 1: Add synonym expansions
        expanded_terms = self._expand_synonyms(query)
        
        # Step 2: Add domain-specific keywords
        if domains:
            domain_terms = self._inject_domain_terms(domains)
            expanded_terms.extend(domain_terms)
        
        # Step 3: Combine into final query
        if expanded_terms:
            # Deduplicate while preserving order
            seen = set()
            unique_terms = []
            for term in expanded_terms:
                term_lower = term.lower()
                if term_lower not in seen:
                    seen.add(term_lower)
                    unique_terms.append(term)
            
            expanded_query = f"{query} {' '.join(unique_terms[:10])}"  # Limit expansion
        else:
            expanded_query = query
        
        logger.info(f"Query rewritten: '{original_query[:50]}...' -> '{expanded_query[:80]}...'")
        return expanded_query
    
    def _expand_synonyms(self, query: str) -> List[str]:
        """Expand query terms with synonyms."""
        expanded = []
        query_lower = query.lower()
        
        for term, synonyms in self.synonyms.items():
            if term.lower() in query_lower:
                # Add first 2 synonyms to avoid query explosion
                expanded.extend(synonyms[:2])
        
        return expanded
    
    def _inject_domain_terms(self, domains: List[str]) -> List[str]:
        """Inject relevant domain keywords."""
        domain_terms = []
        
        for domain in domains:
            domain_clean = domain.strip()
            if domain_clean in self.domain_keywords:
                # Add top 3 keywords per domain
                domain_terms.extend(self.domain_keywords[domain_clean][:3])
        
        return domain_terms
    
    def generate_sub_queries(self, query: str, domains: List[str] = None) -> List[str]:
        """Generate multiple sub-queries for comprehensive retrieval.
        
        Args:
            query: Original query
            domains: Selected domains
            
        Returns:
            List of diverse sub-queries
        """
        sub_queries = [query]  # Original query first
        
        # Add domain-focused variants
        if domains:
            for domain in domains[:2]:  # Top 2 domains
                sub_queries.append(f"{query} {domain}")
        
        # Add methodology-focused query
        method_terms = ["method", "approach", "technique", "algorithm"]
        for term in method_terms[:1]:
            sub_queries.append(f"{query} {term}")
        
        # Add recent work focus
        sub_queries.append(f"{query} recent advances 2023 2024")
        
        return sub_queries[:5]  # Limit to 5 sub-queries
    
    def extract_key_concepts(self, query: str) -> List[str]:
        """Extract key concepts from query for validation.
        
        Used to verify retrieved papers are topically relevant.
        """
        # Simple extraction: words > 4 chars that aren't stopwords
        stopwords = {
            "with", "from", "that", "this", "which", "have", "been", "were",
            "their", "what", "when", "where", "about", "through", "during",
            "before", "after", "above", "below", "between", "into", "achieve",
            "investigate", "explore", "analyze", "study", "research", "reduced",
            "competitive", "performance", "computational", "cost"
        }
        
        words = query.lower().split()
        concepts = [
            w for w in words 
            if len(w) > 4 and w not in stopwords and w.isalpha()
        ]
        
        return concepts[:5]  # Top 5 key concepts
    
    def validate_topic_relevance(self, query: str, text: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """Check if text is topically relevant to query.
        
        Args:
            query: Original query
            text: Text to check (e.g., paper abstract)
            threshold: Minimum relevance score (0-1)
            
        Returns:
            Tuple of (is_relevant, relevance_score)
        """
        key_concepts = self.extract_key_concepts(query)
        
        if not key_concepts:
            return (True, 1.0)  # If no concepts extracted, accept all
        
        text_lower = text.lower()
        matches = sum(1 for concept in key_concepts if concept in text_lower)
        score = matches / len(key_concepts)
        
        return (score >= threshold, score)


# Global instance
query_rewriter = QueryRewriter()
