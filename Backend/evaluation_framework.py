# evaluation_framework.py
"""
Comprehensive Evaluation Framework for RAG Systems

Implements:
- RAGAS metrics (faithfulness, answer relevancy, context precision/recall)
- Custom metrics for literature review quality
- Performance benchmarking
- Comparative analysis
"""

import logging
import time
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

# Try to import RAGAS
try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        context_relevancy
    )
    RAGAS_AVAILABLE = True
    logger.info("RAGAS evaluation library loaded successfully")
except ImportError:
    RAGAS_AVAILABLE = False
    logger.warning("RAGAS not available - using custom metrics only")


class CustomMetrics:
    """Custom metrics specific to literature review quality."""
    
    @staticmethod
    def citation_coverage(output_text: str, expected_handles: List[str]) -> float:
        """
        Measure what percentage of available evidence was cited.
        
        Args:
            output_text: Generated text
            expected_handles: List of available paper handles (P1, P2, etc.)
            
        Returns:
            Coverage score (0-1)
        """
        if not expected_handles:
            return 0.0
        
        cited_handles = set()
        for handle in expected_handles:
            if f"[{handle}]" in output_text:
                cited_handles.add(handle)
        
        coverage = len(cited_handles) / len(expected_handles)
        return coverage
    
    @staticmethod
    def citation_density(output_text: str) -> float:
        """
        Measure citation density (citations per 100 words).
        
        Args:
            output_text: Generated text
            
        Returns:
            Citations per 100 words
        """
        import re
        
        # Count citations [P#]
        citations = re.findall(r'\[P\d+\]', output_text)
        num_citations = len(set(citations))  # Unique citations
        
        # Count words
        words = output_text.split()
        num_words = len(words)
        
        if num_words == 0:
            return 0.0
        
        density = (num_citations / num_words) * 100
        return density
    
    @staticmethod
    def academic_rigor_score(output_text: str) -> Dict[str, Any]:
        """
        Assess academic rigor based on linguistic markers.
        
        Checks for:
        - Technical terminology
        - Comparative language
        - Hedging (uncertainty markers)
        - Quantitative data
        
        Returns:
            Dictionary with component scores
        """
        import re
        
        text_lower = output_text.lower()
        
        # Technical indicators
        technical_terms = [
            'methodology', 'framework', 'algorithm', 'model', 'approach',
            'evaluation', 'performance', 'accuracy', 'precision', 'recall',
            'dataset', 'baseline', 'experiment', 'hypothesis', 'results'
        ]
        tech_count = sum(1 for term in technical_terms if term in text_lower)
        tech_score = min(tech_count / 10, 1.0)  # Normalize to 0-1
        
        # Comparative language
        comparative_terms = [
            'compared to', 'versus', 'outperform', 'superior', 'inferior',
            'in contrast', 'whereas', 'while', 'however', 'although'
        ]
        comp_count = sum(1 for term in comparative_terms if term in text_lower)
        comp_score = min(comp_count / 5, 1.0)
        
        # Hedging (shows scientific caution)
        hedging_terms = [
            'may', 'might', 'could', 'possibly', 'potentially', 'suggest',
            'indicate', 'appear', 'seem', 'likely', 'tend to'
        ]
        hedge_count = sum(1 for term in hedging_terms if term in text_lower)
        hedge_score = min(hedge_count / 8, 1.0)
        
        # Quantitative data (numbers, percentages, metrics)
        numbers = re.findall(r'\d+\.?\d*\%?', output_text)
        quant_score = min(len(numbers) / 15, 1.0)
        
        # Overall rigor score (weighted average)
        overall = (tech_score * 0.3 + comp_score * 0.3 + 
                  hedge_score * 0.2 + quant_score * 0.2)
        
        return {
            "overall_rigor": round(overall, 3),
            "technical_terminology": round(tech_score, 3),
            "comparative_analysis": round(comp_score, 3),
            "scientific_hedging": round(hedge_score, 3),
            "quantitative_data": round(quant_score, 3)
        }
    
    @staticmethod
    def coherence_score(output_text: str) -> float:
        """
        Measure text coherence based on discourse markers.
        
        Returns:
            Coherence score (0-1)
        """
        text_lower = output_text.lower()
        
        # Discourse markers
        transitions = [
            'first', 'second', 'third', 'finally', 'furthermore', 'moreover',
            'additionally', 'in addition', 'however', 'nevertheless',
            'therefore', 'consequently', 'thus', 'hence', 'in conclusion'
        ]
        
        marker_count = sum(1 for marker in transitions if marker in text_lower)
        
        # Normalize by document length
        words = output_text.split()
        if len(words) < 100:
            return 0.5  # Too short to judge
        
        markers_per_100_words = (marker_count / len(words)) * 100
        
        # Ideal range: 2-5 markers per 100 words
        if 2 <= markers_per_100_words <= 5:
            score = 1.0
        elif markers_per_100_words < 2:
            score = markers_per_100_words / 2
        else:  # Too many markers
            score = max(0, 1.0 - (markers_per_100_words - 5) / 5)
        
        return round(score, 3)


class RAGEvaluator:
    """Main evaluation coordinator for RAG-based literature reviews."""
    
    def __init__(self, rag_pipeline, llm_client=None):
        self.rag_pipeline = rag_pipeline
        self.llm_client = llm_client
        self.custom_metrics = CustomMetrics()
        logger.info("RAG Evaluator initialized")
    
    def evaluate_retrieval(
        self, 
        queries: List[str], 
        expected_papers: List[List[str]] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Evaluate retrieval quality.
        
        Args:
            queries: List of test queries
            expected_papers: Optional list of expected paper handles for each query
            k: Number of results to retrieve
            
        Returns:
            Dictionary with retrieval metrics
        """
        logger.info(f"Evaluating retrieval on {len(queries)} queries")
        
        results = {
            "queries_evaluated": len(queries),
            "avg_retrieval_time": 0.0,
            "avg_results_returned": 0.0,
            "precision_at_k": [],
            "recall_at_k": []
        }
        
        total_time = 0.0
        total_results = 0
        
        for i, query in enumerate(queries):
            start_time = time.time()
            retrieved = self.rag_pipeline.hybrid_search(query, k=k)
            duration = time.time() - start_time
            
            total_time += duration
            total_results += len(retrieved)
            
            # Calculate precision/recall if expected papers provided
            if expected_papers and i < len(expected_papers):
                expected = set(expected_papers[i])
                retrieved_handles = set(r.get('handle', '') for r in retrieved)
                
                if expected:
                    precision = len(expected & retrieved_handles) / len(retrieved_handles) if retrieved_handles else 0
                    recall = len(expected & retrieved_handles) / len(expected)
                    
                    results["precision_at_k"].append(precision)
                    results["recall_at_k"].append(recall)
        
        results["avg_retrieval_time"] = round(total_time / len(queries), 4)
        results["avg_results_returned"] = round(total_results / len(queries), 2)
        
        if results["precision_at_k"]:
            results["mean_precision_at_k"] = round(np.mean(results["precision_at_k"]), 3)
            results["mean_recall_at_k"] = round(np.mean(results["recall_at_k"]), 3)
        
        logger.info(f"Retrieval evaluation complete")
        return results
    
    def evaluate_generation(
        self,
        generated_output: str,
        available_handles: List[str] = None,
        reference_output: str = None
    ) -> Dict[str, Any]:
        """
        Evaluate generated literature review quality.
        
        Args:
            generated_output: The generated text
            available_handles: List of paper handles that could be cited
            reference_output: Optional reference/gold standard output
            
        Returns:
            Dictionary with generation metrics
        """
        logger.info("Evaluating generated output quality")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "output_length": len(generated_output),
            "word_count": len(generated_output.split())
        }
        
        # Custom metrics
        if available_handles:
            results["citation_coverage"] = round(
                self.custom_metrics.citation_coverage(generated_output, available_handles), 3
            )
        
        results["citation_density"] = round(
            self.custom_metrics.citation_density(generated_output), 3
        )
        
        results["academic_rigor"] = self.custom_metrics.academic_rigor_score(generated_output)
        
        results["coherence_score"] = self.custom_metrics.coherence_score(generated_output)
        
        # RAGAS metrics (if available and LLM provided)
        if RAGAS_AVAILABLE and self.llm_client and reference_output:
            try:
                ragas_results = self._compute_ragas_metrics(
                    generated_output, 
                    reference_output,
                    available_handles
                )
                results["ragas_metrics"] = ragas_results
            except Exception as e:
                logger.warning(f"RAGAS evaluation failed: {e}")
        
        return results
    
    def _compute_ragas_metrics(
        self,
        generated: str,
        reference: str,
        context_handles: List[str]
    ) -> Dict[str, float]:
        """
        Compute RAGAS metrics.
        
        Note: This is a simplified version. Full RAGAS requires specific data formats.
        """
        # This would need proper RAGAS dataset format
        # Placeholder for structure
        results = {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_precision": 0.0,
            "note": "Full RAGAS implementation requires specific data format"
        }
        
        return results
    
    def benchmark_pipeline(self, test_queries: List[str], iterations: int = 3) -> Dict[str, Any]:
        """
        Benchmark RAG pipeline performance.
        
        Args:
            test_queries: List of test queries
            iterations: Number of iterations per query
            
        Returns:
            Performance benchmark results
        """
        logger.info(f"Benchmarking pipeline with {len(test_queries)} queries ({iterations} iterations)")
        
        timings = []
        
        for query in test_queries:
            query_timings = []
            for i in range(iterations):
                start = time.time()
                self.rag_pipeline.hybrid_search(query, k=5)
                duration = time.time() - start
                query_timings.append(duration)
            timings.append(query_timings)
        
        # Calculate statistics
        all_times = [t for query_times in timings for t in query_times]
        
        results = {
            "num_queries": len(test_queries),
            "iterations_per_query": iterations,
            "total_searches": len(all_times),
            "min_time": round(min(all_times), 4),
            "max_time": round(max(all_times), 4),
            "mean_time": round(np.mean(all_times), 4),
            "median_time": round(np.median(all_times), 4),
            "std_time": round(np.std(all_times), 4),
            "p95_time": round(np.percentile(all_times, 95), 4),
            "p99_time": round(np.percentile(all_times, 99), 4)
        }
        
        # Pipeline stats
        pipeline_stats = self.rag_pipeline.get_stats()
        results["pipeline_stats"] = pipeline_stats
        
        logger.info(f"Benchmark complete - Mean time: {results['mean_time']}s")
        
        return results
    
    def generate_report(self, evaluation_results: Dict[str, Any], output_file: str = None) -> str:
        """
        Generate comprehensive evaluation report.
        
        Args:
            evaluation_results: Combined evaluation results
            output_file: Optional file to save report
            
        Returns:
            Formatted report string
        """
        report_lines = [
            "=" * 80,
            "RAG SYSTEM EVALUATION REPORT",
            "=" * 80,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## RETRIEVAL PERFORMANCE",
            "-" * 80
        ]
        
        if "retrieval" in evaluation_results:
            ret = evaluation_results["retrieval"]
            report_lines.extend([
                f"Queries Evaluated: {ret.get('queries_evaluated', 0)}",
                f"Average Retrieval Time: {ret.get('avg_retrieval_time', 0):.4f}s",
                f"Average Results Returned: {ret.get('avg_results_returned', 0):.2f}",
            ])
            
            if "mean_precision_at_k" in ret:
                report_lines.extend([
                    f"Mean Precision@K: {ret['mean_precision_at_k']:.3f}",
                    f"Mean Recall@K: {ret['mean_recall_at_k']:.3f}",
                ])
        
        report_lines.extend([
            "",
            "## GENERATION QUALITY",
            "-" * 80
        ])
        
        if "generation" in evaluation_results:
            gen = evaluation_results["generation"]
            report_lines.extend([
                f"Output Length: {gen.get('word_count', 0)} words",
                f"Citation Coverage: {gen.get('citation_coverage', 0):.3f}",
                f"Citation Density: {gen.get('citation_density', 0):.2f} per 100 words",
                f"Coherence Score: {gen.get('coherence_score', 0):.3f}",
                "",
                "Academic Rigor Breakdown:",
            ])
            
            if "academic_rigor" in gen:
                rigor = gen["academic_rigor"]
                for key, value in rigor.items():
                    report_lines.append(f"  - {key.replace('_', ' ').title()}: {value:.3f}")
        
        report_lines.extend([
            "",
            "## PERFORMANCE BENCHMARK",
            "-" * 80
        ])
        
        if "benchmark" in evaluation_results:
            bench = evaluation_results["benchmark"]
            report_lines.extend([
                f"Total Searches: {bench.get('total_searches', 0)}",
                f"Mean Search Time: {bench.get('mean_time', 0):.4f}s",
                f"Median Search Time: {bench.get('median_time', 0):.4f}s",
                f"95th Percentile: {bench.get('p95_time', 0):.4f}s",
                f"99th Percentile: {bench.get('p99_time', 0):.4f}s",
            ])
            
            if "pipeline_stats" in bench:
                stats = bench["pipeline_stats"]
                report_lines.extend([
                    "",
                    "Pipeline Statistics:",
                    f"  - Total Searches: {stats.get('total_searches', 0)}",
                    f"  - Cache Hits: {stats.get('cache_hits', 0)}",
                    f"  - Total Chunks: {stats.get('total_chunks', 0)}",
                ])
        
        report_lines.append("=" * 80)
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Evaluation report saved to: {output_file}")
        
        return report


def run_comprehensive_evaluation(
    rag_pipeline,
    generated_output: str,
    test_queries: List[str] = None,
    available_handles: List[str] = None,
    output_dir: str = "outputs/latest_research_session/evaluation"
) -> Dict[str, Any]:
    """
    Run comprehensive evaluation of the RAG system.
    
    Args:
        rag_pipeline: RAG pipeline instance
        generated_output: Final generated literature review
        test_queries: Optional test queries for retrieval evaluation
        available_handles: Available paper handles for citation analysis
        output_dir: Directory to save evaluation results
        
    Returns:
        Complete evaluation results dictionary
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    evaluator = RAGEvaluator(rag_pipeline)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "evaluation_version": "1.0"
    }
    
    # 1. Generation quality
    logger.info("Evaluating generation quality...")
    results["generation"] = evaluator.evaluate_generation(
        generated_output,
        available_handles=available_handles
    )
    
    # 2. Retrieval performance (if test queries provided)
    if test_queries:
        logger.info("Evaluating retrieval performance...")
        results["retrieval"] = evaluator.evaluate_retrieval(test_queries, k=5)
    
    # 3. Performance benchmark
    logger.info("Running performance benchmark...")
    benchmark_queries = test_queries[:5] if test_queries else [
        "transformer models for NLP",
        "attention mechanisms in deep learning",
        "efficient neural networks"
    ]
    results["benchmark"] = evaluator.benchmark_pipeline(benchmark_queries, iterations=3)
    
    # 4. Generate report
    report = evaluator.generate_report(results, output_file=os.path.join(output_dir, "evaluation_report.txt"))
    
    # 5. Save JSON results
    json_file = os.path.join(output_dir, "evaluation_results.json")
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Evaluation complete. Results saved to {output_dir}")
    
    return results
