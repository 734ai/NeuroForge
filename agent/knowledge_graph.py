"""
NeuroForge Knowledge Graph Visualization
Author: Muzan Sano

Advanced knowledge graph creation and visualization for NeuroForge memory system
"""

import json
import asyncio
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import networkx as nx
from collections import defaultdict, Counter
import hashlib
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    id: str
    label: str
    type: str  # 'memory', 'task', 'file', 'concept', 'pattern'
    properties: Dict[str, Any]
    created_at: float
    last_accessed: float
    access_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class GraphEdge:
    """Represents an edge in the knowledge graph"""
    source: str
    target: str
    relationship: str  # 'depends_on', 'similar_to', 'contains', 'triggers', 'references'
    weight: float
    properties: Dict[str, Any]
    created_at: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class KnowledgeGraphBuilder:
    """Builds and maintains the knowledge graph from NeuroForge data"""
    
    def __init__(self, workspace_path: Optional[Path] = None):
        self.workspace_path = workspace_path or Path.cwd()
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.concept_patterns: Dict[str, Set[str]] = defaultdict(set)
        
        # Graph analysis cache
        self._analysis_cache: Dict[str, Any] = {}
        self._cache_timestamp = 0
    
    def add_memory_node(self, memory_id: str, memory_data: Dict[str, Any]) -> str:
        """Add a memory as a node in the knowledge graph"""
        node_id = f"memory_{memory_id}"
        
        # Extract concepts from memory content
        concepts = self._extract_concepts(memory_data)
        
        node = GraphNode(
            id=node_id,
            label=memory_data.get('title', f"Memory {memory_id[:8]}"),
            type='memory',
            properties={
                'content_hash': self._hash_content(memory_data),
                'concepts': list(concepts),
                'workspace': memory_data.get('workspace', ''),
                'tags': memory_data.get('tags', []),
                'content_type': memory_data.get('type', 'unknown'),
                'size': len(str(memory_data))
            },
            created_at=memory_data.get('created_at', time.time()),
            last_accessed=time.time(),
            access_count=1
        )
        
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        
        # Add concept nodes and edges
        for concept in concepts:
            self._add_concept_node(concept)
            self._add_edge(node_id, f"concept_{concept}", "contains")
        
        # Find and create similarity edges
        self._create_similarity_edges(node_id)
        
        logger.debug(f"Added memory node: {node_id}")
        return node_id
    
    def add_task_node(self, task_id: str, task_data: Dict[str, Any]) -> str:
        """Add a task as a node in the knowledge graph"""
        node_id = f"task_{task_id}"
        
        node = GraphNode(
            id=node_id,
            label=task_data.get('description', f"Task {task_id[:8]}"),
            type='task',
            properties={
                'status': task_data.get('status', 'unknown'),
                'plugin': task_data.get('plugin', ''),
                'parameters': task_data.get('parameters', {}),
                'workspace': task_data.get('workspace', ''),
                'execution_time': task_data.get('execution_time', 0),
                'success': task_data.get('status') == 'completed'
            },
            created_at=task_data.get('created_at', time.time()),
            last_accessed=time.time(),
            access_count=1
        )
        
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        
        # Connect task to related memories
        self._connect_task_to_memories(node_id, task_data)
        
        logger.debug(f"Added task node: {node_id}")
        return node_id
    
    def add_file_node(self, file_path: str, file_data: Dict[str, Any]) -> str:
        """Add a file as a node in the knowledge graph"""
        node_id = f"file_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
        
        node = GraphNode(
            id=node_id,
            label=Path(file_path).name,
            type='file',
            properties={
                'path': file_path,
                'extension': Path(file_path).suffix,
                'size': file_data.get('size', 0),
                'language': file_data.get('language', ''),
                'last_modified': file_data.get('last_modified', time.time())
            },
            created_at=file_data.get('created_at', time.time()),
            last_accessed=time.time(),
            access_count=1
        )
        
        self.nodes[node_id] = node
        self.graph.add_node(node_id, **node.to_dict())
        
        logger.debug(f"Added file node: {node_id}")
        return node_id
    
    def _add_concept_node(self, concept: str) -> str:
        """Add a concept node to the graph"""
        node_id = f"concept_{concept}"
        
        if node_id not in self.nodes:
            node = GraphNode(
                id=node_id,
                label=concept,
                type='concept',
                properties={
                    'frequency': 1,
                    'related_memories': set(),
                    'related_tasks': set()
                },
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1
            )
            
            self.nodes[node_id] = node
            self.graph.add_node(node_id, **node.to_dict())
        else:
            # Update frequency
            self.nodes[node_id].properties['frequency'] += 1
            self.nodes[node_id].access_count += 1
            self.nodes[node_id].last_accessed = time.time()
        
        return node_id
    
    def _add_edge(self, source: str, target: str, relationship: str, weight: float = 1.0, properties: Optional[Dict] = None) -> str:
        """Add an edge to the graph"""
        edge_id = f"{source}_{target}_{relationship}"
        
        if edge_id not in self.edges:
            edge = GraphEdge(
                source=source,
                target=target,
                relationship=relationship,
                weight=weight,
                properties=properties or {},
                created_at=time.time()
            )
            
            self.edges[edge_id] = edge
            self.graph.add_edge(source, target, **edge.to_dict())
        else:
            # Strengthen existing edge
            self.edges[edge_id].weight += weight * 0.1
            self.graph[source][target]['weight'] = self.edges[edge_id].weight
        
        return edge_id
    
    def _extract_concepts(self, data: Dict[str, Any]) -> Set[str]:
        """Extract concepts from data using simple keyword extraction"""
        text = ' '.join(str(v) for v in data.values() if isinstance(v, (str, int, float)))
        text = text.lower()
        
        # Simple concept extraction (in practice, this would be more sophisticated)
        import re
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Filter out common words
        stopwords = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'she', 'use', 'top', 'put', 'end', 'why', 'let', 'say', 'too', 'any', 'may', 'own', 'set', 'tell', 'does', 'most', 'over', 'said', 'some', 'time', 'very', 'when', 'much', 'take', 'than', 'only', 'think', 'also', 'come', 'that', 'with', 'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'would', 'there', 'could', 'other', 'after', 'first', 'well', 'year', 'work', 'such', 'make', 'even', 'here', 'where', 'through', 'when', 'down', 'just', 'before', 'never', 'now', 'right', 'each', 'keep', 'place', 'still', 'small', 'every', 'found', 'those', 'never', 'under', 'might', 'while', 'house', 'without', 'again', 'great', 'around', 'another', 'came', 'three', 'high', 'upon', 'school', 'still', 'hand', 'little', 'world', 'often', 'until', 'country', 'never', 'both', 'order', 'during', 'between', 'become', 'water', 'another', 'right', 'though', 'each', 'which', 'show', 'head', 'began', 'left', 'turn', 'asked', 'move', 'while', 'last', 'made', 'white', 'next', 'sound', 'once', 'large', 'light', 'name', 'play', 'away', 'live', 'home', 'today', 'place', 'always', 'point', 'going', 'same', 'second', 'night', 'looked', 'help', 'old', 'part', 'word', 'long', 'story', 'help', 'seem', 'line', 'black', 'kind', 'came', 'sure', 'done', 'being', 'open', 'group', 'young', 'got', 'state', 'need', 'public', 'called', 'held', 'life', 'face', 'fact', 'give', 'across', 'walk', 'form', 'hard', 'having', 'heard', 'means', 'money', 'along', 'began', 'building', 'call', 'eyes', 'feel', 'known', 'looking', 'several', 'side', 'social', 'thought', 'used', 'using', 'whole', 'within', 'question', 'include', 'major', 'often', 'seen', 'something', 'together', 'turned', 'water', 'since', 'either', 'until', 'went', 'without', 'against', 'came', 'different', 'many', 'sometimes', 'started', 'himself', 'family', 'person', 'business', 'possible', 'nothing', 'almost', 'course', 'community', 'enough', 'himself', 'important', 'information', 'looking', 'really', 'someone', 'system', 'things', 'women', 'always', 'program', 'process', 'right', 'should', 'small', 'example', 'general', 'government', 'group', 'hand', 'health', 'high', 'important', 'increase', 'interest', 'large', 'national', 'number', 'often', 'place', 'point', 'political', 'possible', 'president', 'problem', 'provide', 'public', 'really', 'right', 'seems', 'service', 'should', 'small', 'social', 'something', 'state', 'students', 'system', 'though', 'three', 'through', 'today', 'together', 'university', 'water', 'white', 'without', 'women', 'world', 'years', 'young'}
        
        concepts = set()
        for word in words:
            if len(word) >= 4 and word not in stopwords:
                concepts.add(word)
        
        # Limit to most relevant concepts
        return set(list(concepts)[:10])  # Top 10 concepts
    
    def _hash_content(self, data: Dict[str, Any]) -> str:
        """Create a hash of the content for similarity comparison"""
        content_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _create_similarity_edges(self, node_id: str):
        """Create similarity edges between nodes"""
        current_node = self.nodes[node_id]
        current_concepts = set(current_node.properties.get('concepts', []))
        
        for other_id, other_node in self.nodes.items():
            if other_id == node_id or other_node.type != current_node.type:
                continue
            
            other_concepts = set(other_node.properties.get('concepts', []))
            
            # Calculate Jaccard similarity
            if current_concepts and other_concepts:
                intersection = len(current_concepts & other_concepts)
                union = len(current_concepts | other_concepts)
                similarity = intersection / union if union > 0 else 0
                
                # Create edge if similarity is significant
                if similarity > 0.2:  # Threshold for similarity
                    self._add_edge(
                        node_id, other_id, "similar_to", 
                        weight=similarity,
                        properties={'similarity_score': similarity}
                    )
    
    def _connect_task_to_memories(self, task_id: str, task_data: Dict[str, Any]):
        """Connect task nodes to related memory nodes"""
        task_workspace = task_data.get('workspace', '')
        task_concepts = self._extract_concepts(task_data)
        
        for node_id, node in self.nodes.items():
            if node.type == 'memory':
                memory_workspace = node.properties.get('workspace', '')
                memory_concepts = set(node.properties.get('concepts', []))
                
                # Connect if same workspace
                if task_workspace and task_workspace == memory_workspace:
                    self._add_edge(task_id, node_id, "workspace_related", weight=0.5)
                
                # Connect if shared concepts
                shared_concepts = task_concepts & memory_concepts
                if shared_concepts:
                    concept_similarity = len(shared_concepts) / max(len(task_concepts), len(memory_concepts))
                    if concept_similarity > 0.3:
                        self._add_edge(
                            task_id, node_id, "concept_related",
                            weight=concept_similarity,
                            properties={'shared_concepts': list(shared_concepts)}
                        )
    
    def analyze_graph(self) -> Dict[str, Any]:
        """Perform comprehensive graph analysis"""
        current_time = time.time()
        
        # Use cache if recent
        if self._cache_timestamp > current_time - 60:  # 1 minute cache
            return self._analysis_cache
        
        if not self.graph.nodes():
            return {"status": "empty_graph", "message": "No nodes in the graph"}
        
        # Basic graph metrics
        num_nodes = self.graph.number_of_nodes()
        num_edges = self.graph.number_of_edges()
        density = nx.density(self.graph)
        
        # Node type distribution
        node_types = Counter(node.type for node in self.nodes.values())
        
        # Centrality measures (for connected components)
        components = list(nx.weakly_connected_components(self.graph))
        largest_component = max(components, key=len) if components else set()
        
        # Calculate centralities for the largest component
        centralities = {}
        if len(largest_component) > 1:
            subgraph = self.graph.subgraph(largest_component)
            try:
                centralities = {
                    'betweenness': dict(nx.betweenness_centrality(subgraph)),
                    'closeness': dict(nx.closeness_centrality(subgraph)),
                    'degree': dict(nx.degree_centrality(subgraph)),
                    'pagerank': dict(nx.pagerank(subgraph))
                }
            except:
                centralities = {}
        
        # Find influential nodes
        influential_nodes = []
        if centralities:
            pagerank_scores = centralities.get('pagerank', {})
            top_nodes = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:5]
            influential_nodes = [
                {
                    'id': node_id,
                    'label': self.nodes[node_id].label,
                    'type': self.nodes[node_id].type,
                    'score': score
                }
                for node_id, score in top_nodes if node_id in self.nodes
            ]
        
        # Concept analysis
        concept_nodes = [node for node in self.nodes.values() if node.type == 'concept']
        top_concepts = sorted(
            concept_nodes,
            key=lambda x: x.properties.get('frequency', 0),
            reverse=True
        )[:10]
        
        # Relationship analysis
        relationship_types = Counter(edge.relationship for edge in self.edges.values())
        
        analysis = {
            'graph_metrics': {
                'nodes': num_nodes,
                'edges': num_edges,
                'density': round(density, 4),
                'components': len(components),
                'largest_component_size': len(largest_component)
            },
            'node_distribution': dict(node_types),
            'relationship_distribution': dict(relationship_types),
            'influential_nodes': influential_nodes,
            'top_concepts': [
                {
                    'concept': concept.label,
                    'frequency': concept.properties.get('frequency', 0),
                    'connections': self.graph.degree(concept.id)
                }
                for concept in top_concepts
            ],
            'analysis_timestamp': current_time
        }
        
        # Cache the analysis
        self._analysis_cache = analysis
        self._cache_timestamp = current_time
        
        return analysis
    
    def find_knowledge_paths(self, source_id: str, target_id: str, max_length: int = 4) -> List[List[str]]:
        """Find knowledge paths between two nodes"""
        if source_id not in self.graph or target_id not in self.graph:
            return []
        
        try:
            # Find all simple paths up to max_length
            paths = list(nx.all_simple_paths(
                self.graph, source_id, target_id, cutoff=max_length
            ))
            return paths[:10]  # Limit to 10 paths
        except nx.NetworkXNoPath:
            return []
    
    def get_node_neighborhood(self, node_id: str, depth: int = 2) -> Dict[str, Any]:
        """Get the neighborhood of a node up to a certain depth"""
        if node_id not in self.graph:
            return {}
        
        # Get all nodes within depth
        neighbors = set([node_id])
        current_level = set([node_id])
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.successors(node))
                next_level.update(self.graph.predecessors(node))
            current_level = next_level - neighbors
            neighbors.update(current_level)
        
        # Extract subgraph
        subgraph = self.graph.subgraph(neighbors)
        
        return {
            'center_node': node_id,
            'neighborhood_size': len(neighbors),
            'nodes': [self.nodes[nid].to_dict() for nid in neighbors if nid in self.nodes],
            'edges': [
                {
                    'source': u,
                    'target': v,
                    'data': data
                }
                for u, v, data in subgraph.edges(data=True)
            ]
        }
    
    def export_graph(self, format: str = 'json', file_path: Optional[Path] = None) -> Path:
        """Export the knowledge graph in various formats"""
        if file_path is None:
            file_path = self.workspace_path / ".neuroforge" / "knowledge_graph" / f"graph_{int(time.time())}.{format}"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            # Convert sets to lists for JSON serialization
            def convert_sets_to_lists(obj):
                if isinstance(obj, dict):
                    return {k: convert_sets_to_lists(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_sets_to_lists(item) for item in obj]
                elif isinstance(obj, set):
                    return list(obj)
                else:
                    return obj
            
            graph_data = {
                'nodes': [convert_sets_to_lists(node.to_dict()) for node in self.nodes.values()],
                'edges': [convert_sets_to_lists(edge.to_dict()) for edge in self.edges.values()],
                'analysis': convert_sets_to_lists(self.analyze_graph()),
                'export_timestamp': time.time()
            }
            
            with open(file_path, 'w') as f:
                json.dump(graph_data, f, indent=2)
        
        elif format == 'gexf':
            # Export as GEXF for Gephi visualization
            nx.write_gexf(self.graph, file_path)
        
        elif format == 'graphml':
            # Export as GraphML for other tools
            nx.write_graphml(self.graph, file_path)
        
        logger.info(f"Knowledge graph exported to {file_path}")
        return file_path

# Global knowledge graph instance
_global_graph: Optional[KnowledgeGraphBuilder] = None

def get_knowledge_graph() -> KnowledgeGraphBuilder:
    """Get the global knowledge graph instance"""
    global _global_graph
    if _global_graph is None:
        _global_graph = KnowledgeGraphBuilder()
    return _global_graph

# Example usage and testing
if __name__ == "__main__":
    def test_knowledge_graph():
        """Test the knowledge graph system"""
        print("🧠 Testing NeuroForge Knowledge Graph")
        
        graph = KnowledgeGraphBuilder()
        
        # Add test data
        memory_data = {
            'title': 'Python function optimization',
            'content': 'How to optimize Python functions using caching and memoization',
            'type': 'code_snippet',
            'workspace': '/project/backend',
            'tags': ['python', 'optimization', 'performance']
        }
        
        task_data = {
            'description': 'Optimize database queries',
            'plugin': 'performance_analyzer',
            'status': 'completed',
            'workspace': '/project/backend',
            'parameters': {'target': 'database'}
        }
        
        file_data = {
            'size': 1024,
            'language': 'python',
            'last_modified': time.time()
        }
        
        # Add nodes
        memory_id = graph.add_memory_node('mem1', memory_data)
        task_id = graph.add_task_node('task1', task_data)
        file_id = graph.add_file_node('/project/backend/optimize.py', file_data)
        
        # Analyze graph
        analysis = graph.analyze_graph()
        print(f"Graph Analysis: {json.dumps(analysis, indent=2)}")
        
        # Export graph
        export_path = graph.export_graph()
        print(f"Graph exported to: {export_path}")
        
        print("✅ Knowledge graph test completed")
    
    test_knowledge_graph()
