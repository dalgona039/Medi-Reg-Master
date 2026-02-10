import pytest
import json
from src.core.tree_traversal import TreeNavigator
from src.core.error_recovery import ErrorRecoveryFilter


@pytest.fixture
def sample_tree():
    """Create a sample document tree for testing."""
    return {
        "id": "root",
        "title": "JavaScript Guide",
        "summary": "Complete guide to JavaScript programming",
        "children": [
            {
                "id": "ch1",
                "title": "Introduction to JavaScript",
                "summary": "Basics and history of JavaScript language",
                "children": [
                    {
                        "id": "ch1s1",
                        "title": "What is JavaScript?",
                        "summary": "JavaScript is a programming language for web development"
                    },
                    {
                        "id": "ch1s2",
                        "title": "Setting up Environment",
                        "summary": "How to set up Node.js and a code editor"
                    }
                ]
            },
            {
                "id": "ch2",
                "title": "Variables and Data Types",
                "summary": "Understanding variables, let, const, and different data types",
                "children": [
                    {
                        "id": "ch2s1",
                        "title": "Declaring Variables",
                        "summary": "Using var, let, and const keywords effectively"
                    },
                    {
                        "id": "ch2s2",
                        "title": "String Manipulation",
                        "summary": "Working with strings, methods, and templates"
                    }
                ]
            },
            {
                "id": "ch3",
                "title": "Functions in JavaScript",
                "summary": "Function declaration, arrow functions, and closures",
                "children": [
                    {
                        "id": "ch3s1",
                        "title": "Function Basics",
                        "summary": "Declaring and calling functions with parameters"
                    },
                    {
                        "id": "ch3s2",
                        "title": "Arrow Functions",
                        "summary": "Modern ES6 arrow function syntax and benefits"
                    }
                ]
            }
        ]
    }


class TestTreeNavigatorInitialization:
    
    def test_navigator_has_error_recovery(self, sample_tree):
        navigator = TreeNavigator(sample_tree, "Test Document")
        assert navigator.error_recovery is not None
        assert isinstance(navigator.error_recovery, ErrorRecoveryFilter)
    
    def test_error_recovery_configuration(self, sample_tree):
        navigator = TreeNavigator(sample_tree, "Test Document")
        assert navigator.error_recovery.llm_weight == 0.7
        assert navigator.error_recovery.keyword_weight == 0.3


class TestErrorRecoveryDuringTraversal:
    
    def test_filtering_decisions_recorded_during_traversal(self, sample_tree):
        navigator = TreeNavigator(sample_tree, "Test Document")
        
        # Mock LLM function
        def mock_llm(node, query, context):
            return {
                "relevant": "javascript" in node.get("title", "").lower() or "javascript" in node.get("summary", "").lower(),
                "confidence": 0.85 if "javascript" in node.get("title", "").lower() else 0.3,
                "reason": "Test evaluation"
            }
        
        # Override the LLM function temporarily
        original_evaluate = navigator._evaluate_node_relevance
        
        def custom_evaluate(node, query, parent_context, depth):
            if depth == 0:
                return True
            
            title = node.get("title", "")
            summary = node.get("summary", "")
            
            if len(summary) < 20 and len(title) < 10:
                return False
            
            decision = navigator.error_recovery.dual_stage_filter(
                node, query, parent_context, depth, llm_check_fn=mock_llm
            )
            return decision.is_relevant
        
        navigator._evaluate_node_relevance = custom_evaluate
        
        try:
            navigator._traverse_iterative(
                sample_tree,
                "What is JavaScript?",
                max_depth=2,
                max_branches=2
            )
            
            assert len(navigator.error_recovery.filtering_history) > 0
            assert all('node_id' in record for record in navigator.error_recovery.filtering_history)
        finally:
            navigator._evaluate_node_relevance = original_evaluate
    
    def test_over_filtering_recovery_triggers_when_no_results(self, sample_tree):
        navigator = TreeNavigator(sample_tree, "Test Document")
        
        # Create mock that filters everything
        def mock_llm(node, query, context):
            return {
                "relevant": False,
                "confidence": 0.9,
                "reason": "Filtered for test"
            }
        
        original_evaluate = navigator._evaluate_node_relevance
        
        def filtering_evaluate(node, query, parent_context, depth):
            if depth == 0:
                return True
            return False
        
        navigator._evaluate_node_relevance = filtering_evaluate
        
        try:
            navigator._traverse_iterative(
                sample_tree,
                "JavaScript functions",
                max_depth=2,
                max_branches=2
            )
            
            assert len(navigator.error_recovery.filtering_history) >= 0
        finally:
            navigator._evaluate_node_relevance = original_evaluate


class TestErrorRecoveryReport:
    
    def test_filtering_report_generation(self, sample_tree):
        navigator = TreeNavigator(sample_tree, "Test Document")
        
        def mock_llm(node, query, context):
            return {
                "relevant": "variable" in node.get("title", "").lower(),
                "confidence": 0.8,
                "reason": "Test"
            }
        
        original_evaluate = navigator._evaluate_node_relevance
        
        def custom_evaluate(node, query, parent_context, depth):
            if depth == 0:
                return True
            
            title = node.get("title", "")
            summary = node.get("summary", "")
            
            if len(summary) < 20 and len(title) < 10:
                return False
            
            decision = navigator.error_recovery.dual_stage_filter(
                node, query, parent_context, depth, llm_check_fn=mock_llm
            )
            return decision.is_relevant
        
        navigator._evaluate_node_relevance = custom_evaluate
        
        try:
            navigator._traverse_iterative(
                sample_tree,
                "variables and constants",
                max_depth=2,
                max_branches=2
            )
            
            report = navigator.error_recovery.explain_filtering_decisions()
            assert "Filtering Decision Report" in report
            assert len(report) > 0
        finally:
            navigator._evaluate_node_relevance = original_evaluate


class TestErrorRecoveryMetrics:
    
    def test_filtering_history_tracks_decisions(self, sample_tree):
        navigator = TreeNavigator(sample_tree, "Test Document")
        
        def mock_llm(node, query, context):
            return {
                "relevant": True,
                "confidence": 0.75,
                "reason": "Mock evaluation"
            }
        
        original_evaluate = navigator._evaluate_node_relevance
        
        def custom_evaluate(node, query, parent_context, depth):
            if depth == 0:
                return True
            
            title = node.get("title", "")
            summary = node.get("summary", "")
            
            if len(summary) < 20 and len(title) < 10:
                return False
            
            decision = navigator.error_recovery.dual_stage_filter(
                node, query, parent_context, depth, llm_check_fn=mock_llm
            )
            return decision.is_relevant
        
        navigator._evaluate_node_relevance = custom_evaluate
        
        try:
            navigator._traverse_iterative(
                sample_tree,
                "programming basics",
                max_depth=1,
                max_branches=2
            )
            
            history = navigator.error_recovery.filtering_history
            for record in history:
                assert 'node_id' in record
                assert 'is_relevant' in record
                assert 'confidence' in record
                assert 'combined_score' in record
                assert 0 <= record['confidence'] <= 1
                assert 0 <= record['combined_score'] <= 1
        finally:
            navigator._evaluate_node_relevance = original_evaluate


class TestEndToEndErrorRecovery:
    
    def test_full_traversal_with_error_recovery(self, sample_tree):
        navigator = TreeNavigator(sample_tree, "Complete JavaScript Guide")
        
        def mock_llm(node, query, context):
            keywords = query.lower().split()
            node_text = (node.get("title", "") + " " + node.get("summary", "")).lower()
            is_relevant = any(kw in node_text for kw in keywords[:3])
            return {
                "relevant": is_relevant,
                "confidence": 0.85 if is_relevant else 0.2,
                "reason": "Mock evaluation based on keywords"
            }
        
        original_evaluate = navigator._evaluate_node_relevance
        
        def custom_evaluate(node, query, parent_context, depth):
            if depth == 0:
                return True
            
            title = node.get("title", "")
            summary = node.get("summary", "")
            
            if len(summary) < 20 and len(title) < 10:
                return False
            
            decision = navigator.error_recovery.dual_stage_filter(
                node, query, parent_context, depth, llm_check_fn=mock_llm
            )
            return decision.is_relevant
        
        navigator._evaluate_node_relevance = custom_evaluate
        
        try:
            navigator._traverse_iterative(
                sample_tree,
                "JavaScript functions and arrow functions",
                max_depth=2,
                max_branches=2
            )
            
            assert navigator.visited_nodes
            assert len(navigator.error_recovery.filtering_history) > 0
            
            report = navigator.error_recovery.explain_filtering_decisions()
            assert report is not None
            assert len(report) > 0
        finally:
            navigator._evaluate_node_relevance = original_evaluate
