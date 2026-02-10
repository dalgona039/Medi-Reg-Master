import json
import os
import math
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict
import re
from src.config import Config
from src.utils.cache import get_cache


class BM25Ranker:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = defaultdict(lambda: defaultdict(int))
        self.doc_lengths = {}
        self.avg_doc_length = 0
        self.num_docs = 0
        self.idf_cache = {}
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        self.num_docs = len(documents)
        total_length = 0
        
        for doc_id, doc in enumerate(documents):
            tokens = self._tokenize(doc.get('text', '') + ' ' + doc.get('title', ''))
            self.doc_lengths[doc_id] = len(tokens)
            total_length += len(tokens)
            
            for token in set(tokens):
                self.doc_freqs[token][doc_id] += 1
        
        self.avg_doc_length = total_length / self.num_docs if self.num_docs > 0 else 0
    
    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'\w+', text)
        return [t for t in tokens if len(t) > 1]
    
    def _idf(self, token: str) -> float:
        if token in self.idf_cache:
            return self.idf_cache[token]
        
        doc_count = len(self.doc_freqs[token])
        idf = math.log((self.num_docs - doc_count + 0.5) / (doc_count + 0.5) + 1.0)
        self.idf_cache[token] = idf
        return idf
    
    def score(self, doc_id: int, query_tokens: List[str]) -> float:
        score = 0.0
        doc_len = self.doc_lengths.get(doc_id, 0)
        
        for token in set(query_tokens):
            freq = self.doc_freqs[token].get(doc_id, 0)
            idf = self._idf(token)
            
            numerator = idf * freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length))
            
            score += numerator / denominator
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        query_tokens = self._tokenize(query)
        scores = {}
        
        for token in query_tokens:
            for doc_id, freq in self.doc_freqs[token].items():
                if doc_id not in scores:
                    scores[doc_id] = 0
                scores[doc_id] += self._idf(token)
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        detailed_scores = []
        for doc_id, _ in ranked:
            bm25_score = self.score(doc_id, query_tokens)
            detailed_scores.append((doc_id, bm25_score))
        
        return sorted(detailed_scores, key=lambda x: x[1], reverse=True)


class SemanticRanker:
    def __init__(self):
        pass
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def score(self, query: str, document_text: str) -> float:
        similarity = self._simple_similarity(query, document_text)
        return min(similarity, 1.0)


class StructuralRanker:
    def score(self, node: Dict[str, Any], depth: int, max_depth: int = 5) -> float:
        """
        Structural signal: nodes closer to root get higher score
        depth 0 (root) -> 1.0
        depth increases -> score decreases exponentially
        """
        if max_depth <= 0:
            return 1.0
        
        decay = 0.85
        score = decay ** depth
        
        return max(score, 0.1)


class FlatRAGBaseline:
    
    def __init__(self, index_filenames: List[str]):
        self.index_filenames = index_filenames
        self.documents: List[Dict[str, Any]] = []
        self.bm25 = BM25Ranker()
        self.semantic_ranker = SemanticRanker()
        self.structural_ranker = StructuralRanker()
        
        self._load_and_flatten_documents()
        self.bm25.index_documents(self.documents)
    
    def _load_and_flatten_documents(self) -> None:
        for index_filename in self.index_filenames:
            path = os.path.join(Config.INDEX_DIR, index_filename)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Index file not found: {path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                tree = json.load(f)
            
            self._flatten_tree(tree, index_filename, depth=0)
    
    def _flatten_tree(self, node: Dict[str, Any], source: str, depth: int = 0) -> None:
        if not node or not isinstance(node, dict):
            return
        
        flat_node = {
            'id': node.get('id', f'unknown_{len(self.documents)}'),
            'title': node.get('title', 'Untitled'),
            'text': node.get('summary', '') or node.get('text', ''),
            'page_ref': node.get('page_ref', ''),
            'source': source,
            'depth': depth,
            'original_node': node
        }
        
        self.documents.append(flat_node)
        
        children = node.get('children', [])
        if isinstance(children, list):
            for child in children:
                self._flatten_tree(child, source, depth + 1)
    
    def query(
        self, 
        user_question: str, 
        max_depth: int = 5,
        max_branches: int = 3,
        domain_template: str = "general",
        language: str = "ko",
        enable_comparison: bool = True,
        node_context: Optional[dict] = None
    ) -> Tuple[str, Dict]:
        
        cache = get_cache()
        
        cache_key_params = {
            'question': user_question,
            'index_files': self.index_filenames,
            'use_deep_traversal': False,
            'max_depth': max_depth,
            'max_branches': max_branches,
            'domain_template': domain_template,
            'language': language,
            'node_context': node_context
        }
        
        cached_response = cache.get(**cache_key_params)
        if cached_response:
            print(f"✅ Cache HIT - FlatRAG")
            return cached_response["answer"], cached_response["metadata"]
        
        print(f"❌ Cache MISS - FlatRAG generating response")
        
        retrieved_node_ids = self._retrieve_documents(
            user_question, 
            max_results=max_branches
        )
        
        retrieved_nodes = [
            self.documents[doc_id] for doc_id in retrieved_node_ids
        ]
        
        context = self._build_context(retrieved_nodes)
        
        answer = self._generate_answer(user_question, context)
        
        metadata = {
            'retrieved_docs': [node['id'] for node in retrieved_nodes],
            'context_size': len(context),
            'num_documents': len(retrieved_nodes),
            'sources': [node['source'] for node in retrieved_nodes],
            'model': 'FlatRAG-Baseline'
        }
        
        cache.set(
            question=user_question,
            index_files=self.index_filenames,
            use_deep_traversal=False,
            max_depth=max_depth,
            max_branches=max_branches,
            domain_template=domain_template,
            language=language,
            response={'answer': answer, 'metadata': metadata},
            node_context=node_context
        )
        
        return answer, metadata
    
    def _retrieve_documents(self, query: str, max_results: int = 3) -> List[int]:
        bm25_results = self.bm25.search(query, top_k=20)
        
        scored_docs = []
        
        max_bm25 = max((score for _, score in bm25_results), default=1.0)
        
        for doc_id, bm25_score in bm25_results:
            doc = self.documents[doc_id]
            
            semantic_score = self.semantic_ranker.score(
                query, 
                doc['text']
            )
            
            structural_score = self.structural_ranker.score(
                doc, 
                doc['depth']
            )
            
            normalized_bm25 = (bm25_score / max_bm25) if max_bm25 > 0 else 0
            
            combined_score = (
                0.6 * normalized_bm25 +
                0.25 * semantic_score +
                0.15 * structural_score
            )
            
            scored_docs.append((doc_id, combined_score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc_id for doc_id, _ in scored_docs[:max_results]]
    
    def _build_context(self, retrieved_nodes: List[Dict[str, Any]]) -> str:
        if not retrieved_nodes:
            return "No relevant documents found."
        
        context_parts = []
        for i, node in enumerate(retrieved_nodes, 1):
            header = f"[Document {i}: {node['title']}"
            if node['page_ref']:
                header += f" (p.{node['page_ref']})"
            header += "]"
            
            context_parts.append(header)
            context_parts.append(node['text'])
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, query: str, context: str) -> str:
        if not context or context == "No relevant documents found.":
            return f"I could not find relevant information to answer: {query}"
        
        answer = f"Based on the retrieved documents:\n\n{context}\n\nAnswer: "
        
        if '?' in query:
            answer += f"The documents discuss aspects related to: {query[:-1] if query.endswith('?') else query}"
        else:
            answer += f"The retrieved documents contain information about: {query}"
        
        return answer
    
    def get_relevant_docs_for_metric(self, query: str, top_k: int = 5) -> List[str]:
        doc_ids = self._retrieve_documents(query, max_results=top_k)
        return [self.documents[doc_id]['id'] for doc_id in doc_ids]
