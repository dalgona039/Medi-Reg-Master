
import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from src.core.domain_benchmark import (
    DocumentDomain,
    DomainMetrics,
    BenchmarkQuestion,
    BenchmarkResult,
    BenchmarkReport,
    DomainClassifier,
    AnswerEvaluator,
    BenchmarkDataset,
    DomainBenchmark
)


class TestDocumentDomain:
    
    def test_from_string_valid(self):
        assert DocumentDomain.from_string("medical") == DocumentDomain.MEDICAL
        assert DocumentDomain.from_string("legal") == DocumentDomain.LEGAL
        assert DocumentDomain.from_string("technical") == DocumentDomain.TECHNICAL
        assert DocumentDomain.from_string("academic") == DocumentDomain.ACADEMIC
    
    def test_from_string_invalid(self):
        assert DocumentDomain.from_string("unknown") == DocumentDomain.GENERAL
        assert DocumentDomain.from_string("") == DocumentDomain.GENERAL
    
    def test_from_string_case_insensitive(self):
        assert DocumentDomain.from_string("MEDICAL") == DocumentDomain.MEDICAL
        assert DocumentDomain.from_string("Legal") == DocumentDomain.LEGAL


class TestDomainMetrics:
    
    def test_metrics_creation(self):
        metrics = DomainMetrics(
            domain=DocumentDomain.MEDICAL,
            terminology_coverage=0.85,
            precision=0.9,
            recall=0.8
        )
        assert metrics.domain == DocumentDomain.MEDICAL
        assert metrics.terminology_coverage == 0.85
        assert metrics.precision == 0.9
    
    def test_to_dict(self):
        metrics = DomainMetrics(
            domain=DocumentDomain.LEGAL,
            precision=0.75,
            f1_score=0.78
        )
        d = metrics.to_dict()
        assert d["domain"] == "legal"
        assert d["precision"] == 0.75
        assert d["f1_score"] == 0.78
    
    def test_from_dict(self):
        data = {
            "domain": "technical",
            "precision": 0.85,
            "recall": 0.80,
            "response_time_ms": 150.5
        }
        metrics = DomainMetrics.from_dict(data)
        assert metrics.domain == DocumentDomain.TECHNICAL
        assert metrics.precision == 0.85
        assert metrics.response_time_ms == 150.5


class TestBenchmarkQuestion:
    
    def test_question_creation(self):
        q = BenchmarkQuestion(
            id="q1",
            question="What is the main topic?",
            expected_answer="The document discusses...",
            domain=DocumentDomain.ACADEMIC
        )
        assert q.id == "q1"
        assert q.difficulty == "medium"  # Default
        assert not q.requires_reasoning  # Default
    
    def test_to_dict(self):
        q = BenchmarkQuestion(
            id="q2",
            question="Test question",
            expected_answer="Expected",
            domain=DocumentDomain.MEDICAL,
            difficulty="hard",
            requires_reasoning=True,
            expected_sections=["Section 1", "Section 2"]
        )
        d = q.to_dict()
        assert d["id"] == "q2"
        assert d["domain"] == "medical"
        assert d["difficulty"] == "hard"
        assert d["requires_reasoning"] is True
        assert len(d["expected_sections"]) == 2
    
    def test_from_dict(self):
        data = {
            "id": "q3",
            "question": "From dict question",
            "expected_answer": "From dict answer",
            "domain": "legal",
            "difficulty": "easy"
        }
        q = BenchmarkQuestion.from_dict(data)
        assert q.id == "q3"
        assert q.domain == DocumentDomain.LEGAL
        assert q.difficulty == "easy"


class TestBenchmarkResult:
    
    def test_result_creation(self):
        result = BenchmarkResult(
            question_id="q1",
            actual_answer="The answer is...",
            is_correct=True,
            partial_score=0.9,
            sections_found=["Intro", "Methods"],
            section_recall=1.0,
            response_time_ms=150.0,
            has_hallucination=False
        )
        assert result.is_correct
        assert result.partial_score == 0.9
        assert len(result.sections_found) == 2
    
    def test_to_dict_truncates_answer(self):
        long_answer = "A" * 1000
        result = BenchmarkResult(
            question_id="q1",
            actual_answer=long_answer,
            is_correct=True,
            partial_score=1.0,
            sections_found=[],
            section_recall=0.0,
            response_time_ms=100.0,
            has_hallucination=False
        )
        d = result.to_dict()
        assert len(d["actual_answer"]) <= 500


class TestBenchmarkReport:
    
    def test_report_creation(self):
        report = BenchmarkReport(
            domain=DocumentDomain.TECHNICAL,
            document_name="test_doc",
            total_questions=10,
            correct_count=8,
            partial_score_avg=0.85,
            section_recall_avg=0.9,
            response_time_avg_ms=120.0,
            hallucination_rate=0.1,
            reasoning_success_rate=0.7,
            results=[]
        )
        assert report.accuracy == 0.8
        assert report.run_timestamp  # Auto-generated
    
    def test_accuracy_zero_questions(self):
        report = BenchmarkReport(
            domain=DocumentDomain.GENERAL,
            document_name="empty",
            total_questions=0,
            correct_count=0,
            partial_score_avg=0,
            section_recall_avg=0,
            response_time_avg_ms=0,
            hallucination_rate=0,
            reasoning_success_rate=0,
            results=[]
        )
        assert report.accuracy == 0.0
    
    def test_to_dict(self):
        report = BenchmarkReport(
            domain=DocumentDomain.MEDICAL,
            document_name="medical_doc",
            total_questions=5,
            correct_count=4,
            partial_score_avg=0.9,
            section_recall_avg=0.85,
            response_time_avg_ms=200.0,
            hallucination_rate=0.05,
            reasoning_success_rate=0.8,
            results=[]
        )
        d = report.to_dict()
        assert d["domain"] == "medical"
        assert d["accuracy"] == 0.8
        assert "results" in d


class TestDomainClassifier:
    
    def test_classify_medical(self):
        text = "환자의 진단 결과 치료가 필요합니다. 증상은 다음과 같습니다."
        domain, confidence = DomainClassifier.classify(text)
        assert domain == DocumentDomain.MEDICAL
        assert confidence > 0.5
    
    def test_classify_legal(self):
        text = "본 계약의 조항에 따라 법률적 규정을 준수해야 합니다."
        domain, confidence = DomainClassifier.classify(text)
        assert domain == DocumentDomain.LEGAL
        assert confidence > 0.5
    
    def test_classify_technical(self):
        text = "시스템 아키텍처와 API 인터페이스 설계에 대한 알고리즘"
        domain, confidence = DomainClassifier.classify(text)
        assert domain == DocumentDomain.TECHNICAL
        assert confidence > 0.5
    
    def test_classify_academic(self):
        text = "본 연구의 가설을 검증하기 위한 실험 방법론과 분석 결과"
        domain, confidence = DomainClassifier.classify(text)
        assert domain == DocumentDomain.ACADEMIC
        assert confidence > 0.5
    
    def test_classify_general_when_no_keywords(self):
        text = "Hello world, this is a simple generic text."
        domain, confidence = DomainClassifier.classify(text)
        assert domain == DocumentDomain.GENERAL
    
    def test_classify_with_title(self):
        text = "일반 내용"
        title = "의공학 개론 보고서"
        domain, confidence = DomainClassifier.classify(text, title)
        assert domain == DocumentDomain.MEDICAL
    
    @patch("src.core.domain_benchmark.Config")
    def test_classify_with_llm(self, mock_config):
        mock_response = Mock()
        mock_response.text = '{"domain": "medical", "confidence": 0.95, "reasoning": "Healthcare content"}'
        mock_config.CLIENT.models.generate_content.return_value = mock_response
        
        domain, confidence = DomainClassifier.classify_with_llm(
            "환자 진단 관련 내용", "임상 보고서"
        )
        
        assert domain == DocumentDomain.MEDICAL
        assert confidence == 0.95


class TestAnswerEvaluator:
    
    def test_compute_similarity_identical(self):
        similarity = AnswerEvaluator.compute_similarity(
            "The answer is 42",
            "The answer is 42"
        )
        assert similarity == 1.0
    
    def test_compute_similarity_partial(self):
        similarity = AnswerEvaluator.compute_similarity(
            "The answer is approximately 42",
            "The answer is 42"
        )
        assert 0.3 < similarity < 1.0  # ngram overlap varies based on text length
    
    def test_compute_similarity_different(self):
        similarity = AnswerEvaluator.compute_similarity(
            "Completely different text",
            "Nothing similar here"
        )
        assert similarity < 0.5
    
    def test_compute_similarity_empty(self):
        assert AnswerEvaluator.compute_similarity("", "text") == 0.0
        assert AnswerEvaluator.compute_similarity("text", "") == 0.0
    
    def test_compute_keyword_recall_all_found(self):
        recall = AnswerEvaluator.compute_keyword_recall(
            "The patient needs treatment and diagnosis",
            ["patient", "treatment", "diagnosis"]
        )
        assert recall == 1.0
    
    def test_compute_keyword_recall_partial(self):
        recall = AnswerEvaluator.compute_keyword_recall(
            "The patient needs treatment",
            ["patient", "treatment", "diagnosis", "prognosis"]
        )
        assert recall == 0.5
    
    def test_compute_keyword_recall_empty_keywords(self):
        recall = AnswerEvaluator.compute_keyword_recall(
            "Some text",
            []
        )
        assert recall == 1.0
    
    @patch("src.core.domain_benchmark.Config")
    def test_evaluate_with_llm(self, mock_config):
        mock_response = Mock()
        mock_response.text = '{"is_correct": true, "partial_score": 0.85, "explanation": "Good answer"}'
        mock_config.CLIENT.models.generate_content.return_value = mock_response
        
        is_correct, score, explanation = AnswerEvaluator.evaluate_with_llm(
            question="What is X?",
            actual="X is Y",
            expected="X is Y or Z"
        )
        
        assert is_correct is True
        assert score == 0.85
        assert "Good" in explanation


class TestBenchmarkDataset:
    """Tests for BenchmarkDataset."""
    
    @pytest.fixture
    def temp_dataset_dir(self, tmp_path):
        return str(tmp_path / "benchmarks")
    
    def test_add_question(self, temp_dataset_dir):
        dataset = BenchmarkDataset(temp_dataset_dir)
        
        q = dataset.add_question(
            domain=DocumentDomain.MEDICAL,
            question="What is the diagnosis?",
            expected_answer="The diagnosis is...",
            difficulty="hard"
        )
        
        assert q.id is not None
        assert q.domain == DocumentDomain.MEDICAL
        assert len(dataset.questions["medical"]) == 1
    
    def test_save_and_load_dataset(self, temp_dataset_dir):
        dataset = BenchmarkDataset(temp_dataset_dir)
        
        questions = [
            BenchmarkQuestion(
                id="q1",
                question="Question 1",
                expected_answer="Answer 1",
                domain=DocumentDomain.LEGAL
            ),
            BenchmarkQuestion(
                id="q2",
                question="Question 2",
                expected_answer="Answer 2",
                domain=DocumentDomain.LEGAL
            )
        ]
        
        success = dataset.save_dataset(DocumentDomain.LEGAL, questions)
        assert success
        
        # Reload
        dataset2 = BenchmarkDataset(temp_dataset_dir)
        loaded = dataset2.load_dataset(DocumentDomain.LEGAL)
        
        assert len(loaded) == 2
        assert loaded[0].id == "q1"
        assert loaded[1].id == "q2"
    
    def test_load_nonexistent_dataset(self, temp_dataset_dir):
        dataset = BenchmarkDataset(temp_dataset_dir)
        loaded = dataset.load_dataset(DocumentDomain.FINANCIAL)
        assert loaded == []
    
    def test_get_all_domains(self, temp_dataset_dir):
        dataset = BenchmarkDataset(temp_dataset_dir)
        
        dataset.add_question(
            domain=DocumentDomain.MEDICAL,
            question="Q1",
            expected_answer="A1"
        )
        dataset.add_question(
            domain=DocumentDomain.LEGAL,
            question="Q2",
            expected_answer="A2"
        )
        
        domains = dataset.get_all_domains()
        assert DocumentDomain.MEDICAL in domains
        assert DocumentDomain.LEGAL in domains


class TestDomainBenchmark:
    """Tests for DomainBenchmark class."""
    
    @pytest.fixture
    def benchmark(self, tmp_path):
        dataset_dir = str(tmp_path / "benchmarks")
        dataset = BenchmarkDataset(dataset_dir)
        return DomainBenchmark(dataset)
    
    @pytest.fixture
    def sample_questions(self):
        return [
            BenchmarkQuestion(
                id="q1",
                question="What is the main topic?",
                expected_answer="The main topic is X",
                domain=DocumentDomain.GENERAL,
                difficulty="easy"
            ),
            BenchmarkQuestion(
                id="q2",
                question="Explain the methodology",
                expected_answer="The methodology involves...",
                domain=DocumentDomain.GENERAL,
                difficulty="medium"
            )
        ]
    
    def test_evaluate_question(self, benchmark):
        # Setup mocks
        mock_reasoner_instance = Mock()
        mock_reasoner_instance.answer_question.return_value = {
            "answer": "The main topic is X and Y",
            "sources": [
                {"title": "Introduction", "summary": "Intro content"},
                {"title": "Methods", "summary": "Methods content"}
            ]
        }
        
        mock_detector_instance = Mock()
        mock_detector_instance.detect.return_value = {"has_hallucination": False}
        
        question = BenchmarkQuestion(
            id="q1",
            question="What is the main topic?",
            expected_answer="The main topic is X",
            domain=DocumentDomain.GENERAL
        )
        
        with patch.object(AnswerEvaluator, 'evaluate_with_llm', return_value=(True, 0.9, "Good")), \
             patch('src.core.reasoner.TreeRAGReasoner', return_value=mock_reasoner_instance):
            result = benchmark._evaluate_question(
                document_name="test_doc",
                question=question,
                hallucination_detector=mock_detector_instance,
                use_reasoning=False
            )
        
        assert result.question_id == "q1"
        assert result.is_correct
        assert result.partial_score == 0.9
        assert len(result.sections_found) == 2
        assert not result.has_hallucination
    
    def test_compare_domains(self, benchmark):
        # Add some results manually
        benchmark.results["test_doc"] = [
            BenchmarkReport(
                domain=DocumentDomain.MEDICAL,
                document_name="test_doc",
                total_questions=10,
                correct_count=8,
                partial_score_avg=0.85,
                section_recall_avg=0.9,
                response_time_avg_ms=150,
                hallucination_rate=0.05,
                reasoning_success_rate=0.7,
                results=[]
            ),
            BenchmarkReport(
                domain=DocumentDomain.LEGAL,
                document_name="test_doc",
                total_questions=10,
                correct_count=7,
                partial_score_avg=0.8,
                section_recall_avg=0.85,
                response_time_avg_ms=180,
                hallucination_rate=0.1,
                reasoning_success_rate=0.6,
                results=[]
            )
        ]
        
        comparison = benchmark.compare_domains("test_doc")
        
        assert comparison["document_name"] == "test_doc"
        assert comparison["domains_evaluated"] == 2
        assert len(comparison["domain_metrics"]) == 2
        
        # Medical should rank first by accuracy (0.8 vs 0.7)
        assert comparison["rankings"]["by_accuracy"][0]["domain"] == "medical"
        
        # Medical should rank first by response time (150 vs 180)
        assert comparison["rankings"]["by_response_time"][0]["domain"] == "medical"
        
        # Medical should rank first by hallucination rate (0.05 vs 0.1)
        assert comparison["rankings"]["by_hallucination_rate"][0]["domain"] == "medical"
    
    def test_compare_domains_no_results(self, benchmark):
        comparison = benchmark.compare_domains("nonexistent")
        assert "error" in comparison
    
    def test_save_report(self, benchmark, tmp_path):
        report = BenchmarkReport(
            domain=DocumentDomain.TECHNICAL,
            document_name="tech_doc",
            total_questions=5,
            correct_count=4,
            partial_score_avg=0.88,
            section_recall_avg=0.9,
            response_time_avg_ms=100,
            hallucination_rate=0.02,
            reasoning_success_rate=0.8,
            results=[]
        )
        
        output_dir = str(tmp_path / "reports")
        filepath = benchmark.save_report(report, output_dir)
        
        assert os.path.exists(filepath)
        assert "tech_doc" in filepath
        assert "technical" in filepath
        
        # Verify content
        with open(filepath, 'r') as f:
            saved = json.load(f)
        assert saved["domain"] == "technical"
        assert saved["accuracy"] == 0.8
    
    def test_format_tree_structure(self, benchmark):
        tree = {
            "title": "Root",
            "summary": "Root summary that is longer than 100 characters to test truncation",
            "children": [
                {
                    "title": "Child 1",
                    "summary": "Child 1 summary",
                    "children": []
                },
                {
                    "title": "Child 2",
                    "summary": "Child 2 summary"
                }
            ]
        }
        
        formatted = benchmark._format_tree_structure(tree, max_depth=2)
        
        assert "Root" in formatted
        assert "Child 1" in formatted
        assert "Child 2" in formatted
    
    def test_format_tree_structure_respects_max_depth(self, benchmark):
        tree = {
            "title": "Level 0",
            "summary": "L0",
            "children": [
                {
                    "title": "Level 1",
                    "summary": "L1",
                    "children": [
                        {
                            "title": "Level 2",
                            "summary": "L2",
                            "children": [
                                {"title": "Level 3", "summary": "L3"}
                            ]
                        }
                    ]
                }
            ]
        }
        
        formatted = benchmark._format_tree_structure(tree, max_depth=2)
        
        assert "Level 0" in formatted
        assert "Level 1" in formatted
        assert "Level 2" not in formatted  # Should be cut off
        assert "Level 3" not in formatted


class TestDomainClassifierKeywords:
    """Test keyword-based domain classification comprehensively."""
    
    def test_medical_korean_keywords(self):
        texts = [
            "환자의 증상을 분석합니다",
            "진단 결과 치료가 필요합니다",
            "약물 투여 후 경과 관찰",
            "수술 전 검사 진행",
            "의공학 연구 보고서"
        ]
        for text in texts:
            domain, _ = DomainClassifier.classify(text)
            assert domain == DocumentDomain.MEDICAL, f"Failed for: {text}"
    
    def test_legal_korean_keywords(self):
        texts = [
            "법률에 따른 규정 준수",
            "계약 조항 검토",
            "소송 절차 진행",
            "민법 상의 권리",
            "특허 출원 관련"
        ]
        for text in texts:
            domain, _ = DomainClassifier.classify(text)
            assert domain == DocumentDomain.LEGAL, f"Failed for: {text}"
    
    def test_technical_korean_keywords(self):
        texts = [
            "시스템 아키텍처 설계",
            "알고리즘 최적화",
            "API 인터페이스 구현",
            "반도체 회로 설계",
            "네트워크 프로토콜"
        ]
        for text in texts:
            domain, _ = DomainClassifier.classify(text)
            assert domain == DocumentDomain.TECHNICAL, f"Failed for: {text}"
    
    def test_financial_keywords(self):
        texts = [
            "재무제표 분석",
            "투자 수익률 계산",
            "주식 채권 포트폴리오",
            "세금 납부 관련",
            "회계 기준 적용"
        ]
        for text in texts:
            domain, _ = DomainClassifier.classify(text)
            assert domain == DocumentDomain.FINANCIAL, f"Failed for: {text}"
    
    def test_regulatory_keywords(self):
        texts = [
            "ISO 인증 요건",
            "FDA 승인 절차",
            "규제 준수 감사",
            "표준 인허가 심사",
            "CE 마크 인증"
        ]
        for text in texts:
            domain, _ = DomainClassifier.classify(text)
            assert domain == DocumentDomain.REGULATORY, f"Failed for: {text}"
