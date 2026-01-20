# Architecture Migration: Core/Router/Memory Separation

## Overview

Migrate Ollie from monolithic FastAPI app to modular architecture (Core/Router/Memory) with job-based routing, memory tiering, and feedback logging while maintaining backward compatibility.

**⚠️ IMPORTANT: Use feature branches for all work**
- Create a feature branch for each PR (e.g., `feature/pr1-memory-interface`, `feature/pr2-feedback-logging`)
- Do not commit directly to `main` branch
- Each PR should be independently reviewable and shippable

## Current State

### Architecture Overview

Ollie is currently a **monolithic FastAPI application** with the following structure:

```
User Input → FastAPI Core (/chat) → Memory Search → LLM Call → Response
```

### Current Components

**Services (Deployed via Helm):**
- `ollie-core`: FastAPI orchestrator (single pod)
- `ollie-whisper`: STT service (faster-whisper)
- `ollie-ollama`: LLM service (Ollama)
- `ollie-tts`: TTS service (Coqui)
- `ollie-ui`: Streamlit UI (legacy)
- `ollie-frontend`: React frontend (real-time transcription)
- `ollie-training`: CronJob for daily fine-tuning

**Source Code Structure:**
```
src/ollie/
├── core/
│   └── app.py              # Main FastAPI app (all orchestration)
├── memory/
│   ├── retrieval.py        # MemorySystem (ChromaDB wrapper)
│   └── embeddings.py       # EmbeddingService (SentenceTransformers)
├── storage/
│   ├── database.py         # SQLAlchemy setup
│   └── models.py          # Session, Conversation models
├── llm/
│   └── ollama_client.py   # Ollama client (unused in app.py)
├── transcription/         # Whisper service code
├── tts/                   # TTS service code
├── training/
│   ├── train.py           # Fine-tuning pipeline
│   └── export.py          # Export conversations to JSONL
└── ui/                    # Streamlit UI
```

### Current Flow

```
┌─────────────┐
│   User      │
│  (Frontend) │
└──────┬──────┘
       │ POST /chat
       ▼
┌─────────────────────────────────────┐
│     FastAPI Core (app.py)           │
│  ┌───────────────────────────────┐  │
│  │ 1. memory_system.search()    │  │
│  │    → ChromaDB query          │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 2. Build system prompt       │  │
│  │    (hardcoded in app.py)     │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 3. Call Ollama API           │  │
│  │    (direct HTTP call)        │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ 4. Save to SQLite            │  │
│  │    (Conversation model)      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Response  │
└─────────────┘
```

### Current Limitations

1. **No Routing**: Single `/chat` endpoint handles all queries
2. **No Job Separation**: All queries treated as "communicator" job
3. **No Confidence Scoring**: No router confidence output
4. **No Memory Tiering**: Single ChromaDB collection, no gold/silver/scratch tiers
5. **No Feedback Logging**: Only training export exists, no correction logging
6. **Hardcoded Prompts**: System prompt embedded in `app.py` (line 91-96)
7. **No Prompt Versioning**: No versioning or external prompt files
8. **Tight Coupling**: Core directly calls memory, LLM, storage

## Target State

### Target Architecture

```
User Input → Router → Core (Job Handler) → Memory (RAG) → Answer → Feedback Log
```

### Target Components

**Locked Components:**
- `ollie-core`: Main orchestrator (LLM client, prompt assembly, tool calling, safety/policy, job execution)
- `ollie-router`: Selects job (memory|communicator|verifier|builder|planner|decision|explainer) with confidence, optional secondary
- `ollie-memory`: Knowledge + RAG ingestion + retrieval + durable storage + feedback logs

**Optional Components:**
- `ollie-evals`: Router + prompt + retrieval regression tests
- `ollie-ui`: Frontend (already exists)

### Proposed Repository Structure

```
ollie/
├── src/
│   ├── ollie_core/              # Core orchestrator
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI entrypoint
│   │   ├── orchestrator.py     # Main orchestration logic
│   │   ├── jobs/
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # BaseJobHandler interface
│   │   │   ├── communicator.py  # Default chat job
│   │   │   ├── memory.py        # Memory search job
│   │   │   ├── verifier.py      # Verification job
│   │   │   ├── builder.py       # Code/build job
│   │   │   ├── planner.py       # Planning job
│   │   │   ├── decision.py      # Decision job
│   │   │   └── explainer.py     # Explanation job
│   │   └── prompts/
│   │       ├── system.prompt.md
│   │       └── jobs/
│   │           ├── communicator.prompt.md
│   │           └── ...
│   ├── ollie_router/             # Router component
│   │   ├── __init__.py
│   │   ├── router.py            # Router class
│   │   ├── models.py            # RouterOutput (job, confidence, secondary)
│   │   └── prompts/
│   │       └── router.prompt.md
│   ├── ollie_memory/             # Memory component
│   │   ├── __init__.py
│   │   ├── memory.py            # MemorySystem (refactored)
│   │   ├── tiers.py             # Tier management (gold/silver/scratch)
│   │   ├── feedback.py          # Feedback logging
│   │   └── embeddings.py        # EmbeddingService (moved)
│   ├── ollie_storage/            # Storage (refactored)
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py            # Add Feedback model
│   └── ollie_utils/              # Shared utilities
│       ├── __init__.py
│       └── config.py
├── prompts/                      # Versioned prompts (optional external)
│   ├── v1/
│   │   ├── system.prompt.md
│   │   └── router.prompt.md
│   └── v2/
│       └── ...
├── tests/
│   ├── test_router.py
│   ├── test_memory.py
│   └── test_jobs.py
└── helm/ollie/
    ├── templates/
    │   ├── deployment-core.yaml
    │   ├── deployment-router.yaml  # NEW
    │   └── ...
    └── values.yaml
```

### Contracts

**Router Output Contract:**
```python
class RouterOutput(BaseModel):
    job: Literal["memory", "communicator", "verifier", "builder", "planner", "decision", "explainer"]
    confidence: Literal["high", "medium", "low"]
    secondary: Optional[str] = None
    reasoning: Optional[str] = None
```

**Memory Contract:**
```python
class MemoryInterface:
    def search(self, query: str, k: int = 5, filters: Dict = None) -> List[Passage]:
        """Returns passages + metadata"""
    
    def ingest(self, doc: str, tier: Literal["gold", "silver", "scratch"], tags: List[str] = None):
        """Ingest document into specified tier"""
    
    def log_correction(self, question: str, ollie_answer: str, correct_answer: str, tags: List[str] = None):
        """Log feedback correction"""
```

**Feedback Contract:**
```jsonl
{"question": "...", "ollie_answer": "...", "correct_answer": "...", "tags": ["..."], "timestamp": "2025-01-XX..."}
```

## Gap Analysis

| Area | Current | Target | Impact | Priority |
|------|---------|--------|--------|----------|
| **Routing** | None - single `/chat` endpoint | Router component with job selection + confidence | High - core architecture change | P0 |
| **Job Separation** | All queries treated as "communicator" | 7 job types (memory, communicator, verifier, builder, planner, decision, explainer) | High - requires job handlers | P0 |
| **Memory Tiering** | Single ChromaDB collection | Gold/Silver/Scratch tiers with filtering | Medium - improves RAG quality | P1 |
| **Feedback Logging** | Only training export (JSONL conversations) | Dedicated feedback logging with correction format | Medium - enables eval/improvement | P1 |
| **Prompt Management** | Hardcoded in `app.py` | Versioned prompt files (`.prompt.md`) | Medium - enables prompt versioning | P1 |
| **Confidence Scoring** | None | Router outputs confidence (high/medium/low) | Medium - enables fallback logic | P1 |
| **Interfaces** | Direct imports, tight coupling | Abstract interfaces (Router, Memory, Job) | High - enables testing/mocking | P0 |
| **Deployment** | Single core pod | Router pod (optional) or router in core | Low - can be same pod initially | P2 |

## Migration Plan

### Strategy: Strangler Fig Pattern

Wrap existing code with interfaces, then refactor behind them. Each PR is independently shippable and maintains backward compatibility.

**Branch Strategy:**
- Create feature branch for each PR: `feature/pr{N}-{description}`
- Example: `feature/pr1-memory-interface`, `feature/pr2-feedback-logging`
- Each branch should be independently reviewable and mergeable

---

### PR-1: Extract Memory Interface and Add Tiering Foundation

**Branch:** `feature/pr1-memory-interface`

**Objective:** Create `ollie_memory` package with interface, add tier support to ChromaDB without breaking existing code.

**Changes:**
1. Create `src/ollie_memory/` package structure
2. Move `memory/retrieval.py` → `ollie_memory/memory.py`
3. Move `memory/embeddings.py` → `ollie_memory/embeddings.py`
4. Create `ollie_memory/tiers.py` with tier constants and collection naming
5. Update `MemorySystem` to support tiered collections (default: "scratch" for backward compat)
6. Create `ollie_memory/__init__.py` exporting `MemorySystem`
7. Update `core/app.py` to import from `ollie_memory` (backward compatible)

**Files Touched:**
- `src/ollie_memory/` (new package)
- `src/ollie/core/app.py` (import change only)
- `pyproject.toml` (no change needed, same package)

**Acceptance Criteria:**
- ✅ Existing `/chat` endpoint works unchanged
- ✅ Memory system uses "scratch" tier by default
- ✅ Can create gold/silver collections (not used yet)
- ✅ All tests pass

---

### PR-2: Add Feedback Logging Infrastructure

**Branch:** `feature/pr2-feedback-logging`

**Objective:** Add feedback logging system with JSONL output, integrate into memory component.

**Changes:**
1. Create `ollie_memory/feedback.py` with `FeedbackLogger` class
2. Add `Feedback` model to `ollie_storage/models.py`:
   ```python
   class Feedback(Base):
       question: str
       ollie_answer: str
       correct_answer: str
       tags: JSON (or comma-separated)
       timestamp: datetime
   ```
3. Add migration for Feedback table
4. Add `log_correction()` method to `MemorySystem`
5. Create `/feedback` endpoint in `core/app.py` (optional, for future use)

**Files Touched:**
- `src/ollie_memory/feedback.py` (new)
- `src/ollie_storage/models.py` (add Feedback)
- `src/ollie/core/app.py` (add endpoint)
- `src/ollie/database/migrations/` (new migration)

**Acceptance Criteria:**
- ✅ Feedback can be logged via `MemorySystem.log_correction()`
- ✅ Feedback stored in SQLite + JSONL file (`/data/feedback/corrections.jsonl`)
- ✅ No impact on existing chat flow
- ✅ All tests pass

---

### PR-3: Extract Router Component (Interface + Stub Implementation)

**Branch:** `feature/pr3-router-stub`

**Objective:** Create `ollie_router` package with interface and stub implementation that always returns "communicator" job.

**Changes:**
1. Create `src/ollie_router/` package
2. Create `ollie_router/models.py` with `RouterOutput` Pydantic model
3. Create `ollie_router/router.py` with `Router` class:
   ```python
   class Router:
       def route(self, query: str, context: Dict = None) -> RouterOutput:
           # Stub: always return communicator, high confidence
           return RouterOutput(job="communicator", confidence="high")
   ```
4. Create `prompts/router.prompt.md` (placeholder for future)
5. Update `core/app.py` to call router before processing (no-op for now)

**Files Touched:**
- `src/ollie_router/` (new package)
- `src/ollie/core/app.py` (add router call, ignore output for now)
- `prompts/router.prompt.md` (new)

**Acceptance Criteria:**
- ✅ Router can be imported and called
- ✅ Router always returns `{"job": "communicator", "confidence": "high"}`
- ✅ Existing behavior unchanged
- ✅ All tests pass

---

### PR-4: Extract Job Handlers Framework

**Branch:** `feature/pr4-job-handlers`

**Objective:** Create job handler base class and move existing chat logic into `CommunicatorJob`.

**Changes:**
1. Create `src/ollie_core/jobs/` directory
2. Create `jobs/base.py` with `BaseJobHandler` abstract class:
   ```python
   class BaseJobHandler:
       def execute(self, query: str, context: Dict) -> str:
           raise NotImplementedError
   ```
3. Create `jobs/communicator.py` with `CommunicatorJob`:
   - Move chat logic from `app.py` `/chat` endpoint
   - Use existing memory search + LLM call
4. Create `jobs/__init__.py` exporting all jobs
5. Update `core/app.py` to use `CommunicatorJob` instead of inline logic

**Files Touched:**
- `src/ollie_core/jobs/` (new)
- `src/ollie/core/app.py` (refactor `/chat` to use CommunicatorJob)
- `src/ollie_core/orchestrator.py` (new, wraps job execution)

**Acceptance Criteria:**
- ✅ `/chat` endpoint behavior identical to before
- ✅ Code is cleaner, job logic separated
- ✅ Can add new jobs without touching core app
- ✅ All tests pass

---

### PR-5: Implement Real Router with LLM-Based Routing

**Branch:** `feature/pr5-real-router`

**Objective:** Implement router that uses LLM to select job with confidence scoring.

**Changes:**
1. Update `ollie_router/router.py`:
   - Load `prompts/router.prompt.md`
   - Call Ollama with router prompt
   - Parse response to extract job, confidence, secondary
   - Add fallback logic (if parsing fails, default to communicator)
2. Add router prompt template with examples
3. Add router tests in `tests/test_router.py`
4. Update `core/app.py` to use router output to select job handler

**Files Touched:**
- `src/ollie_router/router.py` (implement LLM routing)
- `prompts/router.prompt.md` (add prompt template)
- `src/ollie/core/app.py` (use router output)
- `tests/test_router.py` (new)

**Acceptance Criteria:**
- ✅ Router can route queries to different jobs
- ✅ Confidence scoring works (high/medium/low)
- ✅ Fallback to communicator if router fails
- ✅ Router tests pass
- ✅ Integration tests pass

---

### PR-6: Add Remaining Job Handlers

**Branch:** `feature/pr6-remaining-jobs`

**Objective:** Implement remaining job handlers (memory, verifier, builder, planner, decision, explainer).

**Changes:**
1. Create `jobs/memory.py` - Enhanced memory search job
2. Create `jobs/verifier.py` - Verification/fact-checking job
3. Create `jobs/builder.py` - Code generation job
4. Create `jobs/planner.py` - Planning job
5. Create `jobs/decision.py` - Decision-making job
6. Create `jobs/explainer.py` - Explanation job
7. Create prompt files for each job in `prompts/jobs/`
8. Update `core/app.py` to map router output to job handlers

**Files Touched:**
- `src/ollie_core/jobs/*.py` (6 new job files)
- `prompts/jobs/*.prompt.md` (6 new prompt files)
- `src/ollie/core/app.py` (job mapping)

**Acceptance Criteria:**
- ✅ All 7 job types implemented
- ✅ Router can route to any job
- ✅ Each job has appropriate prompt
- ✅ Jobs can be tested independently
- ✅ All tests pass

---

### PR-7: Implement Memory Tiering

**Branch:** `feature/pr7-memory-tiering`

**Objective:** Enable memory tiering (gold/silver/scratch) with filtering in search.

**Changes:**
1. Update `ollie_memory/memory.py`:
   - Modify `search_memory()` to accept `tier_filter` parameter
   - Query appropriate collection(s) based on tier
   - Combine results with tier metadata
2. Update `ollie_memory/tiers.py` with tier priority logic
3. Update job handlers to specify tier preferences
4. Add migration script to move existing data to "scratch" tier

**Files Touched:**
- `src/ollie_memory/memory.py` (tier filtering)
- `src/ollie_memory/tiers.py` (tier logic)
- `src/ollie_core/jobs/*.py` (specify tiers)
- `scripts/migrate_to_tiers.py` (new migration script)

**Acceptance Criteria:**
- ✅ Memory search can filter by tier
- ✅ Existing data migrated to "scratch"
- ✅ Gold tier used for high-confidence knowledge
- ✅ Backward compatible (defaults to all tiers)
- ✅ All tests pass

---

### PR-8: Extract Prompts to Versioned Files

**Branch:** `feature/pr8-prompt-extraction`

**Objective:** Move all hardcoded prompts to `.prompt.md` files with versioning.

**Changes:**
1. Extract system prompt from `app.py` → `prompts/system.prompt.md`
2. Extract job prompts → `prompts/jobs/*.prompt.md`
3. Create `ollie_core/prompts/loader.py` to load prompts
4. Update all job handlers to use prompt loader
5. Add prompt versioning scheme (v1, v2, etc.)

**Files Touched:**
- `prompts/` directory (new structure)
- `src/ollie_core/prompts/loader.py` (new)
- `src/ollie_core/jobs/*.py` (use prompt loader)
- `src/ollie/core/app.py` (remove hardcoded prompts)

**Acceptance Criteria:**
- ✅ No hardcoded prompts in code
- ✅ Prompts can be versioned
- ✅ Prompt changes don't require code changes
- ✅ Backward compatible (defaults to v1)
- ✅ All tests pass

---

### PR-9: Add Router Regression Tests and Eval Harness

**Branch:** `feature/pr9-eval-framework`

**Objective:** Create evaluation framework for router and memory retrieval.

**Changes:**
1. Create `tests/eval/` directory
2. Create `tests/eval/test_router_regression.py` - Router accuracy tests
3. Create `tests/eval/test_memory_retrieval.py` - RAG retrieval tests
4. Create `tests/eval/fixtures/` with test queries and expected outputs
5. Add `make eval` command to run evaluations

**Files Touched:**
- `tests/eval/` (new test suite)
- `Makefile` (add eval target)

**Acceptance Criteria:**
- ✅ Router regression tests pass
- ✅ Memory retrieval tests pass
- ✅ Can run `make eval` to check system health
- ✅ CI/CD runs eval tests

---

### PR-10: Update Helm Charts for New Architecture

**Branch:** `feature/pr10-helm-updates`

**Objective:** Update Helm charts to support router component (optional separate pod or same pod).

**Changes:**
1. Update `helm/ollie/values.yaml`:
   - Add router configuration section
   - Add option to deploy router as separate pod or in-core
2. Create `helm/ollie/templates/deployment-router.yaml` (optional, if separate pod)
3. Update `deployment-core.yaml` to include router env vars
4. Add health checks for router component

**Files Touched:**
- `helm/ollie/values.yaml` (router config)
- `helm/ollie/templates/deployment-core.yaml` (env vars)
- `helm/ollie/templates/deployment-router.yaml` (new, optional)

**Acceptance Criteria:**
- ✅ Helm chart deploys successfully
- ✅ Router can run in-core or separate pod
- ✅ Health checks work
- ✅ Backward compatible (router in-core by default)
- ✅ Deployment tested in staging

---

## Risks & Mitigations

### Risk 1: Router Accuracy Degrades User Experience
**Mitigation:** 
- Start with stub router (PR-3) that always returns communicator
- Implement real router (PR-5) with extensive fallback logic
- Add regression tests (PR-9) to catch accuracy issues
- Monitor router outputs in production, log failures

### Risk 2: Memory Tiering Breaks Existing Queries
**Mitigation:**
- Default to "scratch" tier for all existing data (PR-1)
- Search all tiers by default, filtering is optional (PR-7)
- Add migration script to verify data integrity
- Keep backward compatibility flag

### Risk 3: Job Handlers Increase Complexity
**Mitigation:**
- Start with single job (communicator) that matches current behavior (PR-4)
- Add jobs incrementally (PR-6)
- Each job is independently testable
- Document job selection criteria clearly

### Risk 4: Prompt Extraction Breaks Production
**Mitigation:**
- Extract prompts gradually (PR-8)
- Keep hardcoded prompts as fallback initially
- Version prompts, can rollback easily
- Test prompt loading in CI/CD

### Risk 5: Helm Deployment Issues
**Mitigation:**
- Keep router in-core pod initially (simpler deployment)
- Make separate router pod optional (PR-10)
- Test Helm charts in staging before production
- Document rollback procedure

## Implementation Notes

### Naming Conventions
- Package names: `ollie_core`, `ollie_router`, `ollie_memory` (snake_case)
- Class names: `Router`, `MemorySystem`, `CommunicatorJob` (PascalCase)
- File names: `router.py`, `memory.py`, `communicator.py` (snake_case)

### Backward Compatibility
- All PRs maintain existing API contracts
- `/chat` endpoint behavior unchanged until PR-5
- Default values match current behavior
- Can rollback any PR independently

### Testing Strategy
- Unit tests for each component (router, memory, jobs)
- Integration tests for full flow
- Regression tests for router accuracy
- Eval harness for system health

### Deployment Strategy
- Deploy PRs incrementally to staging
- Monitor metrics after each PR
- Rollback plan for each PR
- Document breaking changes (none expected)

## Success Criteria

1. ✅ Router can route queries to appropriate jobs with confidence
2. ✅ Memory system supports tiering (gold/silver/scratch)
3. ✅ Feedback logging captures corrections in JSONL format
4. ✅ Prompts are versioned and externalized
5. ✅ All 7 job types implemented and testable
6. ✅ Backward compatibility maintained throughout migration
7. ✅ Helm charts support new architecture
8. ✅ Evaluation framework exists for regression testing

## Labels

- `enhancement`
- `architecture`
- `breaking-change` (only if we decide to break compatibility)
- `good-first-issue` (for PR-1, PR-3, PR-9)

## Related Issues

- Link to any related issues or discussions

---

**Note:** This migration follows a "strangler fig" pattern - each PR wraps existing code with new interfaces, then refactors behind them. This ensures minimal risk and allows incremental deployment.













