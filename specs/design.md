# Cloud FinOps & Cost Optimization Agent — Design

**Project:** Spec-Driven Architect Assistant
**Author:** Sanjay Thakur
**Status:** Design Phase Complete (v1)
**SDD Phase:** Design

---

## 1. Design Goals

The system is designed with the following key principles:

- Build a simple and modular architecture that can be implemented incrementally.
- Ensure high accuracy by relying on AWS data as the source of truth.
- Use LLM only for reasoning, explanation, and recommendation generation.
- Maintain safety by enforcing a read-only, non-destructive system design.
- Optimize for cost efficiency by minimizing unnecessary LLM usage.
- Support future extensibility for MCP, RAG, memory, and multi-cloud scenarios.
- Enable continuous evaluation through an Eval Harness.

---

## 2. Architecture Approach

The system follows a **hybrid architecture combining deterministic logic and LLM-based reasoning**.

### Deterministic Layer (Rule-based)
- Responsible for accurate data processing and validation
- Includes:
  - AWS API data collection (via MCP)
  - Cost calculations
  - Resource utilization analysis
  - Rule-based filtering and validation

### LLM-based Layer (Reasoning)
- Responsible for interpretation and decision support
- Includes:
  - Root cause analysis explanation
  - Recommendation generation
  - Natural language summarization

### Key Design Principle

Deterministic logic is used wherever outcomes are predictable and verifiable, while the LLM is used only where human-like reasoning is required.

This ensures:
- High accuracy
- Reduced hallucination risk
- Better cost control
- Easier debugging and maintenance

---

## 3. High-Level Architecture

```text
                          User / API
                              |
                              v
                    FinOps Orchestrator
                              |
              +---------------+---------------+
              |                               |
              v                               v
     MCP Server (AWS FinOps)          Internal Logic
     ----------------------           ----------------
     - AWS Data Collector             - RCA Engine (LLM)
     - Cost Analysis Engine           - Recommendation Engine (LLM)
     - Resource Inspection            - Validation Layer (rules)
                                      - Memory Layer
              |                               |
              +---------------+---------------+
                              |
                              v
                    Validation Layer (Rule-Based)
                              |
                              v
                       Memory Layer
                       (STM + LTM + Episodic)
                              |
                              v
                       Response to User
                              |
                              v
                    Eval Harness (Post-Processing / CI/CD)
```

**Key architectural distinctions:**
- **MCP Server** is a separate process exposing AWS data tools (Section 6)
- **Internal Logic** contains reasoning and business rules (Sections 7, 8)
- **Validation Layer** is inline; **Eval Harness** is offline (Section 9)

---

## 4. Main Components

### 4.1 FinOps Orchestrator
- Controls overall workflow
- Manages execution flow between components
- Decides routing: direct MCP call (fast path) vs orchestrated agent flow (Section 6.4)
- Ensures ordered execution of analysis and reasoning steps

### 4.2 AWS Data Collector (Deterministic, hosted in MCP Server)
- Connects to AWS using read-only credentials (via AssumeRole, Section 11.4)
- Retrieves:
  - Cost data (Cost Explorer)
  - Resource data (EC2, RDS, EBS)
  - Usage metrics (CloudWatch)
  - Tagging data

### 4.3 Cost Analysis Engine (Deterministic, hosted in MCP Server)
- Identifies:
  - Top cost services
  - Top cost resources
- Aggregates and processes cost data

### 4.4 Resource Inspection Engine (Deterministic, hosted in MCP Server)
- Detects inefficiencies such as:
  - Idle EC2 instances
  - Unattached EBS volumes
  - Oversized RDS instances
  - Unused Elastic IPs

### 4.5 RCA Engine (LLM-Based, internal)
- Performs root cause analysis
- Converts raw metrics into explanations
- Example:
  - "Instance has low CPU usage for 14 days -> underutilized"

### 4.6 Recommendation Engine (LLM-Based, internal)
- Generates actionable optimization recommendations
- Includes:
  - Suggested actions (stop, resize, delete, review, tag)
  - Estimated impact (savings)
  - Prioritization

### 4.7 Validation Layer (Rule-Based, internal)
- Inline guardrail (Section 8)
- Validates:
  - Resource existence (Existence Check)
  - Logical consistency (RCA matches recommendation)
  - Action whitelist (Safety)
  - Numeric sanity (Math)
- Outcomes: Retry / Remove / Escalate

### 4.8 Memory Layer (Internal)
- Multi-tier memory (Section 7):
  - Short-Term Memory (STM): session + account scoped
  - Long-Term Memory (LTM): per account, persistent
  - Episodic Memory: recommendation outcomes, persistent
- Strict isolation per account_id

### 4.9 Reporting Layer (Internal)
- Formats output for user
- Provides:
  - Summary
  - Prioritized recommendations
  - RCA explanations
  - Impact assessment

### 4.10 MCP Server (External, reusable, domain-scoped)
- Single AWS FinOps MCP server hosting data and inspection tools (Section 6)
- Exposes standardized tool interface to the orchestrator
- Authentication via AWS read-only IAM role
- Reusable across other agents and teams
- Hosts components 4.2, 4.3, 4.4 logically

---

## 5. End-to-End Request Flow

The full request lifecycle (incorporating MCP, STM, validation outcomes, and eval distinction):

1. User submits AWS cost audit request (account_id, session_id)
2. Orchestrator validates input and AssumeRole credentials
3. Orchestrator initializes STM(session_id, account_id)
4. LTM lookup: retrieve previous audit summaries for this account
5. Orchestrator routes:
   - Simple query -> direct MCP tool call (fast path)
   - Complex audit -> orchestrated agent flow
6. MCP Server fetches live AWS data (Cost Explorer, EC2, RDS, EBS, CloudWatch)
7. Cost Analysis Engine identifies top cost contributors (deterministic)
8. Resource Inspection Engine detects waste patterns (deterministic)
9. RCA Engine generates root cause explanations (LLM)
10. Recommendation Engine generates prioritized actions (LLM)
11. Validation Layer applies 4 inline checks:
    - PASS -> proceed
    - FAIL + recoverable -> Retry (max 2 attempts with augmented context)
    - FAIL + non-critical -> Remove that item, keep others
    - FAIL + safety violation -> Escalate (surface to user)
12. LTM write: store audit summary
13. Episodic write: log each recommendation with status
14. Structured response is returned to user
15. (Async / CI/CD) Eval Harness evaluates output for correctness, quality, performance, cost
16. STM clears on context switch (new account or session end)

**Critical distinctions:**
- **Validation Layer** is inline and blocks individual responses
- **Eval Harness** is offline/CI-CD and blocks deployments
- **MCP** is for live data; **Memory** is for historical context

---

## 6. MCP Design

### 6.1 MCP Strategy

The system follows a **hybrid routing pattern** that combines:
- **Direct MCP tool calls** for simple data queries (fast path)
- **Orchestrated agent flows** for complex reasoning (orchestrated path)

This separation ensures performance, cost efficiency, and clarity of system behavior.

---

### 6.2 What Goes in MCP vs Internal Code

**MCP Server (external, reusable, data-focused):**
- AWS Data Collector
- Cost Analysis queries (top services, top resources, billing summary)
- Resource Inspection (idle, unused, oversized detection)

**Internal Code (business logic, reasoning, agent-specific):**
- FinOps Orchestrator
- Validation Layer (rule-based correctness checks)
- RCA Engine (LLM-based reasoning)
- Recommendation Engine (LLM-based generation)
- Memory Layer

**MCP Boundary Framework (3 dimensions):**
- Business Purpose: What problem does this solve?
- Security Boundary: Read or write? What credentials?
- Risk Profile: What is the blast radius?

If any dimension differs significantly -> different MCP server.

---

### 6.3 MCP Server Design

The system uses **a single MCP server per domain** rather than multiple small servers per AWS service.

**MCP Server: AWS FinOps MCP**
- Domain: AWS cost optimization
- Authentication: AWS read-only IAM role (via AssumeRole)
- Exposed tools:
  - get_cost_by_service
  - get_top_resources
  - list_idle_ec2
  - list_unattached_ebs
  - list_oversized_rds
  - list_unused_elastic_ips
  - get_resource_metrics
  - get_billing_summary
- Exposed resources:
  - cost_report
  - resource_inventory

---

### 6.4 Routing Decision Matrix

| Query Type | Routing | Justification |
|------------|---------|---------------|
| Simple data lookup | Direct MCP tool call | Fast, cheap, deterministic |
| Single-fact question | Direct MCP tool call | No reasoning required |
| "Why" / "Explain" questions | Orchestrated agent flow | Requires LLM reasoning |
| Multi-step analysis | Orchestrated agent flow | Multiple components needed |
| Recommendation generation | Orchestrated agent flow | LLM + validation required |
| Full optimization report | Orchestrated agent flow | End-to-end orchestration |

---

### 6.5 Benefits of This Approach

- **Performance:** Simple queries avoid orchestration overhead
- **Cost efficiency:** LLM is only invoked when reasoning is required
- **Reusability:** MCP server can be shared across multiple agents and teams
- **Maintainability:** Clear separation between data layer and reasoning layer
- **Standardization:** Aligns with emerging enterprise MCP patterns
- **Extensibility:** Future MCP servers (Azure FinOps, GCP FinOps) can follow same pattern

---

## 7. Memory Design

### 7.1 Memory Strategy

The system uses a **multi-tier memory architecture** with strict scope isolation to ensure correctness, performance, and multi-tenant safety.

Memory is treated as a system-level capability (not an LLM property). The agent reads from and writes to memory stores to maintain context across time.

---

### 7.2 Memory Types Used in v1

The system implements three memory types in v1. Semantic memory is deferred to v2.

| Memory Type | v1 Status | Purpose |
|------------|-----------|---------|
| Short-Term Memory (STM) | Included | Maintain context within a single audit session |
| Long-Term Memory (LTM) | Included | Persist historical audit results for trend comparison |
| Episodic Memory | Included | Track past recommendations and user decisions |
| Semantic Memory | Deferred to v2 | General learned patterns across all accounts |

---

### 7.3 Memory Scope and Isolation

Strict scope isolation is enforced to prevent cross-tenant data leakage.

| Memory Type | Scope | Persistence | Reset Trigger |
|------------|-------|-------------|---------------|
| STM | (session_id, account_id) | Ephemeral | Context switch (new account or new session) |
| LTM | account_id | Permanent | Manual deletion only |
| Episodic | account_id + decision_id | Permanent | Manual deletion only |

**Critical rule:** When the user switches from Account A to Account B, STM clears completely. LTM and Episodic data for Account A remain in the database but are not retrieved unless the user switches back.

---

### 7.4 Storage Choices

| Memory Type | Storage | Rationale |
|------------|---------|-----------|
| STM | In-memory Python dict | Fast, ephemeral, session-scoped |
| LTM | PostgreSQL (structured tables) | Queryable, persistent, supports trend analysis |
| Episodic | PostgreSQL (JSONB columns) | Flexible schema for decision tracking |

Using a single database (PostgreSQL) for LTM and Episodic reduces infrastructure complexity and simplifies the eval harness.

---

### 7.5 Memory vs MCP Boundary

A clear separation is maintained between live data (MCP) and historical context (Memory).

| Data | Source | Reason |
|------|--------|--------|
| Live AWS cost data | MCP | Always fetched fresh; no staleness risk |
| Live resource metrics | MCP | Real-time CloudWatch data |
| Past audit results | LTM (Memory) | Historical comparison |
| Past recommendations + outcomes | Episodic (Memory) | Decision tracking |
| User preferences | LTM (Memory) | Personalization |

**Principle:**
- Live/changing data -> MCP (fetch on demand)
- Derived/historical data -> Memory (stored after analysis)

---

### 7.6 Memory Write Strategy

The system uses an **always-write** strategy in v1:

- After each completed audit, LTM is updated with the audit summary.
- Each recommendation generated is logged to Episodic memory with its outcome (accepted/rejected/pending).
- STM is cleared on context switch.

This trades storage growth for simplicity. Cleanup policies will be added in v2.

---

### 7.7 Multi-Tenant Safety

To prevent cross-tenant contamination:

- STM is always scoped to (session_id, account_id) and cleared on context switch.
- All LTM and Episodic queries are filtered by account_id at the database layer.
- No cross-account memory reads are permitted.
- IAM credentials for one account are never used to query data from another account.

---

### 7.8 Memory Interaction Flow

```text
User submits audit request for Account A
        |
        v
Orchestrator initializes STM(session_id, account_A)
        |
        v
LTM lookup: previous audits for Account A
        |
        v
Analysis runs (MCP fetches live AWS data)
        |
        v
Recommendations generated
        |
        v
Validation Layer checks correctness
        |
        v
LTM write: store audit summary
Episodic write: log each recommendation
        |
        v
Response to user
        |
        v
[User switches to Account B]
        |
        v
STM clears completely
        |
        v
New STM(session_id, account_B) initialized
        |
        v
LTM lookup for Account B begins
```

---

## 8. Validation Layer Design

### 8.1 Purpose

The Validation Layer is an inline rule-based guardrail that checks every LLM-generated output before it is sent to the user.

Its goal is to prevent hallucinated, unsafe, or invalid recommendations from reaching production.

Validation is deterministic, fast (<100ms target), and never uses an LLM for the validation itself.

---

### 8.2 Validation vs Eval Harness

Validation Layer and Eval Harness serve different purposes and must not be confused.

| Aspect | Validation Layer | Eval Harness |
|--------|------------------|--------------|
| When it runs | Inline, before response | Offline, after response |
| Purpose | Block bad output | Measure system quality |
| Speed | Must be fast (<100ms) | Can be slow |
| Type | Rule-based only | Rule-based + LLM-as-judge |
| Blocks response? | Yes | No |
| Failure outcome | Output rejected | Metric logged |

---

### 8.3 Validation Checks

The system implements four mandatory validation checks on every LLM output.

| Check | Type | Description |
|-------|------|-------------|
| Existence Check | Hallucination | Verifies that any resource ID referenced by the LLM exists in the current AWS inventory |
| Action Whitelist | Safety | Confirms the recommended action is within the allowed set (stop, resize, tag, review) |
| Logical Consistency | Reasoning | Verifies that the RCA and the recommendation are aligned (e.g., low CPU -> downsize, not upsize) |
| Numeric Sanity | Math | Confirms estimated savings are realistic compared to the actual resource cost |

---

### 8.4 Validation Outcomes

When a validation check fails, the system applies one of three outcomes based on severity.

| Outcome | When to Apply | Behavior |
|---------|---------------|----------|
| Reject + Retry | LLM error is recoverable (e.g., hallucinated resource ID) | Pass corrected context back to LLM; max 2 retries |
| Reject + Remove | Single bad item among many; non-critical | Drop the item; continue with valid recommendations |
| Reject + Escalate | Critical safety violation | Surface warning to user; do not silently suppress |

**Principle:** Safety violations require user visibility. Silent suppression hides system bugs.

---

### 8.5 Safety Rules (Hard Constraints)

The following rules are non-negotiable and trigger immediate Reject + Escalate.

- Recommendation to delete any resource tagged 'production' or 'prod'
- Recommendation to modify any resource outside the audited account
- Recommendation involving credentials, IAM, or security configurations
- Recommendation with estimated impact exceeding a configured threshold (e.g., $10,000/month)

---

### 8.6 Validation Position in Architecture

```text
LLM generates output
        |
        v
Validation Layer (inline, deterministic)
        |
   +----+----+
   |         |
   v         v
 PASS      FAIL
   |         |
   |    +----+----+----+
   |    |         |    |
   |  Retry   Remove Escalate
   |
   v
Response to User
```

---

### 8.7 Why Validation Must Be Deterministic

Using an LLM to validate LLM output creates a circular dependency: the same model that hallucinates is asked to detect hallucinations.

Rule-based validation provides:

- Deterministic, repeatable checks
- Fast execution (<100ms)
- Testable in unit tests
- Auditable for compliance
- No additional LLM cost

LLM-as-judge is reserved for the Eval Harness (offline measurement), never inline validation.

---

### 8.8 Retry Strategy

Retry is the most common validation outcome. To prevent infinite loops:

- Maximum 2 retry attempts per recommendation
- Each retry passes augmented context to the LLM:
  - On existence failure: pass the actual resource list
  - On logical inconsistency: pass both RCA and recommendation for re-alignment
  - On numeric failure: pass the actual cost data
- If retries exhausted: route to Reject + Remove or Reject + Escalate based on severity

---

## 9. Eval Harness Design

### 9.1 Purpose

The Eval Harness is an automated evaluation system that runs predefined test cases through the agent, measures multiple quality dimensions, logs results, and tracks performance over time.

It is independent of the production response path and does not block user responses.

The harness ensures the agent meets the acceptance criteria defined in requirements.md and detects regressions before they reach production.

---

### 9.2 Eval Harness vs Validation Layer

The Eval Harness and Validation Layer are distinct systems.

| Aspect | Eval Harness | Validation Layer |
|--------|--------------|------------------|
| When | Offline (batch or post-response async) | Inline (before response) |
| Purpose | Measure system quality | Block bad output |
| Speed | Can be slow | Must be fast (<100ms) |
| Type | Rule-based + LLM-as-judge | Rule-based only |
| Blocks response? | No | Yes |
| Failure outcome | Metric logged | Output rejected |

---

### 9.3 Four Evaluation Dimensions

The harness measures four independent dimensions on every run.

| Dimension | What It Measures | Example Metric |
|-----------|------------------|----------------|
| Correctness | Did the system produce the right answer? | % of expected idle resources detected |
| Quality | Was the explanation/recommendation high quality? | LLM-as-judge score (1-10) |
| Performance | How fast was execution? | p50/p95 latency |
| Cost | What did it cost to run? | LLM token spend per audit |

Junior systems measure only correctness. Production systems measure all four.

---

### 9.4 Test Case Categories

The system maintains test cases across five categories.

| Category | Purpose | Example |
|----------|---------|---------|
| Happy Path | Validate normal operation | Account with 5 idle EC2s detected correctly |
| Edge Cases | Boundary conditions | Empty account returns "no resources found" |
| Failure Tests | Graceful degradation | Invalid credentials produce clear error |
| Safety Tests | Validate guardrails | Production-tagged DB never recommended for deletion |
| Regression Tests | Prevent re-introduction of fixed bugs | Previously failing cases continue to pass |

Each category contributes to overall system confidence.

---

### 9.5 Ground Truth Strategy

For v1, the system uses **synthetic test data** to establish ground truth.

| Method | v1 Status | Rationale |
|--------|-----------|-----------|
| Synthetic data | Used in v1 | Controlled, repeatable, cheap, ground truth known by construction |
| Manual labeling | Deferred | Expensive and slow for v1 |
| Real AWS sandbox | Deferred to v2 | Most realistic but adds AWS cost and complexity |

Tradeoff: Synthetic data is less realistic than production data. v2 will add AWS sandbox testing to validate against real-world scenarios.

---

### 9.6 Scoring Methods

Different dimensions require different scoring methods.

| Method | Use For | Example |
|--------|---------|---------|
| Deterministic Scoring | Correctness checks, counting, numeric verification | "Did the system detect >=4 of 5 idle EC2s?" |
| LLM-as-Judge | Text quality, reasoning evaluation | "Score the RCA explanation 1-10 for clarity and accuracy" |
| Heuristic Scoring | Structured output completeness | "Does each recommendation include action, savings, risk, priority?" |

---

### 9.7 LLM-as-Judge Configuration

When using LLM-as-judge, the system enforces independence to prevent bias.

- The judge LLM is from a different model family than the agent LLM
  - Example: If agent uses Claude, judge uses GPT-4.1
  - Reason: Same-model judging creates self-confirmation bias
- The judge is given:
  - Original question
  - Ground truth reference answer (when available)
  - Generated answer
  - Scoring rubric
- The judge produces a structured score with reasoning

---

### 9.8 Execution Modes

The harness supports three execution modes.

| Mode | When It Runs | Purpose |
|------|--------------|---------|
| Batch | Nightly or scheduled | Regression detection across all test cases |
| CI/CD | On every code commit | Prevent shipping broken code |
| Post-response async (v2) | After each user request | Continuous production monitoring |

For v1, batch and CI/CD modes are implemented. Async monitoring is deferred to v2.

---

### 9.9 Test Case Definition Format

Each test case is defined as structured YAML for executability and version control.

```yaml
test_id: TC-001
category: happy_path
description: "Detect idle EC2 instances"
input:
  account_id: "synthetic-001"
  account_state:
    - 5 idle EC2 instances
    - 0 active resources
expected:
  idle_detected_min: 4
  recommendations_count_min: 3
  no_errors: true
scoring:
  method: deterministic
  pass_threshold: 0.8
```

Test cases are stored in version control and reviewed like code.

---

### 9.10 Eval Harness Architecture

```text
Test Case Definitions (YAML files in version control)
        |
        v
Eval Harness Orchestrator (separate service / Docker image)
        |
        v
For each test case:
        |
        +--> Run agent against synthetic input
        |
        +--> Capture output
        |
        +--> Apply scoring methods:
        |       - Deterministic checks
        |       - LLM-as-judge (independent model)
        |       - Heuristic scoring
        |
        +--> Measure performance (latency p50/p95)
        |
        +--> Measure cost (LLM tokens, USD)
        |
        v
Results written to PostgreSQL (eval_runs table)
        |
        v
Aggregate dashboard / pass-fail report
        |
        v
CI/CD: pass/fail signal returned to pipeline
```

The harness runs in a separate service to avoid coupling with production response path.

---

### 9.11 Result Storage

Eval results are stored in PostgreSQL using the same database as memory (but in isolated tables - see Section 10.7).

Key fields per test run (full schema in Section 10.6):

- run_id (UUID)
- test_id (references test_cases.test_id)
- run_timestamp (UTC)
- correctness_score (decimal 0-1)
- quality_score (decimal 0-10, from LLM-as-judge)
- latency_ms (p50, p95 aggregated)
- cost_tokens (int)
- pass_fail (varchar)
- judge_reasoning (text, free-form)

This enables trend analysis:
- "Has correctness improved over the last 4 weeks?"
- "Did the latest prompt change increase cost?"
- "Is quality drifting?"

---

### 9.12 Pass/Fail Criteria

Each test case has its own pass threshold defined in its YAML definition.

**System-level aggregate criteria for v1 (used as deployment gates):**

| Dimension | Threshold | Behavior on Failure |
|-----------|-----------|---------------------|
| Correctness | >= 80% of test cases pass | Block deployment |
| Quality | Average LLM-as-judge score >= 7/10 | Block deployment |
| Performance | p95 latency <= 5 minutes per audit | Block deployment |
| Cost | Average <= $0.50 per audit | Block deployment |

If aggregate criteria fail, the CI/CD pipeline blocks deployment (Section 11.8).

**Principle:** Anything measured must be a gate. The Eval Harness is not a passive dashboard - it actively blocks bad deployments.

---

## 10. Data Model

### 10.1 Purpose

The data model defines the structure of data flowing through the system across three layers:

- External Data (from AWS via MCP)
- Internal Domain Models (used by application code)
- Persisted Data (stored in PostgreSQL)

Each layer is intentionally decoupled to ensure resilience, testability, and portability.

---

### 10.2 Three-Layer Data Architecture

| Layer | Purpose | Format |
|-------|---------|--------|
| External Data | Raw data fetched from AWS via MCP | JSON (AWS API shape) |
| Internal Domain Models | Application working data | Python dataclasses / Pydantic models |
| Persisted Data | Long-term storage for memory and eval | PostgreSQL tables (strict columns + JSONB) |

**Principle:** Each layer is owned by us, except External Data which is owned by AWS. The boundary between External Data and Internal Domain Models is the **decoupling point** that protects the system from AWS API changes.

---

### 10.3 Why Decouple External Data from Internal Models

The internal domain model is mapped from AWS JSON at the MCP boundary. This separation provides:

- **API change resilience** - AWS API field renames do not break business logic
- **Coupling control** - application logic depends on our contract, not AWS's
- **Testability** - internal models can be unit tested without real AWS calls
- **Multi-cloud future** - Azure/GCP support requires only new mapping, not new business logic
- **Security control** - fields containing PII or unnecessary data can be filtered at the boundary

---

### 10.4 Core Internal Domain Models

The system operates on five core domain entities.

#### AuditRequest
- request_id (UUID)
- account_id
- session_id
- requested_at
- audit_scope (list of resource types)
- user_id

#### Resource
- resource_id
- resource_type (ec2, rds, ebs, eip)
- region
- tags (dict)
- monthly_cost (DECIMAL)
- utilization_metrics (dict)

#### Finding
- finding_id (UUID)
- resource_id
- finding_type (idle, oversized, unused, untagged)
- severity (low, medium, high)
- estimated_waste (DECIMAL)
- evidence (dict)

#### Recommendation
- recommendation_id (UUID)
- finding_id
- action (stop, resize, delete, review, tag)
- rationale (LLM-generated explanation)
- estimated_savings (DECIMAL)
- risk_level (low, medium, high)
- priority (1 = highest)
- validation_status (passed, retried, escalated)

#### AuditResult
- audit_id (UUID)
- request_id
- findings (list)
- recommendations (list)
- total_estimated_savings
- audit_duration_ms
- llm_cost_usd
- completed_at

---

### 10.5 Persisted Schema - Memory Tables

These tables support the Memory Layer defined in Section 7.

```sql
-- LTM: Audit history per account
CREATE TABLE audit_history (
    audit_id UUID PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    requested_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    findings_count INT,
    total_savings_estimated DECIMAL(12, 2),
    summary_json JSONB,
    INDEX idx_account_completed (account_id, completed_at)
);

-- Episodic: Recommendation outcomes
CREATE TABLE recommendation_log (
    recommendation_id UUID PRIMARY KEY,
    audit_id UUID REFERENCES audit_history(audit_id),
    account_id VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    action VARCHAR(50),
    estimated_savings DECIMAL(12, 2),
    user_decision VARCHAR(20),  -- accepted, rejected, pending
    decided_at TIMESTAMP,
    INDEX idx_account_decision (account_id, user_decision)
);
```

---

### 10.6 Persisted Schema - Eval Tables

These tables support the Eval Harness defined in Section 9.

```sql
-- Test case definitions (source of truth)
CREATE TABLE test_cases (
    test_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(50),
    description TEXT,
    definition_yaml TEXT,
    created_at TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Eval run results
CREATE TABLE eval_runs (
    run_id UUID PRIMARY KEY,
    test_id VARCHAR(50) REFERENCES test_cases(test_id),
    run_timestamp TIMESTAMP NOT NULL,
    correctness_score DECIMAL(4, 2),
    quality_score DECIMAL(4, 2),
    latency_ms INT,
    cost_tokens INT,
    pass_fail VARCHAR(10),
    judge_reasoning TEXT,
    INDEX idx_test_time (test_id, run_timestamp)
);
```

---

### 10.7 Production / Test Data Isolation

**Critical principle:** Production data and test data live in completely separate tables with **no foreign keys between them**.

| Table | Type | References Allowed |
|-------|------|--------------------|
| audit_history | Production | recommendation_log only |
| recommendation_log | Production | audit_history only |
| test_cases | Test | none |
| eval_runs | Test | test_cases only |

**Why:**
- Prevents test runs from polluting production tables
- Enables independent cleanup policies
- Maintains compliance boundaries
- Allows test data to be wiped without affecting production audits

---

### 10.8 Field Strategy - Strict Columns vs JSONB

The system uses a hybrid approach for schema flexibility.

| Field Type | Storage | Rationale |
|-----------|---------|-----------|
| Stable + queried often (cost, account_id, timestamps) | Strict column with index | 10-100x faster queries |
| Volatile + occasional reads (custom tags, evolving metrics) | JSONB | Schema flexibility without migrations |
| Large structured payloads (full audit summary) | JSONB | Avoids excessive column count |

**Rule:** Strict columns are stable + frequently queried. JSONB is volatile + occasionally accessed.

---

### 10.9 ID Strategy

All entity IDs use UUIDs (v4).

Reasons:
- No information leak (auto-increment reveals count to attackers)
- Works across distributed systems without coordination
- No collision risk in CI/CD parallel test runs
- Standard practice for enterprise systems

Test case IDs use human-readable strings (e.g., TC-001) for clarity in test reports.

---

### 10.10 Timestamp Strategy

All timestamps are stored in **UTC**.

User-local time conversion happens at the presentation layer only.

This prevents:
- Timezone bugs in trend analysis
- Inconsistencies across regional deployments
- Confusion in multi-region cost comparisons

---

### 10.11 Data Flow Across Layers

```text
AWS APIs
    |
    v (MCP returns raw JSON)
External Data (AWS shape)
    |
    v (mapped at MCP boundary)
Internal Domain Models (Python objects)
    |
    v (processed by Analysis, RCA, Recommendation engines)
Findings + Recommendations
    |
    v (serialized for storage)
Persisted Data (PostgreSQL)
    |
    v (retrieved for memory queries / eval analysis)
Internal Domain Models (re-hydrated)
```

Each transition between layers is an explicit transformation. Raw AWS JSON never flows directly into business logic or persistence.

---

## 11. Deployment Approach

### 11.1 Purpose

This section defines how the system is packaged, deployed, secured, monitored, and shipped to production.

It is the operational counterpart of the architecture defined in Sections 1-10.

---

### 11.2 Compute Platform

The system runs on **AWS ECS Fargate**.

| Compute Option | Decision | Rationale |
|----------------|----------|-----------|
| AWS Lambda | Rejected | 15-minute execution limit and cold starts are too close to the 2-5 minute audit duration; MCP server is long-running, unsuitable for serverless |
| ECS Fargate | Selected | No execution time limit, container-based, no server management, simpler than Kubernetes, gives container experience |
| EKS (Kubernetes) | Rejected | Over-engineered for v1 (3 services). Kubernetes is the right choice at 50+ services |

---

### 11.3 Packaging

The system is packaged as **three independent Docker images**, each mapping to a distinct architectural concern.

| Image | Contents | Architecture Section |
|-------|----------|---------------------|
| finops-agent | Orchestrator + Reasoning (LLM) + Validation Layer | Sections 3, 8 |
| mcp-server | AWS FinOps MCP Server | Section 6 |
| eval-harness | Eval orchestrator + LLM-as-judge | Section 9 |

Benefits:
- Independent deployment lifecycle per image
- Independent scaling per service
- Clear separation of concerns
- Failure isolation (eval issues do not affect production response path)

---

### 11.4 Multi-Tenant AWS Access - IAM AssumeRole Pattern

To access customer AWS accounts safely, the system uses the **AssumeRole pattern with External ID** - the AWS-standard multi-tenant access mechanism.

**Pattern:**

1. **Customer creates an IAM Role** in their AWS account
   - Role name: FinOpsAuditRole
   - Permissions: Read-only (Cost Explorer, EC2 describe, RDS describe, EBS describe, CloudWatch read)
   - Trust policy: Allows the service's AWS account to assume this role
   - External ID: Unique secret per customer (prevents confused deputy attack)

2. **Customer provides to the service:**
   - Role ARN
   - External ID

3. **At runtime, the agent assumes the role:**
   - Calls AWS STS assume_role
   - Receives temporary credentials (1-hour expiry)
   - Performs the audit with temporary credentials
   - Credentials expire automatically; no cleanup required

**Benefits:**
- No static customer credentials are ever stored
- Customer can revoke access instantly by deleting the role
- Time-limited credentials reduce blast radius
- Full AWS audit trail of every role assumption
- External ID prevents impersonation attacks
- Compliant with SOC2, GDPR, and standard enterprise patterns

**Anti-pattern (rejected):** Storing customer AWS access keys in Secrets Manager. This creates liability, breach risk, and compliance failures.

---

### 11.5 Secrets Management

| Secret Type | Storage | Rotation |
|------------|---------|----------|
| LLM API keys (Azure OpenAI, judge LLM) | AWS Secrets Manager | Manual quarterly |
| PostgreSQL connection string | AWS Secrets Manager | Auto via Secrets Manager |
| PostgreSQL password | AWS Secrets Manager (auto-rotated) | Auto every 30 days |
| Customer AWS access | IAM AssumeRole + External ID | N/A (temporary creds) |
| Application config (region, log level) | AWS Parameter Store | N/A |

**Rule:** No secrets in code, no secrets in environment variables (plaintext), no secrets in Git.

---

### 11.6 Network Topology

```text
Internet
   |
   v
API Gateway (authentication, rate limiting)
   |
   v
ECS Fargate Cluster (private subnet)
   |
   +--> finops-agent
   |       |
   |       +--> MCP Server (private VPC, internal only)
   |       +--> LLM (Azure OpenAI, via HTTPS)
   |       +--> PostgreSQL (private subnet, SG-restricted)
   |
   +--> eval-harness (separate task)
            |
            +--> finops-agent (test invocation)
            +--> PostgreSQL (eval_runs table)
```

Key decisions:
- No service is directly internet-facing except API Gateway
- MCP server is internal-only (security boundary)
- PostgreSQL is in a private subnet with security group restrictions
- Cross-account AWS access uses STS AssumeRole (no inbound network access required)

---

### 11.7 Observability - Three Pillars

The system implements logs, metrics, and traces.

| Pillar | Tool | Captures |
|--------|------|----------|
| Logs | CloudWatch Logs (structured JSON) | request_id, account_id, errors, latency per stage |
| Metrics | CloudWatch Metrics | requests/min, error rate, p50/p95 latency, token usage, cost per audit |
| Traces | LangSmith + AWS X-Ray | LLM call traces (prompts, completions, tokens, cost) and cross-component spans |

**Why LangSmith specifically:**
- LLM-specific observability (token usage, prompts, completions per call)
- Trace visualization for multi-agent flows
- Integrates cleanly with CloudWatch for full-stack view

**Alarms:**
- Error rate > 5% over 5 minutes
- p95 latency > 5 minutes
- Cost per audit > $0.50
- Eval batch failure (correctness < 80%)

---

### 11.8 CI/CD Pipeline

The deployment pipeline enforces quality gates at every stage.

```text
Git push to main
   |
   v
GitHub Actions (or Azure DevOps)
   |
   v
1. Lint (ruff)                       --> blocks on style errors
   |
   v
2. Unit tests (pytest)               --> blocks on code bugs
   |
   v
3. Build Docker images               --> blocks on build failure
   |
   v
4. Push images to ECR
   |
   v
5. Eval Harness smoke run            --> blocks if correctness < 80%,
   (subset of test cases)               quality < 7/10, or cost > $0.50/audit
   |
   v
6. Deploy to staging (ECS Fargate)
   |
   v
7. Full Eval Harness run on staging  --> blocks if regression detected
   |
   v
8. Manual approval gate (production)
   |
   v
9. Deploy to production
```

**Critical principle:** Anything measured must be a gate. The Eval Harness is not a passive dashboard - it actively blocks bad deployments.

---

### 11.9 Environment Strategy

| Environment | Purpose | Data |
|-------------|---------|------|
| Local (dev) | Developer machines | Synthetic test data only |
| CI | Eval Harness smoke runs | Synthetic test data only |
| Staging | Pre-production validation | Synthetic + sandbox AWS account |
| Production | Customer-facing | Real customer accounts via AssumeRole |

**Rule:** Production data never flows to lower environments. Test data never pollutes production tables (see Section 10.7).

---

### 11.10 Cost Optimization (FinOps for the FinOps Agent)

The system that audits cloud cost must itself be cost-efficient.

| Cost Lever | Approach |
|-----------|----------|
| LLM cost | Use cheaper model (Haiku / GPT-4.1-mini) for routing; reserve premium model for reasoning |
| Compute | Fargate Spot for non-critical eval workloads |
| Storage | PostgreSQL right-sized for v1; reserved instances after v1 traffic baseline |
| Data transfer | Keep MCP server and agent in same VPC (no cross-AZ for v1) |
| Eval frequency | Batch nightly + on every PR (not continuous) |

Target: Total operating cost <= projected monthly budget defined in NFR-02.

---

### 11.11 Rollback Strategy

| Failure Type | Rollback Mechanism |
|-------------|---------------------|
| Bad code deploy | ECS service rolling back to previous task definition |
| Schema migration failure | All migrations are backward-compatible; old code reads new schema |
| LLM provider outage | Fallback to secondary model family (e.g., Azure OpenAI -> Anthropic) |
| MCP server failure | Direct boto3 fallback path for critical tools (degraded mode) |

Rollbacks are automated where possible. Manual rollback playbook is documented in operations runbook (separate document).

---

### 11.12 What Is NOT in v1 (Deferred to v2)

To prevent scope creep:

- Kubernetes (EKS) - only if scale demands it
- Multi-region deployment - v1 is single-region
- Real-time monitoring dashboard (Grafana, Datadog) - CloudWatch is sufficient for v1
- Blue/green deployments - rolling updates are adequate for v1
- Customer-facing web portal - API only for v1
- Semantic Memory (Section 7.2)
- Async eval monitoring (Section 9.8)

---

## End of Design Document

**Next Phase:** tasks.md - Ordered implementation plan based on this design.

**Design completion checklist:**
- [x] Architecture approach defined
- [x] All major components specified
- [x] MCP boundaries decided
- [x] Memory architecture isolated per tenant
- [x] Validation layer with safety rules
- [x] Eval harness with 4 dimensions + deployment gates
- [x] Data model with prod/test isolation
- [x] Deployment with AssumeRole + CI/CD gates
