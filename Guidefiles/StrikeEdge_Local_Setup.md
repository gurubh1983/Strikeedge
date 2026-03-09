# StrikeEdge Local Development Setup (No Docker)

## Overview

This guide sets up StrikeEdge for local development **without Docker Desktop**, using free tools and services only. Once fully tested locally, we'll migrate to AWS paid services.

---

## Development Philosophy

```
LOCAL FIRST (Free) ──────────────────────────────▶ PRODUCTION (Paid)
                                                   
SQLite/PostgreSQL (local)  ──▶  Aurora Serverless
File-based cache           ──▶  ElastiCache Redis  
Local Python scripts       ──▶  AWS Lambda
Ollama (local LLM)         ──▶  AWS Bedrock
File storage               ──▶  S3 Vectors
Manual testing             ──▶  Automated CI/CD
```

---

## Free Tools Stack

| Component | Local (Free) | Production (Paid) |
|-----------|--------------|-------------------|
| **Database** | SQLite → PostgreSQL (local) | Aurora Serverless |
| **Cache** | File-based / Python dict | ElastiCache Redis |
| **Task Queue** | In-process / SQLite queue | SQS + Lambda |
| **LLM** | Ollama (Llama3, Mistral) | AWS Bedrock |
| **Embeddings** | sentence-transformers (local) | SageMaker |
| **Vector DB** | ChromaDB (local) | S3 Vectors |
| **API** | FastAPI (uvicorn) | API Gateway + Lambda |
| **Frontend** | Vite dev server | CloudFront + S3 |
| **Data Source** | Fyers API v3 (Free) | Same |

---

## Step 1: Environment Setup

### 1.1 Install Python with uv

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installation
uv --version
```

### 1.2 Install Node.js

Download from https://nodejs.org (LTS version)

```bash
# Verify
node --version  # Should be 20+
npm --version
```

### 1.3 Install Ollama (Free Local LLM)

Download from https://ollama.ai

```bash
# After installation, pull models
ollama pull llama3.2        # 3B model, fast
ollama pull mistral         # 7B model, better quality
ollama pull nomic-embed-text # Embeddings model

# Verify Ollama is running
ollama list
```

### 1.4 Install PostgreSQL (Optional, SQLite works too)

Download from https://www.postgresql.org/download/

Or use SQLite (no installation needed - comes with Python)

---

## Step 2: Project Setup

### 2.1 Create Project Structure

```bash
# Create project directory
mkdir strikeedge
cd strikeedge

# Create directory structure
mkdir -p backend/{api,data_pipeline,indicators,screener,agents,database}
mkdir -p backend/agents/{orchestrator,researcher,backtester,optimizer,scanner,analyzer,risk,tagger,sentiment,greeks,reporter}
mkdir -p frontend/web
mkdir -p data/{cache,vectors,candles,logs}
mkdir -p tests/{unit,integration}
mkdir -p scripts

# Initialize git
git init
echo "data/\n.env\n__pycache__/\n*.pyc\n.venv/\nnode_modules/" > .gitignore
```

### 2.2 Initialize Python Backend

```bash
cd backend

# Initialize with uv
uv init

# Add core dependencies (all free)
uv add fastapi uvicorn[standard]  # API framework
uv add sqlalchemy aiosqlite       # Database (SQLite async)
uv add pandas numpy               # Data processing
uv add pandas-ta                  # Technical indicators
uv add httpx websockets           # HTTP & WebSocket client
uv add pydantic pydantic-settings # Data validation
uv add python-dotenv              # Environment variables
uv add chromadb                   # Local vector database
uv add sentence-transformers     # Local embeddings
uv add ollama                     # Ollama Python client
uv add apscheduler                # Task scheduling
uv add rich                       # Beautiful terminal output
uv add pytest pytest-asyncio      # Testing

cd ..
```

### 2.3 Create Environment File

```bash
# Create .env file
cat > .env << 'EOF'
# StrikeEdge Local Development Configuration

# Fyers API v3 (Free)
FYERS_APP_ID=XXXXXX-100
FYERS_SECRET_KEY=your_secret_key
FYERS_REDIRECT_URI=https://127.0.0.1:8000/callback
FYERS_TOTP_SECRET=your_totp_secret

# Database (SQLite for local)
DATABASE_URL=sqlite+aiosqlite:///./data/strikeedge.db

# Cache directory
CACHE_DIR=./data/cache

# Vector DB directory  
VECTOR_DB_DIR=./data/vectors

# Candle data directory
CANDLE_DIR=./data/candles

# Ollama (Local LLM)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Development mode
DEBUG=true
EOF
```

---

## Step 3: Database Setup (SQLite - No Installation)

### 3.1 Database Schema

```python
# backend/database/models.py

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Instrument(Base):
    """F&O instruments from Fyers"""
    __tablename__ = "instruments"
    
    token = Column(String, primary_key=True)
    symbol = Column(String, index=True)
    name = Column(String)
    instrument_type = Column(String)  # OPTIDX, OPTSTK, FUTIDX, FUTSTK
    exchange = Column(String, default="NFO")
    strike_price = Column(Float, nullable=True)
    option_type = Column(String, nullable=True)  # CE, PE
    expiry = Column(DateTime, nullable=True)
    lot_size = Column(Integer, default=1)
    underlying = Column(String, index=True)
    
    # Classification (from Strike Tagger agent)
    moneyness = Column(String, nullable=True)  # ITM, ATM, OTM
    liquidity_score = Column(Float, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow)


class Candle(Base):
    """OHLCV candles for strikes"""
    __tablename__ = "candles"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    token = Column(String, ForeignKey("instruments.token"), index=True)
    timeframe = Column(String, index=True)  # 1min, 5min, 15min, etc.
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    
    # Calculated indicators (cached)
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)


class IndicatorValue(Base):
    """Current indicator values per strike"""
    __tablename__ = "indicator_values"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    token = Column(String, ForeignKey("instruments.token"), index=True)
    timeframe = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    
    # Technical indicators
    rsi = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    ema_9 = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    ema_50 = Column(Float, nullable=True)
    bollinger_upper = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)
    vwap = Column(Float, nullable=True)
    
    # Options specific
    iv = Column(Float, nullable=True)
    delta = Column(Float, nullable=True)
    gamma = Column(Float, nullable=True)
    theta = Column(Float, nullable=True)
    vega = Column(Float, nullable=True)
    oi = Column(Integer, nullable=True)
    oi_change = Column(Integer, nullable=True)


class Screener(Base):
    """User-defined screeners"""
    __tablename__ = "screeners"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, index=True, default="local_user")
    name = Column(String)
    description = Column(Text, nullable=True)
    
    # Screener configuration
    underlyings = Column(JSON)  # ["NIFTY", "BANKNIFTY"]
    timeframe = Column(String, default="5min")
    conditions = Column(JSON)  # [{indicator: "rsi", operator: ">", value: 60}]
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ScanResult(Base):
    """Scan results / signals"""
    __tablename__ = "scan_results"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    screener_id = Column(String, ForeignKey("screeners.id"), index=True)
    token = Column(String, ForeignKey("instruments.token"))
    
    # Signal details
    signal_type = Column(String)  # CROSSES_ABOVE, CROSSES_BELOW, etc.
    indicator = Column(String)
    value = Column(Float)
    
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Strike info at time of signal
    strike_price = Column(Float)
    option_type = Column(String)
    underlying = Column(String)
    spot_price = Column(Float, nullable=True)


class AgentJob(Base):
    """Agent job tracking"""
    __tablename__ = "agent_jobs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, default="local_user")
    job_type = Column(String)  # SCAN, BACKTEST, OPTIMIZE, RESEARCH
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Request
    request_payload = Column(JSON)
    
    # Agent outputs
    tagger_output = Column(JSON, nullable=True)
    greeks_output = Column(JSON, nullable=True)
    scanner_output = Column(JSON, nullable=True)
    backtest_output = Column(JSON, nullable=True)
    optimizer_output = Column(JSON, nullable=True)
    sentiment_output = Column(JSON, nullable=True)
    report_output = Column(JSON, nullable=True)
    
    # Summary
    summary = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeBase(Base):
    """Research knowledge base (replaces S3 Vectors locally)"""
    __tablename__ = "knowledge_base"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    content = Column(Text)
    metadata = Column(JSON)  # source, date, type, etc.
    embedding_id = Column(String, nullable=True)  # ChromaDB reference
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3.2 Database Initialization

```python
# backend/database/init_db.py

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/strikeedge.db")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_database():
    """Create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized successfully!")

async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

if __name__ == "__main__":
    asyncio.run(init_database())
```

---

## Step 4: Local Cache System (Replaces Redis)

```python
# backend/cache/file_cache.py

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import pickle

class FileCache:
    """
    File-based cache to replace Redis for local development.
    Simple but effective for single-user local testing.
    """
    
    def __init__(self, cache_dir: str = "./data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache = {}  # In-memory for fast access
    
    def _get_path(self, key: str) -> Path:
        """Get file path for a cache key"""
        # Sanitize key for filesystem
        safe_key = key.replace(":", "_").replace("/", "_")
        return self.cache_dir / f"{safe_key}.cache"
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set a cache value with optional TTL"""
        cache_data = {
            "value": value,
            "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store in memory
        self.memory_cache[key] = cache_data
        
        # Store to file
        path = self._get_path(key)
        with open(path, 'wb') as f:
            pickle.dump(cache_data, f)
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cache value, returns None if expired or not found"""
        # Check memory first
        if key in self.memory_cache:
            data = self.memory_cache[key]
            if datetime.fromisoformat(data["expires_at"]) > datetime.utcnow():
                return data["value"]
            else:
                del self.memory_cache[key]
        
        # Check file
        path = self._get_path(key)
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    data = pickle.load(f)
                
                if datetime.fromisoformat(data["expires_at"]) > datetime.utcnow():
                    self.memory_cache[key] = data  # Populate memory cache
                    return data["value"]
                else:
                    path.unlink()  # Delete expired
            except Exception:
                pass
        
        return None
    
    def delete(self, key: str) -> None:
        """Delete a cache entry"""
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        path = self._get_path(key)
        if path.exists():
            path.unlink()
    
    def clear(self) -> None:
        """Clear all cache"""
        self.memory_cache.clear()
        for path in self.cache_dir.glob("*.cache"):
            path.unlink()


# Global cache instance
cache = FileCache()
```

---

## Step 5: Local LLM Setup (Ollama)

```python
# backend/agents/llm_client.py

import ollama
from typing import Optional, List, Dict, Any
import json

class LocalLLMClient:
    """
    Local LLM client using Ollama.
    Free, runs locally, no API costs.
    """
    
    def __init__(
        self,
        model: str = "llama3.2",
        embed_model: str = "nomic-embed-text",
        host: str = "http://localhost:11434"
    ):
        self.model = model
        self.embed_model = embed_model
        self.client = ollama.Client(host=host)
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion"""
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat(
            model=self.model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens
            }
        )
        
        return response["message"]["content"]
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON output"""
        schema_str = json.dumps(schema, indent=2)
        
        enhanced_prompt = f"""{prompt}

Respond ONLY with valid JSON matching this schema:
{schema_str}

JSON Response:"""
        
        response = await self.generate(
            prompt=enhanced_prompt,
            system=system,
            temperature=0.3  # Lower for structured output
        )
        
        # Extract JSON from response
        try:
            # Try to find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        return {"error": "Failed to parse JSON", "raw": response}
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        response = self.client.embeddings(
            model=self.embed_model,
            prompt=text
        )
        return response["embedding"]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return [self.embed(text) for text in texts]


# Global LLM instance
llm = LocalLLMClient()
```

---

## Step 6: Local Vector Database (ChromaDB)

```python
# backend/database/vector_db.py

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os

class LocalVectorDB:
    """
    Local vector database using ChromaDB.
    Replaces S3 Vectors for local development.
    """
    
    def __init__(self, persist_dir: str = "./data/vectors"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections
        self.research_collection = self.client.get_or_create_collection(
            name="market_research",
            metadata={"description": "Market research and news"}
        )
        
        self.signals_collection = self.client.get_or_create_collection(
            name="trading_signals",
            metadata={"description": "Historical trading signals"}
        )
    
    def add_research(
        self,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float],
        doc_id: Optional[str] = None
    ) -> str:
        """Add research document to vector DB"""
        import uuid
        doc_id = doc_id or str(uuid.uuid4())
        
        self.research_collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )
        
        return doc_id
    
    def search_research(
        self,
        query_embedding: List[float],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search research documents by embedding"""
        results = self.research_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        return [
            {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            }
            for i in range(len(results["ids"][0]))
        ]
    
    def add_signal(
        self,
        content: str,
        metadata: Dict[str, Any],
        embedding: List[float]
    ) -> str:
        """Add trading signal to vector DB"""
        import uuid
        doc_id = str(uuid.uuid4())
        
        self.signals_collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata]
        )
        
        return doc_id
    
    def get_stats(self) -> Dict[str, int]:
        """Get collection statistics"""
        return {
            "research_count": self.research_collection.count(),
            "signals_count": self.signals_collection.count()
        }


# Global vector DB instance
vector_db = LocalVectorDB()
```

---

## Step 7: Local Task Queue (Replaces SQS + Lambda)

```python
# backend/queue/local_queue.py

import asyncio
from typing import Callable, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    job_type: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class LocalJobQueue:
    """
    In-process job queue to replace SQS + Lambda for local development.
    Processes jobs asynchronously in the same process.
    """
    
    def __init__(self):
        self.queue: deque[Job] = deque()
        self.jobs: Dict[str, Job] = {}
        self.handlers: Dict[str, Callable] = {}
        self.is_running = False
        self._worker_task = None
    
    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler for a job type"""
        self.handlers[job_type] = handler
        logger.info(f"Registered handler for job type: {job_type}")
    
    def submit(self, job_type: str, payload: Dict[str, Any]) -> str:
        """Submit a job to the queue"""
        job_id = str(uuid.uuid4())
        job = Job(id=job_id, job_type=job_type, payload=payload)
        
        self.jobs[job_id] = job
        self.queue.append(job)
        
        logger.info(f"Job submitted: {job_id} ({job_type})")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def get_status(self, job_id: str) -> Optional[JobStatus]:
        """Get job status"""
        job = self.jobs.get(job_id)
        return job.status if job else None
    
    async def _process_job(self, job: Job):
        """Process a single job"""
        handler = self.handlers.get(job.job_type)
        
        if not handler:
            job.status = JobStatus.FAILED
            job.error = f"No handler for job type: {job.job_type}"
            logger.error(job.error)
            return
        
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(job.payload)
            else:
                result = handler(job.payload)
            
            job.result = result
            job.status = JobStatus.COMPLETED
            logger.info(f"Job completed: {job.id}")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            logger.error(f"Job failed: {job.id} - {e}")
        
        finally:
            job.completed_at = datetime.utcnow()
    
    async def _worker(self):
        """Background worker that processes jobs"""
        logger.info("Job queue worker started")
        
        while self.is_running:
            if self.queue:
                job = self.queue.popleft()
                await self._process_job(job)
            else:
                await asyncio.sleep(0.1)  # Small delay when idle
    
    async def start(self):
        """Start the job queue worker"""
        if not self.is_running:
            self.is_running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("Job queue started")
    
    async def stop(self):
        """Stop the job queue worker"""
        self.is_running = False
        if self._worker_task:
            await self._worker_task
            logger.info("Job queue stopped")
    
    def get_pending_count(self) -> int:
        """Get count of pending jobs"""
        return len(self.queue)
    
    def get_all_jobs(self) -> List[Job]:
        """Get all jobs"""
        return list(self.jobs.values())


# Global job queue instance
job_queue = LocalJobQueue()
```

---

## Step 8: Run Everything Locally

### 8.1 Startup Script

```python
# scripts/run_local.py

import asyncio
import uvicorn
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

async def main():
    """Start all local services"""
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    
    console.print(Panel.fit(
        "[bold green]StrikeEdge Local Development[/bold green]\n"
        "[dim]Starting all services...[/dim]",
        border_style="green"
    ))
    
    # 1. Initialize database
    console.print("📦 Initializing database...", style="cyan")
    from database.init_db import init_database
    await init_database()
    
    # 2. Check Ollama
    console.print("🤖 Checking Ollama...", style="cyan")
    try:
        from agents.llm_client import llm
        response = await llm.generate("Say 'OK' if you're working")
        console.print(f"   Ollama: ✅ {response[:50]}...", style="green")
    except Exception as e:
        console.print(f"   Ollama: ❌ {e}", style="red")
        console.print("   Run: ollama serve", style="yellow")
    
    # 3. Start job queue
    console.print("📋 Starting job queue...", style="cyan")
    from queue.local_queue import job_queue
    await job_queue.start()
    
    # 4. Start API server
    console.print("🚀 Starting API server...", style="cyan")
    console.print("")
    console.print(Panel.fit(
        "[bold]API Server:[/bold] http://localhost:8000\n"
        "[bold]API Docs:[/bold]   http://localhost:8000/docs\n"
        "[bold]Health:[/bold]     http://localhost:8000/health",
        title="🌐 StrikeEdge API",
        border_style="blue"
    ))
    
    # Run uvicorn
    config = uvicorn.Config(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 Quick Start Commands

```bash
# Terminal 1: Start Ollama (if not running as service)
ollama serve

# Terminal 2: Start StrikeEdge
cd strikeedge
cd backend
uv run python ../scripts/run_local.py

# Terminal 3: Run tests
cd strikeedge/backend
uv run pytest tests/ -v
```

---

## Free Tools Summary

| Need | Free Solution | Notes |
|------|---------------|-------|
| Database | SQLite | Built into Python, zero setup |
| Cache | File-based + dict | Simple, effective for local |
| LLM | Ollama (Llama3.2) | 3GB RAM, runs on any laptop |
| Embeddings | nomic-embed-text | Via Ollama, free |
| Vector DB | ChromaDB | Local, persistent |
| Task Queue | In-process async | No external service |
| API | FastAPI + uvicorn | Industry standard |
| Data | Fyers API v3 | Free tier |
| Testing | pytest | Free |

---

## Migration Path to Production

When ready to go live:

```
LOCAL                          PRODUCTION
─────────────────────────────────────────────────────
SQLite          ──migrate──▶   Aurora Serverless
FileCache       ──migrate──▶   ElastiCache Redis
LocalJobQueue   ──migrate──▶   SQS + Lambda
Ollama          ──migrate──▶   AWS Bedrock
ChromaDB        ──migrate──▶   S3 Vectors
uvicorn         ──migrate──▶   API Gateway + Lambda
local files     ──migrate──▶   S3
```

Each component has a clean interface that makes migration straightforward!
