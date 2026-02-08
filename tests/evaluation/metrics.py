import time
import numpy as np
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import re


class EvaluationMetrics:
    """
    RAG 시스템 평가를 위한 종합 메트릭 클래스
    
    석사 연구 기준:
    - Retrieval: Precision@K, Recall@K, F1@K, NDCG@K
    - Generation: Faithfulness, Citation Accuracy
    - Efficiency: Latency, Token Reduction Rate
    """
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        """
        Precision@K: 상위 K개 중 정답 비율
        
        Formula: P@K = |retrieved[:k] ∩ relevant| / k
        
        Args:
            retrieved: 시스템이 반환한 문서 ID 리스트 (순서 중요)
            relevant: 정답 문서 ID 집합
            k: 상위 몇 개를 볼 것인가
            
        Returns:
            0.0 ~ 1.0 사이의 precision 값
            
        Example:
            retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
            relevant = {'doc1', 'doc3', 'doc6'}
            precision_at_k(retrieved, relevant, 3) = 2/3 = 0.667
        """
        if k == 0:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
        
        return relevant_retrieved / k
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        """
        Recall@K: 정답 중 상위 K개에서 찾은 비율
        
        Formula: R@K = |retrieved[:k] ∩ relevant| / |relevant|
        
        Args:
            retrieved: 시스템이 반환한 문서 ID 리스트
            relevant: 정답 문서 ID 집합
            k: 상위 몇 개를 볼 것인가
            
        Returns:
            0.0 ~ 1.0 사이의 recall 값
            
        Example:
            retrieved = ['doc1', 'doc2', 'doc3']
            relevant = {'doc1', 'doc3', 'doc6'}
            recall_at_k(retrieved, relevant, 3) = 2/3 = 0.667
        """
        if len(relevant) == 0:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        relevant_retrieved = sum(1 for doc in retrieved_at_k if doc in relevant)
        
        return relevant_retrieved / len(relevant)
    
    @staticmethod
    def f1_at_k(retrieved: List[str], relevant: Set[str], k: int) -> float:
        """
        F1@K: Precision과 Recall의 조화평균
        
        Formula: F1@K = 2 * (P@K * R@K) / (P@K + R@K)
        
        Args:
            retrieved: 시스템이 반환한 문서 ID 리스트
            relevant: 정답 문서 ID 집합
            k: 상위 몇 개를 볼 것인가
            
        Returns:
            0.0 ~ 1.0 사이의 F1 값
        """
        precision = EvaluationMetrics.precision_at_k(retrieved, relevant, k)
        recall = EvaluationMetrics.recall_at_k(retrieved, relevant, k)
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevant: Dict[str, float], k: int) -> float:
        """
        NDCG@K: Normalized Discounted Cumulative Gain
        
        순서를 고려한 랭킹 평가 (상위일수록 중요)
        
        Formula:
            DCG@K = Σ(rel_i / log2(i+1)) for i in 1..k
            NDCG@K = DCG@K / IDCG@K
        
        Args:
            retrieved: 시스템이 반환한 문서 ID 리스트
            relevant: {doc_id: relevance_score} 형태의 정답 (0.0~1.0)
            k: 상위 몇 개를 볼 것인가
            
        Returns:
            0.0 ~ 1.0 사이의 NDCG 값
            
        Example:
            retrieved = ['doc1', 'doc2', 'doc3']
            relevant = {'doc1': 1.0, 'doc2': 0.5, 'doc4': 1.0}
            ndcg_at_k(retrieved, relevant, 3) ≈ 0.85
        """
        if k == 0 or len(relevant) == 0:
            return 0.0
        
        # DCG 계산
        dcg = 0.0
        for i, doc_id in enumerate(retrieved[:k]):
            if doc_id in relevant:
                # i+2: 순위는 1부터 시작, log2(1)=0 방지
                dcg += relevant[doc_id] / np.log2(i + 2)
        
        # IDCG 계산 (이상적인 순서로 정렬했을 때)
        ideal_scores = sorted(relevant.values(), reverse=True)[:k]
        idcg = sum(score / np.log2(i + 2) for i, score in enumerate(ideal_scores))
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def mean_reciprocal_rank(retrieved_list: List[List[str]], relevant_list: List[Set[str]]) -> float:
        """
        MRR: Mean Reciprocal Rank
        
        첫 번째 정답이 몇 번째 순위에 나타나는가?
        
        Formula: MRR = (1/|Q|) * Σ(1/rank_i)
        
        Args:
            retrieved_list: 각 쿼리별 반환 문서 리스트들
            relevant_list: 각 쿼리별 정답 집합들
            
        Returns:
            0.0 ~ 1.0 사이의 MRR 값
            
        Example:
            retrieved_list = [
                ['doc1', 'doc2', 'doc3'],  # 첫 정답 위치: 1 (rank=1)
                ['doc4', 'doc5', 'doc1'],  # 첫 정답 위치: 3 (rank=3)
            ]
            relevant_list = [{'doc1', 'doc6'}, {'doc1', 'doc7'}]
            mrr = (1/1 + 1/3) / 2 = 0.667
        """
        if len(retrieved_list) != len(relevant_list):
            raise ValueError("retrieved_list and relevant_list must have same length")
        
        reciprocal_ranks = []
        
        for retrieved, relevant in zip(retrieved_list, relevant_list):
            for rank, doc_id in enumerate(retrieved, start=1):
                if doc_id in relevant:
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                # 정답을 찾지 못한 경우
                reciprocal_ranks.append(0.0)
        
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    @staticmethod
    def citation_accuracy(generated_answer: str, ground_truth_citations: Set[str]) -> Tuple[float, Dict[str, Any]]:
        """
        Citation Accuracy: 생성된 답변의 인용 정확도
        
        TreeRAG의 핵심 강점인 page-level citation 평가
        
        Args:
            generated_answer: 시스템이 생성한 답변
            ground_truth_citations: 정답 인용 집합 (예: {'doc1#p10', 'doc2#p5'})
            
        Returns:
            accuracy (float): 0.0~1.0
            details (dict): 세부 정보
            
        Example:
            answer = "답변입니다 [문서A, p.10] [문서B, p.5]"
            ground_truth = {'문서A#p10', '문서B#p5', '문서C#p3'}
            accuracy = 2/3 = 0.667 (2개 정확히 인용, 1개 놓침)
        """
        # 답변에서 인용 추출 패턴: [문서명, p.X] 또는 [Document, p.X]
        citation_pattern = r'\[([^,\]]+),\s*p\.(\d+)\]'
        found_citations = re.findall(citation_pattern, generated_answer)
        
        # 인용을 'doc_name#pX' 형식으로 정규화
        found_set = set()
        for doc_name, page_num in found_citations:
            doc_name = doc_name.strip()
            citation_key = f"{doc_name}#p{page_num}"
            found_set.add(citation_key)
        
        # 정확도 계산
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
        """
        Context Reduction Rate: TreeRAG의 컨텍스트 감소율
        
        TreeRAG의 핵심 주장: "90%+ 컨텍스트 감소"를 검증
        
        Formula: reduction_rate = 1 - (tree_size / flat_size)
        
        Args:
            flat_context_size: Flat RAG의 컨텍스트 크기 (tokens)
            tree_context_size: TreeRAG의 컨텍스트 크기 (tokens)
            
        Returns:
            0.0 ~ 1.0 사이의 감소율 (0.9 = 90% 감소)
            
        Example:
            flat_size = 10000 tokens
            tree_size = 800 tokens
            reduction = 1 - (800/10000) = 0.92 (92% 감소)
        """
        if flat_context_size == 0:
            return 0.0
        
        reduction = 1.0 - (tree_context_size / flat_context_size)
        
        return max(0.0, reduction)  # 음수 방지
    
    @staticmethod
    def latency_comparison(tree_latency_ms: float, flat_latency_ms: float) -> Dict[str, float]:
        """
        Latency Comparison: TreeRAG vs Flat RAG 응답속도 비교
        
        Args:
            tree_latency_ms: TreeRAG 응답시간 (밀리초)
            flat_latency_ms: Flat RAG 응답시간 (밀리초)
            
        Returns:
            {
                'tree_ms': TreeRAG 시간,
                'flat_ms': Flat RAG 시간,
                'speedup': 배속 (>1이면 TreeRAG가 빠름),
                'difference_ms': 차이 (ms)
            }
        """
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
        """
        Faithfulness Score: 답변이 소스에 충실한가?
        
        Hallucination 감지 - 기존 hallucination_detector 활용
        
        Args:
            answer: 생성된 답변
            source_contexts: 소스 문서 컨텍스트들
            threshold: 신뢰도 임계값
            
        Returns:
            {
                'score': 0.0~1.0,
                'faithful': boolean,
                'low_confidence_sentences': List[str]
            }
        """
        # 문장 단위로 분리
        sentences = [s.strip() for s in answer.split('.') if s.strip()]
        
        if not sentences:
            return {
                'score': 1.0,
                'faithful': True,
                'low_confidence_sentences': []
            }
        
        # 각 문장별 신뢰도 계산 (간단한 word overlap 기반)
        sentence_scores = []
        low_confidence = []
        
        for sentence in sentences:
            # 문장의 단어들이 소스 컨텍스트에 얼마나 존재하는가?
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
        
        # 전체 faithfulness score
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
        """
        여러 쿼리의 결과를 집계하여 평균, 표준편차 계산
        
        Args:
            results: 각 쿼리별 메트릭 딕셔너리 리스트
            
        Returns:
            {
                'metric_name': {
                    'mean': float,
                    'std': float,
                    'min': float,
                    'max': float
                }
            }
        """
        if not results:
            return {}
        
        # 모든 메트릭 이름 수집
        all_metrics = set()
        for result in results:
            all_metrics.update(result.keys())
        
        # 각 메트릭별 통계 계산
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
        """
        종합 평가 리포트 생성
        
        Args:
            retrieval_metrics: Precision, Recall, F1, NDCG 등
            generation_metrics: Faithfulness, Citation accuracy 등
            efficiency_metrics: Latency, Context reduction 등
            
        Returns:
            사람이 읽기 쉬운 형태의 종합 리포트
        """
        report = []
        report.append("=" * 60)
        report.append("TreeRAG Comprehensive Evaluation Report")
        report.append("=" * 60)
        report.append("")
        
        # Retrieval Quality
        report.append("📊 Retrieval Quality:")
        report.append("-" * 60)
        for metric, value in retrieval_metrics.items():
            report.append(f"  {metric:30s}: {value:.4f}")
        report.append("")
        
        # Generation Quality
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
        
        # Efficiency
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
