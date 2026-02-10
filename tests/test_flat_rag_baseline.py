import pytest
import json
import os
from pathlib import Path
from src.core.flat_rag_baseline import FlatRAGBaseline, BM25Ranker, SemanticRanker, StructuralRanker
from src.config import Config


class TestBM25Ranker:
    
    def test_tokenization(self):
        ranker = BM25Ranker()
        tokens = ranker._tokenize("Hello World! This is a TEST.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "test" in tokens
        assert len(tokens) >= 4
    
    def test_idf_calculation(self):
        ranker = BM25Ranker()
        documents = [
            {'text': 'cat dog animal', 'title': ''},
            {'text': 'dog bird', 'title': ''},
            {'text': 'cat fish', 'title': ''}
        ]
        ranker.index_documents(documents)
        
        idf_common = ranker._idf('dog')
        idf_rare = ranker._idf('bird')
        
        assert idf_common > 0
        assert idf_rare >= idf_common
    
    def test_bm25_scoring(self):
        ranker = BM25Ranker()
        documents = [
            {'text': 'machine learning deep learning neural networks', 'title': 'AI'},
            {'text': 'cooking recipes ingredients', 'title': 'Food'},
            {'text': 'machine learning algorithms', 'title': 'ML'}
        ]
        ranker.index_documents(documents)
        
        query = 'machine learning'
        results = ranker.search(query, top_k=3)
        
        assert len(results) <= 3
        assert results[0][1] > 0
        assert all(score >= 0 for _, score in results)


class TestSemanticRanker:
    
    def test_jaccard_similarity(self):
        ranker = SemanticRanker()
        
        score_high = ranker.score("machine learning", "machine learning algorithm")
        score_low = ranker.score("machine learning", "cooking recipe")
        
        assert score_high > score_low
        assert 0 <= score_high <= 1
        assert 0 <= score_low <= 1


class TestStructuralRanker:
    
    def test_depth_penalty(self):
        ranker = StructuralRanker()
        
        score_root = ranker.score({}, depth=0)
        score_deep = ranker.score({}, depth=3)
        
        assert score_root > score_deep
        assert 0 < score_deep < 1


class TestFlatRAGBaseline:
    
    @pytest.fixture
    def sample_index_file(self, tmp_path):
        sample_tree = {
            "id": "root",
            "title": "Machine Learning Basics",
            "summary": "Introduction to machine learning concepts",
            "text": "Machine learning is a subset of artificial intelligence",
            "page_ref": "1",
            "children": [
                {
                    "id": "node1",
                    "title": "Supervised Learning",
                    "summary": "Supervised learning algorithms",
                    "text": "Supervised learning uses labeled data to train models",
                    "page_ref": "3-5",
                    "children": []
                },
                {
                    "id": "node2",
                    "title": "Unsupervised Learning",
                    "summary": "Unsupervised learning algorithms",
                    "text": "Unsupervised learning finds patterns in unlabeled data",
                    "page_ref": "6-8",
                    "children": [
                        {
                            "id": "node2_1",
                            "title": "Clustering",
                            "summary": "Clustering techniques",
                            "text": "Clustering groups similar data points together",
                            "page_ref": "7"
                        }
                    ]
                }
            ]
        }
        
        index_file = tmp_path / "test_index.json"
        index_file.write_text(json.dumps(sample_tree), encoding='utf-8')
        
        return str(index_file)
    
    def test_flat_rag_initialization(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        assert len(flat_rag.documents) >= 4
        assert flat_rag.documents[0]['title'] == 'Machine Learning Basics'
    
    def test_document_flattening(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        titles = [doc['title'] for doc in flat_rag.documents]
        assert 'Machine Learning Basics' in titles
        assert 'Supervised Learning' in titles
        assert 'Unsupervised Learning' in titles
        assert 'Clustering' in titles
    
    def test_depth_tracking(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        root_docs = [d for d in flat_rag.documents if d['depth'] == 0]
        child_docs = [d for d in flat_rag.documents if d['depth'] == 1]
        grandchild_docs = [d for d in flat_rag.documents if d['depth'] == 2]
        
        assert len(root_docs) == 1
        assert len(child_docs) >= 2
        assert len(grandchild_docs) >= 1
    
    def test_query_interface(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        answer, metadata = flat_rag.query(
            "What is supervised learning?",
            max_branches=3
        )
        
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(metadata, dict)
        assert 'retrieved_docs' in metadata
        assert 'context_size' in metadata
        assert 'model' in metadata
        assert metadata['model'] == 'FlatRAG-Baseline'
    
    def test_retrieval_relevance(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        supervised_query = "supervised learning with labels"
        retrieved = flat_rag._retrieve_documents(supervised_query, max_results=3)
        
        assert len(retrieved) > 0
        assert len(retrieved) <= 3
        assert all(isinstance(doc_id, int) for doc_id in retrieved)
    
    def test_retrieval_returns_top_documents(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        query = "machine learning clustering"
        retrieved = flat_rag._retrieve_documents(query, max_results=2)
        
        assert len(retrieved) <= 2
        retrieved_docs = [flat_rag.documents[doc_id] for doc_id in retrieved]
        retrieved_titles = [doc['title'] for doc in retrieved_docs]
        
        assert any('learning' in title.lower() for title in retrieved_titles)
    
    def test_context_building(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        nodes = [flat_rag.documents[0], flat_rag.documents[1]]
        context = flat_rag._build_context(nodes)
        
        assert len(context) > 0
        assert '[Document' in context
        assert any(node['title'] in context for node in nodes)
    
    def test_metadata_structure(self, sample_index_file, monkeypatch):
        monkeypatch.setattr(Config, 'INDEX_DIR', str(Path(sample_index_file).parent))
        
        flat_rag = FlatRAGBaseline([Path(sample_index_file).name])
        
        answer, metadata = flat_rag.query("What is machine learning?")
        
        assert isinstance(metadata, dict)
        assert 'retrieved_docs' in metadata
        assert 'context_size' in metadata
        assert 'num_documents' in metadata
        assert 'sources' in metadata
        assert 'model' in metadata
        
        assert isinstance(metadata['retrieved_docs'], list)
        assert isinstance(metadata['context_size'], int)
        assert isinstance(metadata['num_documents'], int)
        assert isinstance(metadata['sources'], list)


class TestFlatRAGIntegration:
    
    def test_multi_document_retrieval(self, tmp_path, monkeypatch):
        index1 = {
            "id": "doc1_root",
            "title": "AI Basics",
            "summary": "Introduction to AI",
            "text": "Artificial intelligence is transforming technology",
            "children": []
        }
        
        index2 = {
            "id": "doc2_root",
            "title": "Deep Learning",
            "summary": "Neural networks and deep learning",
            "text": "Deep learning uses multiple layers of neural networks",
            "children": []
        }
        
        file1 = tmp_path / "ai.json"
        file2 = tmp_path / "dl.json"
        file1.write_text(json.dumps(index1))
        file2.write_text(json.dumps(index2))
        
        monkeypatch.setattr(Config, 'INDEX_DIR', str(tmp_path))
        
        flat_rag = FlatRAGBaseline(['ai.json', 'dl.json'])
        
        assert len(flat_rag.documents) >= 2
    
    def test_bm25_with_multilingual_content(self, tmp_path, monkeypatch):
        sample_tree = {
            "id": "root",
            "title": "Machine Learning Basics",
            "summary": "Introduction to machine learning concepts",
            "text": "Machine learning is a subset of artificial intelligence",
            "page_ref": "1",
            "children": []
        }
        
        index_file = tmp_path / "test_index.json"
        index_file.write_text(json.dumps(sample_tree), encoding='utf-8')
        
        monkeypatch.setattr(Config, 'INDEX_DIR', str(tmp_path))
        
        flat_rag = FlatRAGBaseline([index_file.name])
        
        english_query = "machine learning"
        results = flat_rag._retrieve_documents(english_query)
        
        assert len(results) > 0
