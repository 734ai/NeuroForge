"""
NeuroForge Memory Engine

Hybrid memory system combining RAM buffer, persistent storage (LMDB),
structured data (SQLite), and vector search (ChromaDB) for context-aware
task automation in VSCode.

Author: Muzan Sano
License: MIT
"""

import asyncio
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timezone

import lmdb
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

from pydantic import BaseModel
import git


@dataclass
class MemoryContext:
    """Represents a memory context with metadata"""
    id: str
    content: Dict[str, Any]
    tags: List[str]
    timestamp: datetime
    session_id: str
    workspace_path: Optional[str] = None
    git_hash: Optional[str] = None


class MemoryConfig(BaseModel):
    """Configuration for memory engine"""
    workspace_path: str
    memory_store_path: str = "memory_store"
    max_ram_size: int = 1000  # Max items in RAM buffer
    enable_encryption: bool = False
    vector_dimension: int = 384
    

class RAMBuffer:
    """Fast in-memory buffer for active contexts"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._buffer: Dict[str, MemoryContext] = {}
        self._access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[MemoryContext]:
        """Get item from buffer, updating access time"""
        if key in self._buffer:
            self._access_times[key] = time.time()
            return self._buffer[key]
        return None
    
    def put(self, key: str, context: MemoryContext) -> None:
        """Store item in buffer, evicting LRU if needed"""
        if len(self._buffer) >= self.max_size:
            self._evict_lru()
        
        self._buffer[key] = context
        self._access_times[key] = time.time()
    
    def _evict_lru(self) -> None:
        """Remove least recently used item"""
        if not self._access_times:
            return
        
        lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        del self._buffer[lru_key]
        del self._access_times[lru_key]
    
    def clear(self) -> None:
        """Clear all items from buffer"""
        self._buffer.clear()
        self._access_times.clear()


class PersistentStore:
    """LMDB-based persistent storage for session data"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.env = lmdb.open(str(self.db_path), max_dbs=5, map_size=100 * 1024 * 1024)  # 100MB
    
    def store_context(self, context: MemoryContext) -> None:
        """Store memory context in LMDB"""
        with self.env.begin(write=True) as txn:
            key = context.id.encode()
            value = json.dumps(asdict(context), default=str).encode()
            txn.put(key, value)
    
    def get_context(self, context_id: str) -> Optional[MemoryContext]:
        """Retrieve memory context from LMDB"""
        with self.env.begin() as txn:
            key = context_id.encode()
            value = txn.get(key)
            if value:
                data = json.loads(value.decode())
                # Convert timestamp back to datetime
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                return MemoryContext(**data)
        return None
    
    def list_contexts(self, limit: int = 100) -> List[str]:
        """List all context IDs"""
        contexts = []
        with self.env.begin() as txn:
            cursor = txn.cursor()
            for key, _ in cursor:
                contexts.append(key.decode())
                if len(contexts) >= limit:
                    break
        return contexts
    
    def close(self) -> None:
        """Close LMDB environment"""
        self.env.close()


class StructuredStore:
    """SQLite-based structured data storage"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path) / "structured.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._init_tables()
    
    def _init_tables(self) -> None:
        """Initialize database tables"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                workspace_path TEXT,
                metadata TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS workspace_state (
                workspace_path TEXT PRIMARY KEY,
                git_branch TEXT,
                git_hash TEXT,
                open_files TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def store_task(self, task_id: str, name: str, status: str, 
                   workspace_path: str, metadata: Dict[str, Any]) -> None:
        """Store task information"""
        self.conn.execute("""
            INSERT OR REPLACE INTO tasks 
            (id, name, status, workspace_path, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, name, status, workspace_path, json.dumps(metadata)))
        self.conn.commit()
    
    def get_workspace_state(self, workspace_path: str) -> Optional[Dict[str, Any]]:
        """Get current workspace state"""
        cursor = self.conn.execute("""
            SELECT git_branch, git_hash, open_files, last_updated 
            FROM workspace_state 
            WHERE workspace_path = ?
        """, (workspace_path,))
        
        row = cursor.fetchone()
        if row:
            return {
                'git_branch': row[0],
                'git_hash': row[1], 
                'open_files': json.loads(row[2]) if row[2] else [],
                'last_updated': row[3]
            }
        return None
    
    def update_workspace_state(self, workspace_path: str, git_branch: str,
                              git_hash: str, open_files: List[str]) -> None:
        """Update workspace state"""
        self.conn.execute("""
            INSERT OR REPLACE INTO workspace_state
            (workspace_path, git_branch, git_hash, open_files)
            VALUES (?, ?, ?, ?)
        """, (workspace_path, git_branch, git_hash, json.dumps(open_files)))
        self.conn.commit()


class VectorStore:
    """ChromaDB-based vector storage for semantic search"""
    
    def __init__(self, db_path: str):
        if not CHROMADB_AVAILABLE:
            print("Warning: ChromaDB not available, using simple text matching")
            self.client = None
            self.collection = None
            self._simple_store = {}
            return
            
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="neuroforge_memory",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_context(self, context: MemoryContext, embedding: Optional[List[float]] = None) -> None:
        """Add context to vector store"""
        if not CHROMADB_AVAILABLE:
            # Simple text storage fallback
            text_content = json.dumps(context.content)
            self._simple_store[context.id] = {
                'content': text_content,
                'metadata': {
                    'id': context.id,
                    'tags': ','.join(context.tags),
                    'timestamp': context.timestamp.isoformat(),
                    'session_id': context.session_id
                }
            }
            return
            
        # For now, use simple text representation
        # In production, would use proper embeddings
        text_content = json.dumps(context.content)
        
        self.collection.add(
            documents=[text_content],
            metadatas=[{
                'id': context.id,
                'tags': ','.join(context.tags),
                'timestamp': context.timestamp.isoformat(),
                'session_id': context.session_id
            }],
            ids=[context.id]
        )
    
    def search_similar(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search for similar contexts"""
        if not CHROMADB_AVAILABLE:
            # Simple text matching fallback
            results = []
            query_lower = query.lower()
            for context_id, data in self._simple_store.items():
                content = data['content'].lower()
                if query_lower in content:
                    # Simple scoring based on query length vs content length
                    score = len(query) / len(content) if content else 0
                    results.append((context_id, score))
            
            # Sort by score and return top results
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]
        
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        # Return (context_id, distance) pairs
        if results['ids'] and results['distances']:
            return list(zip(results['ids'][0], results['distances'][0]))
        return []


class MemoryEngine:
    """Main memory engine orchestrating all storage backends"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.session_id = str(uuid.uuid4())
        
        # Initialize storage backends
        self.ram_buffer = RAMBuffer(config.max_ram_size)
        self.persistent_store = PersistentStore(
            str(Path(config.workspace_path) / config.memory_store_path / "persistent")
        )
        self.structured_store = StructuredStore(
            str(Path(config.workspace_path) / config.memory_store_path)
        )
        
        # Initialize vector store with ChromaDB availability check
        self.vector_store = VectorStore(
            str(Path(config.workspace_path) / config.memory_store_path / "vector")
        )
        
        # Git integration for workspace awareness
        try:
            self.git_repo = git.Repo(config.workspace_path)
        except git.exc.GitError:
            self.git_repo = None
            
        print(f"NeuroForge Memory Engine initialized")
        if not CHROMADB_AVAILABLE:
            print("Note: Using simplified search without ChromaDB vector embeddings")
    
    async def store_memory(self, content: Dict[str, Any], tags: List[str] = None) -> str:
        """Store new memory context"""
        tags = tags or []
        context_id = str(uuid.uuid4())
        
        # Get current git state
        git_hash = None
        if self.git_repo:
            try:
                git_hash = self.git_repo.head.commit.hexsha
            except:
                pass
        
        context = MemoryContext(
            id=context_id,
            content=content,
            tags=tags,
            timestamp=datetime.now(timezone.utc),
            session_id=self.session_id,
            workspace_path=self.config.workspace_path,
            git_hash=git_hash
        )
        
        # Store in all backends
        self.ram_buffer.put(context_id, context)
        self.persistent_store.store_context(context)
        self.vector_store.add_context(context)
        
        return context_id
    
    async def retrieve_memory(self, context_id: str) -> Optional[MemoryContext]:
        """Retrieve memory context by ID"""
        # Check RAM buffer first
        context = self.ram_buffer.get(context_id)
        if context:
            return context
        
        # Check persistent store
        context = self.persistent_store.get_context(context_id)
        if context:
            # Cache in RAM for future access
            self.ram_buffer.put(context_id, context)
            return context
        
        return None
    
    async def search_memories(self, query: str, tags: List[str] = None, 
                            limit: int = 10) -> List[MemoryContext]:
        """Search memories using vector similarity"""
        similar_ids = self.vector_store.search_similar(query, limit * 2)  # Get more for filtering
        
        memories = []
        for context_id, _ in similar_ids:
            context = await self.retrieve_memory(context_id)
            if context:
                # Filter by tags if specified
                if tags and not any(tag in context.tags for tag in tags):
                    continue
                memories.append(context)
                
                if len(memories) >= limit:
                    break
        
        return memories
    
    async def get_workspace_context(self) -> Dict[str, Any]:
        """Get current workspace context"""
        context = {
            'workspace_path': self.config.workspace_path,
            'session_id': self.session_id,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Add git information
        if self.git_repo:
            try:
                context.update({
                    'git_branch': self.git_repo.active_branch.name,
                    'git_hash': self.git_repo.head.commit.hexsha,
                    'git_dirty': self.git_repo.is_dirty(),
                    'git_untracked': len(self.git_repo.untracked_files) > 0
                })
            except:
                pass
        
        return context
    
    async def update_workspace_state(self, open_files: List[str] = None) -> None:
        """Update current workspace state"""
        if not self.git_repo:
            return
        
        try:
            self.structured_store.update_workspace_state(
                self.config.workspace_path,
                self.git_repo.active_branch.name,
                self.git_repo.head.commit.hexsha,
                open_files or []
            )
        except:
            pass
    
    def close(self) -> None:
        """Clean shutdown of memory engine"""
        self.ram_buffer.clear()
        self.persistent_store.close()


# Example usage and testing
async def main():
    """Test the memory engine"""
    config = MemoryConfig(
        workspace_path="/tmp/test_workspace",
        memory_store_path="test_memory"
    )
    
    engine = MemoryEngine(config)
    
    # Store some test memories
    task_id = await engine.store_memory(
        content={'task': 'test git integration', 'status': 'completed'},
        tags=['git', 'test']
    )
    
    print(f"Stored memory: {task_id}")
    
    # Retrieve memory
    memory = await engine.retrieve_memory(task_id)
    print(f"Retrieved: {memory}")
    
    # Search memories
    results = await engine.search_memories("git integration")
    print(f"Search results: {len(results)}")
    
    # Get workspace context
    context = await engine.get_workspace_context()
    print(f"Workspace context: {context}")
    
    engine.close()


if __name__ == "__main__":
    asyncio.run(main())
