import pytest
from src.core.error_recovery import ErrorRecoveryFilter, FilteringDecision


class TestDualStageFilter:
    
    def test_root_node_always_relevant(self):
        filter_obj = ErrorRecoveryFilter()
        
        root_node = {"id": "root", "title": "Root", "summary": "Root node"}
        
        decision = filter_obj.dual_stage_filter(
            root_node, "test query", "", depth=0
        )
        
        assert decision.is_relevant is True
        assert decision.confidence == 1.0
    
    def test_sparse_content_rejected(self):
        filter_obj = ErrorRecoveryFilter()
        
        sparse_node = {"id": "sparse", "title": "X", "summary": ""}
        
        decision = filter_obj.dual_stage_filter(
            sparse_node, "test query", "", depth=1
        )
        
        assert decision.is_relevant is False
        assert decision.confidence > 0.9
    
    def test_keyword_matching(self):
        filter_obj = ErrorRecoveryFilter()
        
        relevant_node = {
            "id": "n1",
            "title": "Machine Learning Basics",
            "summary": "Introduction to machine learning concepts and algorithms"
        }
        
        decision = filter_obj.dual_stage_filter(
            relevant_node,
            "What is machine learning?",
            "",
            depth=1
        )
        
        assert decision.keyword_score > 0.5
        assert decision.is_relevant is True
    
    def test_keyword_not_matching(self):
        filter_obj = ErrorRecoveryFilter()
        
        irrelevant_node = {
            "id": "n2",
            "title": "Cooking Recipes",
            "summary": "Collection of delicious dessert recipes"
        }
        
        decision = filter_obj.dual_stage_filter(
            irrelevant_node,
            "What is machine learning?",
            "",
            depth=1
        )
        
        assert decision.keyword_score < 0.5
        assert decision.is_relevant is False


class TestLLMEvaluation:
    
    def test_llm_mock_evaluation(self):
        filter_obj = ErrorRecoveryFilter()
        
        def mock_llm(node, query, context):
            return {
                "relevant": True,
                "confidence": 0.85,
                "reason": "Test"
            }
        
        node = {
            "id": "n3",
            "title": "Test Section",
            "summary": "This is a test section with enough content to evaluate"
        }
        
        decision = filter_obj.dual_stage_filter(
            node,
            "test",
            "",
            depth=1,
            llm_check_fn=mock_llm
        )
        
        assert decision.llm_score == 0.9
        assert decision.confidence > 0


class TestOverFilteringDetection:
    
    def test_no_nodes_selected_triggers_recovery(self):
        filter_obj = ErrorRecoveryFilter()
        
        filtered_nodes = [
            {"id": "n1", "title": "machine learning algorithm", "summary": "Details about machine learning"},
            {"id": "n2", "title": "training methods", "summary": "How to train models"},
        ]
        
        over_filtered, recovered = filter_obj.detect_over_filtering(
            selected_nodes=[],
            filtered_nodes=filtered_nodes,
            query="machine learning"
        )
        
        assert over_filtered is True
        assert len(recovered) > 0
    
    def test_many_nodes_filtered_triggers_recovery(self):
        filter_obj = ErrorRecoveryFilter()
        
        selected_nodes = [{"id": "n0", "title": "One", "summary": "Selected"}]
        filtered_nodes = [
            {"id": "n1", "title": "machine learning methods", "summary": "Details"},
            {"id": "n2", "title": "deep learning algorithms", "summary": "More details"},
            {"id": "n3", "title": "training approaches", "summary": "Training"},
            {"id": "n4", "title": "testing procedures", "summary": "Testing"},
        ]
        
        over_filtered, recovered = filter_obj.detect_over_filtering(
            selected_nodes=selected_nodes,
            filtered_nodes=filtered_nodes,
            query="machine learning training"
        )
        
        assert over_filtered is True
        assert len(recovered) > 0
    
    def test_normal_filtering_no_recovery(self):
        filter_obj = ErrorRecoveryFilter()
        
        selected_nodes = [
            {"id": "n0", "title": "A", "summary": "Selected 1"},
            {"id": "n1", "title": "B", "summary": "Selected 2"},
        ]
        filtered_nodes = [
            {"id": "n2", "title": "C", "summary": "Filtered"},
        ]
        
        over_filtered, recovered = filter_obj.detect_over_filtering(
            selected_nodes=selected_nodes,
            filtered_nodes=filtered_nodes,
            query="test"
        )
        
        assert over_filtered is False
        assert len(recovered) == 0


class TestCriticalNodeRecovery:
    
    def test_recover_nodes_with_critical_keywords(self):
        filter_obj = ErrorRecoveryFilter()
        
        filtered_nodes = [
            {
                "id": "n1",
                "title": "Deep Neural Networks Implementation",
                "summary": "Detailed guide to implementing deep neural networks"
            },
            {
                "id": "n2",
                "title": "Activation Functions",
                "summary": "Linear and non-linear activation"
            }
        ]
        
        recovered = filter_obj._recover_critical_nodes(
            filtered_nodes,
            "deep neural networks"
        )
        
        assert len(recovered) > 0
        assert any("deep" in n["title"].lower() for n in recovered)
    
    def test_no_recovery_without_critical_keywords(self):
        filter_obj = ErrorRecoveryFilter()
        
        filtered_nodes = [
            {"id": "n1", "title": "Cooking", "summary": "Food"},
            {"id": "n2", "title": "Sports", "summary": "Games"},
        ]
        
        recovered = filter_obj._recover_critical_nodes(
            filtered_nodes,
            "machine learning"
        )
        
        assert len(recovered) == 0


class TestAdaptiveThreshold:
    
    def test_threshold_relaxed_when_over_filtering(self):
        filter_obj = ErrorRecoveryFilter()
        
        adjusted = filter_obj.adaptive_threshold_adjustment(
            num_selected=1,
            num_total=100,
            query_length=20
        )
        
        assert adjusted < filter_obj.confidence_threshold
    
    def test_threshold_tightened_when_under_filtering(self):
        filter_obj = ErrorRecoveryFilter()
        
        adjusted = filter_obj.adaptive_threshold_adjustment(
            num_selected=90,
            num_total=100,
            query_length=20
        )
        
        assert adjusted > filter_obj.confidence_threshold
    
    def test_threshold_adjusted_for_short_queries(self):
        filter_obj = ErrorRecoveryFilter()
        
        adjusted_short = filter_obj.adaptive_threshold_adjustment(
            num_selected=50,
            num_total=100,
            query_length=5
        )
        
        adjusted_long = filter_obj.adaptive_threshold_adjustment(
            num_selected=50,
            num_total=100,
            query_length=150
        )
        
        assert adjusted_short > adjusted_long


class TestFilteringHistory:
    
    def test_filtering_history_recorded(self):
        filter_obj = ErrorRecoveryFilter()
        
        node1 = {"id": "n1", "title": "Test 1", "summary": "Content 1"}
        node2 = {"id": "n2", "title": "Test 2", "summary": "Content 2"}
        
        filter_obj.dual_stage_filter(node1, "test", "", depth=1)
        filter_obj.dual_stage_filter(node2, "test", "", depth=1)
        
        assert len(filter_obj.filtering_history) == 2
        assert filter_obj.filtering_history[0]['node_id'] == 'n1'
        assert filter_obj.filtering_history[1]['node_id'] == 'n2'
    
    def test_explain_filtering_decisions(self):
        filter_obj = ErrorRecoveryFilter()
        
        node = {"id": "n1", "title": "Test", "summary": "Test content"}
        filter_obj.dual_stage_filter(node, "test", "", depth=1)
        
        report = filter_obj.explain_filtering_decisions()
        
        assert "Filtering Decision Report" in report
        assert "Confident Rejections" in report or "Uncertain Rejections" in report
        assert "False Negatives" in report


class TestFilteringDecisionDataclass:
    
    def test_filtering_decision_creation(self):
        decision = FilteringDecision(
            is_relevant=True,
            confidence=0.85,
            reason="Test reason",
            llm_score=0.9,
            keyword_score=0.8,
            combined_score=0.87
        )
        
        assert decision.is_relevant is True
        assert decision.confidence == 0.85
        assert decision.combined_score == 0.87


class TestIntegrationErrorRecovery:
    
    def test_end_to_end_recovery_workflow(self):
        filter_obj = ErrorRecoveryFilter()
        
        nodes_to_evaluate = [
            {
                "id": "n1",
                "title": "Introduction to Machine Learning",
                "summary": "Basic concepts and history of machine learning algorithms"
            },
            {
                "id": "n2",
                "title": "Unrelated Topic",
                "summary": "This is about something completely different"
            },
            {
                "id": "n3",
                "title": "Deep Learning Techniques",
                "summary": "Advanced neural network architectures for machine learning"
            }
        ]
        
        selected = []
        filtered = []
        
        for node in nodes_to_evaluate:
            decision = filter_obj.dual_stage_filter(
                node,
                "machine learning algorithms",
                "",
                depth=1
            )
            
            if decision.is_relevant:
                selected.append(node)
            else:
                filtered.append(node)
        
        over_filtered, recovered = filter_obj.detect_over_filtering(
            selected,
            filtered,
            "machine learning algorithms"
        )
        
        if over_filtered:
            selected.extend(recovered)
        
        assert len(selected) > 0
        assert any("machine" in n["title"].lower() for n in selected)
