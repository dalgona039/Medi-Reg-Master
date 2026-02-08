import time
import numpy as np
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import re


class EvaluationMetrics:
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        if k == 0:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
        
        return relevant_retrieved / k
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        if len(relevant) == 0:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
        
        return relevant_retrieved / len(relevant)
    
    @staticmethod
    def f1_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        precision = EvaluationMetrics.precision_at_k(retrieved, relevant, k)
        recall = EvaluationMetrics.recall_at_k(retrieved, relevant, k)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevant: Dict[str, float], k: int) -> float:
        if k == 0 or len(relevant) == 0:
            return 0.0
        
        dcg = 0.0
        for i, doc_id in enumerate(retrieved[:k]):
            if doc_id in relevant:
                dcg += relevant[doc_id] / np.log2(i + 2)
        
        ideal_scores = sorted(relevant.values(), reverse=True)[:k]
        ideal_scores = sorted(relevant.values(), reverse=True)[:k]
        idcg = sum(score / np.log2(i + 2) for i, score in enumerate(ideal_scores))
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def mean_reciprocal_rank(retrieved_list: List[List[str]], relevant_list: List[Set[str]]) -> float:
        if len(retrieved_list) != len(relevant_list):
            raise ValueError("retrieved_list and relevant_list must have same length")
        
        reciprocal_ranks = []
        
        for retrieved, relevant in zip(retrieved_list, relevant_list):
            for rank, doc_id in enumerate(retrieved, start=1):
                if doc_id in relevant:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                reciprocal_ranks.append(0.0)
        
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    @staticmethod
    def citation_accuracy(generated_answer: str, ground_truth_citations: Set[str]) -> Tuple[float, Dict[str, Any]]:
        citation_pattern = r'\[([^,\]]+),\s*p\.(\d+)\]'
        found_citations = re.findall(citation_pattern, generated_answer)
        
        found_set = set()
        for doc_name, page_num in found_citations:
            doc_name = doc_name.strip()
            citation_key = f"{doc_name}#p{page_num}"
            found_set.add(citation_key)
        
        if len(ground_truth_citations) == 0:
            accuracy = 1.0 if len(found_set) == 0 else 0.0
        else:
            correct_citations = found_set.intersection(ground_truth_citations)
            accuracy = len(correct_citations) / len(ground_truth_citations)
        
        return accuracy, {
            'found_citations': list(found_set),
            'expected_citations': list(ground_truth_citations),
            'correct': len(found_set.intersection(ground_truth_citations)),
            'missing': len(ground_truth_citations - found_set),
            'extra': len(found_set - ground_truth_citations)
        }
    
    @staticmethod
    def context_reduction_rate(flat_context_size: int, tree_context_size: int) -> float:
        if flat_context_size == 0:
            return 0.0
        
        reduction = 1.0 - (tree_context_size / flat_context_size)
        
        return max(0.0, reduction)
    
    @staticmethod
    def latency_comparison(tree_latency_ms: float, flat_latency_ms: float) -> Dict[str, float]:
        speedup = flat_latency_ms / tree_latency_ms if tree_latency_ms > 0 else 0.0
        
        return {
            'tree_ms': tree_latency_ms,
            'flat_ms': flat_latency_ms,
            'speedup': speedup,
            'difference_ms': flat_latency_ms - tree_latency_ms,
            'faster_system': 'TreeRAG' if speedup > 1.0 else 'FlatRAG'
        }
    
    @staticmethod
    def faithfulness_score(answer: str, source_contexts: List[str], threshold: float = 0.5) -> Dict[str, Any]:
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        
        if not sentences:
            return {
                'score': 1.0,
                'faithful': True,
                'low_confidence_sentences': []
            }
        
        sentence_scores = []
        low_confidence = []
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            
            max_overlap = 0.0
            for context in source_contexts:
                context_words = set(context.lower().split())
                overlap = len(sentence_words.intersection(context_words))
                overlap_ratio = overlap / len(sentence_words) if sentence_words else 0.0
                max_overlap = max(max_overlap, overlap_ratio)
            
            sentence_scores.append(max_overlap)
            
            if max_overlap < threshold:
                low_confidence.append(sentence)
        
        avg_score = np.mean(sentence_scores) if sentence_scores else 0.0
        
        return {
            'score': float(avg_score),
            'faithful': avg_score >= threshold,
            'low_confidence_sentences': low_confidence,
            'sentence_count': len(sentences),
            'low_confidence_count': len(low_confidence)
        }
    
    @staticmethod
    def aggregate_metrics(results: List[Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        if not results:
            return {}
        
        all_metrics = set()
        for result in results:
            all_metrics.update(result.keys())
        
        aggregated = {}
        
        for metric in all_metrics:
            values = [r[metric] for r in results if metric in r and isinstance(r[metric], (int, float))]
            
            if values:
                aggregated[metric] = {
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'count': len(values)
                }
        
        return aggregated
    
    @staticmethod
    def comprehensive_report(
        retrieval_metrics: Dict[str, float],
        generation_metrics: Dict[str, Any],
        efficiency_metrics: Dict[str, float]
    ) -> str:
        report = []
        report.append("=" * 60)
        report.append("TreeRAG Comprehensive Evaluation Report")
        report.append("=" * 60)
        report.append("")
        
        report.append("📊 Retrieval Quality:")
        report.append("-" * 60)
        for metric, value in retrieval_metrics.items():
            report.append(f"  {metric:30s}: {value:.4f}")
        report.append("")
        
        report.append("✍️  Generation Quality:")
        report.append("-" * 60)
        for metric, value in generation_metrics.items():
            if isinstance(value, dict):
                report.append(f"  {metric}:")
                for k, v in value.items():
                    report.append(f"    {k:28s}: {v}")
            else:
                report.append(f"  {metric:30s}: {value}")
        report.append("")
        
        report.append("⚡ Efficiency:")
        report.append("-" * 60)
        for metric, value in efficiency_metrics.items():
            if isinstance(value, (int, float)):
                report.append(f"  {metric:30s}: {value:.2f}")
            else:
                report.append(f"  {metric:30s}: {value}")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
