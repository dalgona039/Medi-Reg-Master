import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    genai = None
    HAS_GENAI = False


@dataclass
class RelevanceWeights:
    semantic_weight: float = 0.7
    structural_weight: float = 0.2
    contextual_weight: float = 0.1
    
    def __post_init__(self):
        total = self.semantic_weight + self.structural_weight + self.contextual_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Weights must sum to 1.0, got {total}. "
                f"(λ₁={self.semantic_weight}, λ₂={self.structural_weight}, λ₃={self.contextual_weight})"
            )
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'semantic_weight': self.semantic_weight,
            'structural_weight': self.structural_weight,
            'contextual_weight': self.contextual_weight
        }


class HierarchicalRetrievalModel:
    def __init__(
        self,
        weights: Optional[RelevanceWeights] = None,
        max_depth: int = 5,
        depth_decay: float = 0.9
    ):
        self.weights = weights or RelevanceWeights()
        self.max_depth = max_depth
        self.depth_decay = depth_decay
        
        self.embedding_model = 'models/text-embedding-004'
    
    def relevance_score(
        self,
        node: Dict[str, Any],
        query: str,
        current_depth: int,
        parent_node: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[np.ndarray] = None
    ) -> Tuple[float, Dict[str, float]]:
        semantic_score = self._semantic_relevance(node, query, query_embedding)
        structural_score = self._structural_relevance(current_depth)
        contextual_score = self._contextual_relevance(node, parent_node)
        
        total_score = (
            self.weights.semantic_weight * semantic_score +
            self.weights.structural_weight * structural_score +
            self.weights.contextual_weight * contextual_score
        )
        total_score = np.clip(total_score, 0.0, 1.0)
        
        component_scores = {
            'semantic': float(semantic_score),
            'structural': float(structural_score),
            'contextual': float(contextual_score),
            'total': float(total_score)
        }
        
        return float(total_score), component_scores
    
    def _semantic_relevance(
        self,
        node: Dict[str, Any],
        query: str,
        query_embedding: Optional[np.ndarray] = None
    ) -> float:
        node_title = node.get('title', '')
        node_summary = node.get('summary', '')
        node_text = f"{node_title}. {node_summary}".strip()
        
        if not node_text:
            return 0.0
        
        query_lower = query.lower()
        node_lower = node_text.lower()
        
        import re
        query_words = set(re.findall(r'\w+', query_lower))
        node_words = set(re.findall(r'\w+', node_lower))
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(node_words))
        similarity = overlap / len(query_words)
        
        title_lower = node_title.lower()
        for query_word in query_words:
            if query_word in title_lower:
                similarity = min(similarity + 0.2, 1.0)
                break
        
        return min(similarity, 1.0)
    
    def _semantic_relevance_with_embedding(
        self,
        node_text: str,
        query: str,
        query_embedding: Optional[np.ndarray] = None
    ) -> float:
        try:
            if query_embedding is None:
                query_result = genai.embed_content(
                    model=self.embedding_model,
                    content=query,
                    task_type="retrieval_query"
                )
                query_embedding = np.array(query_result['embedding'])
            
            node_result = genai.embed_content(
                model=self.embedding_model,
                content=node_text,
                task_type="retrieval_document"
            )
            node_embedding = np.array(node_result['embedding'])
            
            similarity = np.dot(query_embedding, node_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(node_embedding)
            )
            
            normalized_similarity = (similarity + 1) / 2
            
            return float(np.clip(normalized_similarity, 0.0, 1.0))
            
        except Exception as e:
            print(f" Embedding error: {e}, fallback to keyword matching")
            return self._semantic_relevance(
                {'title': '', 'summary': node_text},
                query,
                None
            )
    
    def _structural_relevance(self, current_depth: int) -> float:
        if current_depth >= self.max_depth:
            return 0.0
        
        # Exponential decay
        score = self.depth_decay ** current_depth
        
        return float(np.clip(score, 0.0, 1.0))
    
    def _contextual_relevance(
        self,
        node: Dict[str, Any],
        parent_node: Optional[Dict[str, Any]]
    ) -> float:
        if parent_node is None:
            return 1.0
        
        node_title = node.get('title', '')
        parent_title = parent_node.get('title', '')
        
        if not node_title or not parent_title:
            return 0.5
        

        node_words = set(node_title.lower().split())
        parent_words = set(parent_title.lower().split())
        
        if not parent_words:
            return 0.5
        
        overlap = len(node_words.intersection(parent_words))
        coherence = overlap / len(parent_words)
        
        coherence = max(coherence, 0.3)
        
        return min(coherence, 1.0)
    
    def rank_nodes(
        self,
        nodes: List[Dict[str, Any]],
        query: str,
        parent_node: Optional[Dict[str, Any]] = None,
        current_depth: int = 0
    ) -> List[Tuple[Dict[str, Any], float, Dict[str, float]]]:
        scored_nodes = []
        
        for node in nodes:
            score, components = self.relevance_score(
                node=node,
                query=query,
                current_depth=current_depth,
                parent_node=parent_node
            )
            scored_nodes.append((node, score, components))
        
        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        
        return scored_nodes
    
    def get_complexity_analysis(self) -> Dict[str, str]:
        return {
            'time_complexity': 'O(N) where N = number of visited nodes',
            'space_complexity': 'O(D) where D = max tree depth (DFS stack)',
            'optimality': 'Greedy best-first search (not optimal, but efficient)',
            'trade_off': 'Efficiency (90% context reduction) vs Completeness (may miss some relevant nodes)',
            'limitations': 'Early filtering error: if parent is incorrectly judged irrelevant, all descendants are pruned'
        }
    
    def explain_decision(
        self,
        node: Dict[str, Any],
        query: str,
        current_depth: int,
        parent_node: Optional[Dict[str, Any]] = None
    ) -> str:
        score, components = self.relevance_score(node, query, current_depth, parent_node)
        
        explanation = [
            f"\n{'='*60}",
            f"Node: {node.get('title', 'Untitled')}",
            f"Total Relevance Score: {score:.4f}",
            f"{'='*60}",
            "",
            "Component Breakdown:",
            f"  🔍 Semantic Relevance  (λ₁={self.weights.semantic_weight}): {components['semantic']:.4f}",
            f"     → Query-node similarity based on content",
            "",
            f"  🏗️  Structural Relevance (λ₂={self.weights.structural_weight}): {components['structural']:.4f}",
            f"     → Depth penalty (current depth: {current_depth}/{self.max_depth})",
            "",
            f"  🔗 Contextual Relevance (λ₃={self.weights.contextual_weight}): {components['contextual']:.4f}",
            f"     → Parent-child coherence",
            "",
            f"Final Score = {self.weights.semantic_weight}×{components['semantic']:.4f} + "
            f"{self.weights.structural_weight}×{components['structural']:.4f} + "
            f"{self.weights.contextual_weight}×{components['contextual']:.4f} = {score:.4f}",
            f"{'='*60}\n"
        ]
        
        return "\n".join(explanation)


# Default model instance
default_model = HierarchicalRetrievalModel()
