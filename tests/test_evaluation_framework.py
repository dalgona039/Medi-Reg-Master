import pytest
import sys
import os
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from evaluation.metrics import EvaluationMetrics
from evaluation.benchmark_framework import QueryTestCase, BenchmarkFramework


class TestEvaluationMetrics:
    
    def test_precision_at_k(self):
        retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        relevant = {'doc1', 'doc3', 'doc6'}
        
        assert EvaluationMetrics.precision_at_k(retrieved, relevant, 1) == 1.0
        
        assert abs(EvaluationMetrics.precision_at_k(retrieved, relevant, 3) - 2/3) < 0.001
        assert abs(EvaluationMetrics.precision_at_k(retrieved, relevant, 5) - 2/5) < 0.001
    
    def test_recall_at_k(self):
        retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
        relevant = {'doc1', 'doc3', 'doc6'}
        
        assert abs(EvaluationMetrics.recall_at_k(retrieved, relevant, 3) - 2/3) < 0.001
        assert abs(EvaluationMetrics.recall_at_k(retrieved, relevant, 5) - 2/3) < 0.001
    
    def test_f1_at_k(self):
        retrieved = ['doc1', 'doc2', 'doc3']
        relevant = {'doc1', 'doc3', 'doc6'}
        
        f1 = EvaluationMetrics.f1_at_k(retrieved, relevant, 3)
        assert abs(f1 - 2/3) < 0.001
    
    def test_ndcg_at_k(self):
        retrieved = ['doc1', 'doc2', 'doc3']
        relevant = {'doc1': 1.0, 'doc2': 0.5, 'doc4': 1.0}
        
        ndcg = EvaluationMetrics.ndcg_at_k(retrieved, relevant, 3)
        
        assert 0.0 <= ndcg <= 1.0
        print(f"NDCG@3 = {ndcg:.4f}")
    
    def test_mean_reciprocal_rank(self):
        retrieved_list = [
            ['doc1', 'doc2', 'doc3'],
            ['doc4', 'doc5', 'doc1'],
        ]
        relevant_list = [
            {'doc1', 'doc6'},
            {'doc1', 'doc7'}
        ]
        
        mrr = EvaluationMetrics.mean_reciprocal_rank(retrieved_list, relevant_list)
        assert abs(mrr - 0.667) < 0.01
        print(f"MRR = {mrr:.4f}")
    
    def test_citation_accuracy(self):
        answer = "답변입니다 [문서A, p.10] [문서B, p.5] [문서C, p.8]"
        ground_truth = {'문서A#p10', '문서B#p5', '문서D#p3'}
        
        accuracy, details = EvaluationMetrics.citation_accuracy(answer, ground_truth)
        
        assert abs(accuracy - 2/3) < 0.01
        assert details['correct'] == 2
        assert details['missing'] == 1
        assert details['extra'] == 1
        
        print(f"Citation Accuracy = {accuracy:.4f}")
        print(f"Details: {details}")
    
    def test_context_reduction_rate(self):
        flat_size = 10000
        tree_size = 800
        
        reduction = EvaluationMetrics.context_reduction_rate(flat_size, tree_size)
        assert abs(reduction - 0.92) < 0.01
        print(f"Context Reduction: {reduction*100:.1f}%")
    
    def test_latency_comparison(self):
        tree_latency = 500.0
        flat_latency = 800.0
        
        result = EvaluationMetrics.latency_comparison(tree_latency, flat_latency)
        
        assert result['tree_ms'] == 500.0
        assert result['flat_ms'] == 800.0
        assert abs(result['speedup'] - 1.6) < 0.01
        assert result['faster_system'] == 'TreeRAG'
        
        print(f"Latency: {result}")
    
    def test_faithfulness_score(self):
        answer = "인슐린은 혈당을 낮춥니다. 당뇨병 치료에 사용됩니다."
        source_contexts = [
            "인슐린은 혈당 수치를 감소시키는 호르몬입니다",
            "당뇨병 환자에게 인슐린 치료가 권장됩니다"
        ]
        
        result = EvaluationMetrics.faithfulness_score(answer, source_contexts, threshold=0.3)
        
        print(f"Faithfulness: {result}")
        assert 'score' in result
        assert 'faithful' in result
        assert 0.0 <= result['score'] <= 1.0
    
    def test_aggregate_metrics(self):
        results = [
            {'precision@3': 0.8, 'recall@3': 0.7, 'f1@3': 0.75},
            {'precision@3': 0.9, 'recall@3': 0.8, 'f1@3': 0.85},
            {'precision@3': 0.7, 'recall@3': 0.6, 'f1@3': 0.65},
        ]
        
        aggregated = EvaluationMetrics.aggregate_metrics(results)
        
        # Precision@3 평균 = (0.8 + 0.9 + 0.7) / 3 ≈ 0.8
        assert 'precision@3' in aggregated
        assert abs(aggregated['precision@3']['mean'] - 0.8) < 0.01
        
        print(f"Aggregated: {aggregated}")


class TestBenchmarkFramework:
    
    def test_query_test_case_creation(self):
        test_case = QueryTestCase(
            query="인슐린 저항성 치료는?",
            relevant_docs=['doc1_node5', 'doc1_node12'],
            relevant_scores={'doc1_node5': 1.0, 'doc1_node12': 0.8},
            expected_citations=['doc1#p10'],
            category='medical',
            domain='medical'
        )
        
        assert test_case.query == "인슐린 저항성 치료는?"
        assert len(test_case.relevant_docs) == 2
        assert test_case.category == 'medical'
        
 
        test_dict = test_case.to_dict()
        assert test_dict['query'] == test_case.query
    
    def test_benchmark_framework_initialization(self):
        framework = BenchmarkFramework()
        
        assert len(framework.test_cases) == 0
        assert len(framework.results) == 0
    
    def test_add_test_case(self):
        framework = BenchmarkFramework()
        
        test_case = QueryTestCase(
            query="테스트 질문",
            relevant_docs=['doc1'],
            category='test'
        )
        
        framework.add_test_case(test_case)
        
        assert len(framework.test_cases) == 1
        assert framework.test_cases[0].query == "테스트 질문"
    
    def test_load_test_cases_from_json(self):
        framework = BenchmarkFramework()
        
        json_path = os.path.join(
            os.path.dirname(__file__),
            'evaluation',
            'sample_test_cases.json'
        )
        
        if os.path.exists(json_path):
            framework.add_test_cases_from_json(json_path)
            
            assert len(framework.test_cases) > 0
            print(f"Loaded {len(framework.test_cases)} test cases")
        else:
            print(f"⚠️ Sample test cases not found at {json_path}")


class TestMetricsComprehensiveReport:
    
    def test_comprehensive_report(self):
        retrieval_metrics = {
            'precision@3': 0.85,
            'recall@3': 0.78,
            'f1@3': 0.81,
            'ndcg@3': 0.88
        }
        
        generation_metrics = {
            'citation_accuracy': 0.92,
            'faithfulness': {'score': 0.87, 'faithful': True}
        }
        
        efficiency_metrics = {
            'latency_ms': 450.5,
            'context_reduction': 0.91,
            'speedup': 1.6
        }
        
        report = EvaluationMetrics.comprehensive_report(
            retrieval_metrics,
            generation_metrics,
            efficiency_metrics
        )
        
        print("\n" + report)
        
        assert "Retrieval Quality" in report
        assert "Generation Quality" in report
        assert "Efficiency" in report
        assert "0.85" in report  # precision 값 포함


def test_metrics_integration():
    print("\n" + "="*60)
    print("🧪 PHASE 1-1: Evaluation Framework Integration Test")
    print("="*60 + "\n")
    
    # 가상의 실험 결과
    retrieved_docs = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
    relevant_docs = {'doc1', 'doc3', 'doc6', 'doc7'}
    relevant_scores = {'doc1': 1.0, 'doc2': 0.6, 'doc3': 0.9, 'doc6': 0.8, 'doc7': 0.7}
    
    print("📊 Retrieval Metrics:")
    print(f"  Precision@3: {EvaluationMetrics.precision_at_k(retrieved_docs, relevant_docs, 3):.4f}")
    print(f"  Recall@3: {EvaluationMetrics.recall_at_k(retrieved_docs, relevant_docs, 3):.4f}")
    print(f"  F1@3: {EvaluationMetrics.f1_at_k(retrieved_docs, relevant_docs, 3):.4f}")
    print(f"  NDCG@3: {EvaluationMetrics.ndcg_at_k(retrieved_docs, relevant_scores, 3):.4f}")
    
    print("\n⚡ Efficiency:")
    print(f"  Context Reduction: {EvaluationMetrics.context_reduction_rate(10000, 850)*100:.1f}%")
    
    latency = EvaluationMetrics.latency_comparison(500, 800)
    print(f"  Speedup: {latency['speedup']:.2f}x ({latency['faster_system']})")
    
    print("\n✅ All metrics computed successfully!")


if __name__ == "__main__":
    test_metrics_integration()
