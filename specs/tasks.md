# Cloud FinOps & Cost Optimization Agent - Implementation Tasks

**Project:** Spec-Driven Architect Assistant
**Author:** Sanjay Thakur
**SDD Phase:** Tasks (Phase 3)
**Status:** Active

---

## How to Use This Document

- Each task is **atomic and completable in one sitting** (max 3 hours)
- Cadence is **irregular** - pick tasks based on your available slot
- Follow the order strictly (later tasks depend on earlier)
- Do NOT start a task you cannot finish in the current sitting
- Mark tasks Done only when the Definition of Done is met
- Commit after every completed task

---

## Task Size Guide

| Size | Time | Meaning |
|------|------|---------|
| XS | < 1 hour | Trivial config, one-line change |
| S | 1-2 hours | Small self-contained feature |
| M | 2-3 hours | Medium - must fit one sitting |
| L | Split required | Break into smaller tasks |

---

## Task Streams

| Stream | Prefix | Goal |
|--------|--------|------|
| A. Foundation | T-A-* | Project setup, structure, tooling |
| B. MCP Server | T-B-* | AWS FinOps MCP server |
| C. Core Orchestrator | T-C-* | Main agent flow + LLM integration |
| D. Validation Layer | T-D-* | Rule-based guardrails |
| E. Memory Layer | T-E-* | STM / LTM / Episodic |
| F. Eval Harness | T-F-* | Test infrastructure + CI/CD gates |

---

## Milestones Overview

| Milestone | Description | Tasks |
|-----------|-------------|-------|
| M1: Vertical Slice v0.1 | End-to-end synthetic audit | T-A-01 to T-C-03 |
| M2: Real AWS Integration | AssumeRole + Cost Explorer | T-B-03 to T-B-10 |
| M3: Memory + Full Validation | Full memory + all 4 validation checks | T-D-02 to T-E-06 |
| M4: Eval Harness | Test cases + LLM-as-judge + CI/CD gates | T-F-01 to T-F-08 |
| M5: Production Hardening | Docker, PostgreSQL, observability | T-A-05 to T-A-12 |
| M6: Polish + Retrospective | LinkedIn post + SDD retrospective | T-A-13 to T-A-15 |

**Total tasks:** ~50 across 6 milestones
**Estimated total effort:** 60-80 hours (irregular sittings)

---

# MILESTONE 1: Vertical Slice v0.1

**Goal:** Working end-to-end audit against synthetic data. Demonstrates the full architecture path.

**Definition of Done for M1:**
- CLI accepts an account_id and returns recommendations
- MCP server exposes at least one working tool
- Orchestrator routes request through MCP + LLM + Validation
- Existence validation blocks hallucinated resource IDs
- Console output shows: findings + recommendations + savings estimates

**Estimated effort:** 8-12 hours

---

### T-A-01: Initialize Python project structure
- **Size:** XS
- **Design ref:** N/A (foundation)
- **Depends on:** None
- **Steps:**
  1. Create Python virtual env at `C:\\AI\\spec-driven-architect-assistant\\.venv`
  2. Create `src/finops_agent/` package
  3. Create `src/mcp_server/` package
  4. Create `src/eval_harness/` package
  5. Create `tests/` folder
  6. Create `pyproject.toml` with project metadata
  7. Add `.gitignore` (venv, __pycache__, .env, *.pyc)
- **Definition of Done:**
  - `python -c "import finops_agent"` runs without error
  - `git status` shows no venv or __pycache__ tracked

---

### T-A-02: Add core dependencies
- **Size:** XS
- **Design ref:** Section 2 (Architecture)
- **Depends on:** T-A-01
- **Steps:**
  1. Add runtime dependencies to `pyproject.toml`:
     - `pydantic`
     - `openai` or `anthropic`
     - `python-dotenv`
     - `click` or `typer`
  2. Add dev dependencies:
     - `pytest`
     - `ruff`
     - `pytest-cov`
  3. Install: `pip install -e ".[dev]"`
- **Definition of Done:**
  - `pytest --version` works
  - `ruff --version` works
  - LLM client library importable

---

### T-A-03: Create synthetic AWS account data file
- **Size:** S
- **Design ref:** Section 10.4 (Domain Models)
- **Depends on:** T-A-02
- **Steps:**
  1. Create `tests/fixtures/synthetic_account_001.json`
  2. Include 3 EC2 instances:
     - i-fake-001: idle (cpu_avg_14d: 2.5, cost: $50/month)
     - i-fake-002: idle (cpu_avg_14d: 3.1, cost: $30/month)
     - i-fake-003: active (cpu_avg_14d: 65.0, cost: $80/month)
  3. Format matches internal Resource domain model (Section 10.4)
- **Definition of Done:**
  - JSON file loads with `json.load()` without errors
  - 3 resources present with all required fields

---

### T-A-04: Define core domain models (Pydantic)
- **Size:** M
- **Design ref:** Section 10.4
- **Depends on:** T-A-02
- **Steps:**
  1. Create `src/finops_agent/models.py`
  2. Define Pydantic models: AuditRequest, Resource, Finding, Recommendation, AuditResult
  3. Match field names and types from design Section 10.4
  4. Add basic validators (e.g., cost >= 0)
- **Definition of Done:**
  - All 5 models importable
  - `Resource.model_validate(json_data)` works for synthetic data
  - Unit test in `tests/test_models.py` passes

---

### T-B-01: MCP server skeleton
- **Size:** S
- **Design ref:** Section 6.3
- **Depends on:** T-A-01, T-A-02
- **Steps:**
  1. Create `src/mcp_server/server.py`
  2. Set up basic MCP server structure (use official MCP Python SDK or simple JSON-RPC stub)
  3. Register empty tool list
  4. Server runs on localhost:8080
- **Definition of Done:**
  - `python -m mcp_server.server` starts without error
  - Server responds to a health check endpoint
  - No tools registered yet (next task)

---

### T-B-02: Implement first MCP tool - list_idle_ec2
- **Size:** M
- **Design ref:** Section 6.3 (tool list)
- **Depends on:** T-A-03, T-B-01
- **Steps:**
  1. Create `src/mcp_server/tools/list_idle_ec2.py`
  2. Tool signature: `list_idle_ec2(account_id: str) -> list[Resource]`
  3. For v0.1: reads from synthetic JSON fixture
  4. Filter: cpu_avg_14d < 5.0
  5. Register tool in MCP server
- **Definition of Done:**
  - MCP server exposes `list_idle_ec2` tool
  - Calling with `account_id="synthetic-001"` returns 2 idle resources
  - Response conforms to Resource model

---

### T-C-01: LLM client setup
- **Size:** S
- **Design ref:** Section 4.5, 4.6
- **Depends on:** T-A-02
- **Steps:**
  1. Create `src/finops_agent/llm_client.py`
  2. Read API key from `.env`
  3. Wrap LLM call: `generate_recommendation(idle_resources: list[Resource]) -> str`
  4. Use cheap model for M1 (GPT-4.1-mini or Claude Haiku)
- **Definition of Done:**
  - Function returns non-empty string for real LLM call
  - `.env` is git-ignored
  - Manual test: call with 2 idle resources returns a recommendation

---

### T-C-02: Orchestrator skeleton
- **Size:** M
- **Design ref:** Section 4.1, Section 5
- **Depends on:** T-B-02, T-C-01, T-A-04
- **Steps:**
  1. Create `src/finops_agent/orchestrator.py`
  2. Define `run_audit(account_id: str) -> AuditResult`
  3. Flow: Call MCP tool -> Pass to LLM -> Wrap in Recommendation -> Return AuditResult
  4. No validation yet (next task)
  5. No memory yet
- **Definition of Done:**
  - `run_audit("synthetic-001")` returns valid AuditResult
  - Result contains at least 1 recommendation
  - No hardcoded strings - flow is real

---

### T-D-01: Existence validation check (inline)
- **Size:** S
- **Design ref:** Section 8.3 (Existence Check)
- **Depends on:** T-C-02
- **Steps:**
  1. Create `src/finops_agent/validation/existence_check.py`
  2. Function: `validate_existence(recommendations, known_resource_ids) -> (passed, rejected)`
  3. Wire into orchestrator AFTER LLM, BEFORE returning result
- **Definition of Done:**
  - If LLM references a fake resource_id, it is rejected
  - Only validated recommendations reach final response
  - Unit test: pass known + unknown IDs, verify filtering

---

### T-C-03: CLI entry point (M1 DEMO)
- **Size:** S
- **Design ref:** Section 5
- **Depends on:** T-C-02, T-D-01
- **Steps:**
  1. Create `src/finops_agent/cli.py`
  2. Use `click` or `typer`
  3. Command: `python -m finops_agent.cli --account synthetic-001`
  4. Print formatted output with findings, recommendations, savings
- **Definition of Done:**
  - THIS IS THE MILESTONE 1 DEMO COMMAND
  - CLI runs end-to-end without errors
  - Output shows real recommendations from real LLM call
  - Existence validation applied

---

## Milestone 1 Complete Criteria

- [ ] T-A-01 through T-C-03 marked done
- [ ] `python -m finops_agent.cli --account synthetic-001` produces valid output
- [ ] At least one hallucinated recommendation is caught by existence validation
- [ ] All unit tests pass
- [ ] Code committed to git with clean commit history

---

# MILESTONE 2: Real AWS Integration

**Goal:** Replace synthetic data with real AWS API calls via AssumeRole pattern.

**Definition of Done for M2:**
- MCP tools call real AWS Cost Explorer and EC2 APIs
- AssumeRole pattern with External ID implemented
- Read-only IAM role documented
- Multiple resource types supported (EC2, RDS, EBS)

**Estimated effort:** 10-15 hours

---

### T-B-03: Add boto3 dependency and AWS credentials handling
- **Size:** S
- **Design ref:** Section 11.4 (AssumeRole)
- **Depends on:** T-B-02
- **Steps:**
  1. Add `boto3` to dependencies
  2. Create `src/mcp_server/aws_client.py`
  3. Read AWS credentials from `.env` (your own account for testing)
  4. Add function `get_boto3_session()` returning boto3 Session
- **Definition of Done:**
  - `boto3.client("sts").get_caller_identity()` returns your account
  - Credentials never logged

---

### T-B-04: Implement AssumeRole with External ID
- **Size:** M
- **Design ref:** Section 11.4
- **Depends on:** T-B-03
- **Steps:**
  1. Create `src/mcp_server/assume_role.py`
  2. Function: `assume_customer_role(role_arn: str, external_id: str) -> Session`
  3. Uses STS.assume_role with 1-hour duration
  4. Returns short-lived boto3 Session
  5. Add unit test with mocked STS
- **Definition of Done:**
  - Function returns valid temporary credentials
  - Test AssumeRole against a role in your own account (self-assume)
  - Documentation: how to create the role (in comments)

---

### T-B-05: Real list_idle_ec2 using EC2 + CloudWatch
- **Size:** M
- **Design ref:** Section 6.3
- **Depends on:** T-B-04
- **Steps:**
  1. Update `list_idle_ec2` tool to use real APIs
  2. Call EC2 DescribeInstances to get inventory
  3. Call CloudWatch GetMetricStatistics for CPU average (14 days)
  4. Filter: cpu_avg_14d < 5.0
  5. Keep synthetic fallback via env flag `USE_SYNTHETIC_DATA=true`
- **Definition of Done:**
  - Tool works against real AWS account
  - Returns actual idle instances (or empty list if none)
  - Env flag toggles between real and synthetic

---

### T-B-06: Implement get_cost_by_service tool
- **Size:** M
- **Design ref:** Section 6.3
- **Depends on:** T-B-04
- **Steps:**
  1. Create `src/mcp_server/tools/get_cost_by_service.py`
  2. Uses AWS Cost Explorer GetCostAndUsage
  3. Returns top 5 services by spend for last 30 days
  4. Register with MCP server
- **Definition of Done:**
  - Tool returns real cost data
  - Top 5 services correctly identified and sorted

---

### T-B-07: Implement list_unattached_ebs tool
- **Size:** S
- **Design ref:** Section 6.3
- **Depends on:** T-B-04
- **Steps:**
  1. Create tool: `list_unattached_ebs(account_id: str)`
  2. Uses EC2 DescribeVolumes with filter State=available
  3. Register with MCP server
- **Definition of Done:**
  - Tool returns unattached EBS volumes
  - Cost estimate included

---

### T-B-08: Implement list_oversized_rds tool
- **Size:** M
- **Design ref:** Section 6.3
- **Depends on:** T-B-04
- **Steps:**
  1. Create tool: `list_oversized_rds(account_id: str)`
  2. Uses RDS DescribeDBInstances + CloudWatch CPU avg
  3. Filter: cpu_avg_14d < 20
  4. Register with MCP server
- **Definition of Done:**
  - Tool returns underutilized RDS instances
  - Downsize suggestion included (t3.large -> t3.medium etc.)

---

### T-B-09: Implement list_unused_elastic_ips tool
- **Size:** XS
- **Design ref:** Section 6.3
- **Depends on:** T-B-04
- **Steps:**
  1. Create tool: `list_unused_elastic_ips(account_id: str)`
  2. Uses EC2 DescribeAddresses, filter unattached
- **Definition of Done:**
  - Returns unused EIPs with cost impact

---

### T-B-10: Wire all real tools into orchestrator
- **Size:** M
- **Design ref:** Section 5
- **Depends on:** T-B-05, T-B-06, T-B-07, T-B-08, T-B-09
- **Steps:**
  1. Update orchestrator to call all 5 tools
  2. Aggregate findings across resource types
  3. Pass complete inventory to LLM
- **Definition of Done:**
  - CLI now returns findings across EC2, RDS, EBS, EIPs
  - Cost breakdown by service included in output

---

## Milestone 2 Complete Criteria

- [ ] All 5 MCP tools use real AWS APIs
- [ ] AssumeRole pattern works with External ID
- [ ] Env flag allows synthetic fallback for testing
- [ ] CLI runs against real AWS account and returns real findings

---

# MILESTONE 3: Memory + Full Validation

**Goal:** Add all memory tiers and complete the validation layer with all 4 checks.

**Definition of Done for M3:**
- STM, LTM, Episodic memory all functional
- All 4 validation checks operational
- Retry/Remove/Escalate outcomes implemented
- Multi-tenant isolation verified

**Estimated effort:** 12-18 hours

---

### T-D-02: Action Whitelist validation check
- **Size:** S
- **Design ref:** Section 8.3
- **Depends on:** T-D-01
- **Steps:**
  1. Create `src/finops_agent/validation/action_whitelist.py`
  2. Allowed actions: stop, resize, tag, review, delete_unattached
  3. Reject if action not in whitelist
  4. Wire into orchestrator
- **Definition of Done:**
  - LLM output with disallowed action (e.g., "terminate production") is rejected
  - Unit test covers positive and negative cases

---

### T-D-03: Logical Consistency validation check
- **Size:** M
- **Design ref:** Section 8.3
- **Depends on:** T-D-01
- **Steps:**
  1. Create `src/finops_agent/validation/logical_consistency.py`
  2. Rules:
     - Low CPU + "resize down" = consistent
     - Low CPU + "resize up" = inconsistent
     - Idle + "stop" = consistent
     - Idle + "keep running" = inconsistent
  3. Wire into orchestrator
- **Definition of Done:**
  - Contradictory recommendations are caught
  - Unit tests cover common consistency cases

---

### T-D-04: Numeric Sanity validation check
- **Size:** S
- **Design ref:** Section 8.3
- **Depends on:** T-D-01
- **Steps:**
  1. Create `src/finops_agent/validation/numeric_sanity.py`
  2. Rule: estimated_savings <= resource.monthly_cost
  3. Rule: savings > 0
  4. Wire into orchestrator
- **Definition of Done:**
  - Recommendations claiming impossible savings are flagged

---

### T-D-05: Validation outcomes - Retry/Remove/Escalate
- **Size:** M
- **Design ref:** Section 8.4
- **Depends on:** T-D-02, T-D-03, T-D-04
- **Steps:**
  1. Create `src/finops_agent/validation/outcomes.py`
  2. Retry logic: max 2 attempts with augmented context
  3. Remove logic: drop single failing item, keep rest
  4. Escalate logic: surface warning to user output
  5. Wire all validation checks through outcome system
- **Definition of Done:**
  - Retry triggers on hallucinated IDs (max 2 attempts)
  - Remove drops single bad items
  - Escalate surfaces safety violations visibly

---

### T-D-06: Safety rules - hard constraints
- **Size:** S
- **Design ref:** Section 8.5
- **Depends on:** T-D-05
- **Steps:**
  1. Implement hard constraints:
     - No delete on production-tagged resources
     - No IAM/security config modifications
     - No cross-account operations
     - Impact threshold check (>$10K/month = escalate)
- **Definition of Done:**
  - Attempting a production-tag deletion triggers Escalate
  - User sees clear warning in output

---

### T-E-01: Short-Term Memory (STM) in-memory implementation
- **Size:** S
- **Design ref:** Section 7.3, 7.4
- **Depends on:** T-C-02
- **Steps:**
  1. Create `src/finops_agent/memory/stm.py`
  2. Class `ShortTermMemory` keyed by (session_id, account_id)
  3. Store: current audit context, in-flight recommendations
  4. Method `reset()` on context switch
- **Definition of Done:**
  - STM initializes on audit start
  - STM clears when account_id changes
  - Unit test verifies isolation across accounts

---

### T-E-02: PostgreSQL setup + migration tooling
- **Size:** M
- **Design ref:** Section 7.4, Section 10.5
- **Depends on:** T-A-02
- **Steps:**
  1. Add `psycopg` or `sqlalchemy` to dependencies
  2. Create Docker Compose for local PostgreSQL
  3. Set up migration tool (Alembic recommended)
  4. Create initial migration for audit_history and recommendation_log tables
- **Definition of Done:**
  - Local PostgreSQL running via Docker Compose
  - `alembic upgrade head` creates all tables
  - Connection tested from Python

---

### T-E-03: Long-Term Memory (LTM) - audit_history table access
- **Size:** M
- **Design ref:** Section 7.3, Section 10.5
- **Depends on:** T-E-02
- **Steps:**
  1. Create `src/finops_agent/memory/ltm.py`
  2. Methods: `store_audit(audit_result)`, `get_previous_audits(account_id, limit)`
  3. Always filter by account_id
  4. Store summary as JSONB
- **Definition of Done:**
  - Audit results persist across CLI runs
  - Retrieval only returns records for the queried account_id

---

### T-E-04: Episodic Memory - recommendation_log
- **Size:** M
- **Design ref:** Section 7.3
- **Depends on:** T-E-02
- **Steps:**
  1. Create `src/finops_agent/memory/episodic.py`
  2. Methods: `log_recommendation(rec, decision)`, `get_history(account_id)`
  3. Filter by account_id
- **Definition of Done:**
  - Every recommendation logged with pending status
  - CLI supports marking a recommendation as accepted/rejected

---

### T-E-05: Wire memory into orchestrator
- **Size:** M
- **Design ref:** Section 5 (flow)
- **Depends on:** T-E-01, T-E-03, T-E-04
- **Steps:**
  1. Update orchestrator flow:
     - Initialize STM at start
     - Lookup LTM for prior audits
     - Write LTM after audit completes
     - Log each recommendation to Episodic
  2. Include prior audit context in LLM prompt
- **Definition of Done:**
  - Second audit run against same account references prior findings
  - CLI output shows "Compared to last audit N days ago" line

---

### T-E-06: Multi-tenant safety verification test
- **Size:** S
- **Design ref:** Section 7.7
- **Depends on:** T-E-05
- **Steps:**
  1. Write integration test:
     - Run audit for Account A
     - Switch to Account B in same session
     - Verify STM cleared
     - Verify Account A LTM not returned for B
- **Definition of Done:**
  - Test passes
  - No cross-account data leakage

---

## Milestone 3 Complete Criteria

- [ ] All 4 validation checks operational
- [ ] Retry/Remove/Escalate outcomes work
- [ ] STM resets on context switch
- [ ] LTM persists across runs
- [ ] Episodic logs recommendation outcomes
- [ ] Multi-tenant isolation test passes

---

# MILESTONE 4: Eval Harness

**Goal:** Build the evaluation system that gates deployment.

**Definition of Done for M4:**
- Test cases defined in YAML
- Deterministic + LLM-as-judge scoring implemented
- Results stored in eval_runs table
- Pass/fail criteria enforced in CI

**Estimated effort:** 10-15 hours

---

### T-F-01: Eval harness project structure
- **Size:** XS
- **Design ref:** Section 9.10
- **Depends on:** T-A-01
- **Steps:**
  1. Create `src/eval_harness/runner.py`
  2. Create `tests/eval_cases/` directory for YAML test cases
  3. Create eval_runs migration in Alembic
- **Definition of Done:**
  - Skeleton structure created
  - eval_runs and test_cases tables exist

---

### T-F-02: Define YAML test case format + first 3 cases
- **Size:** M
- **Design ref:** Section 9.9
- **Depends on:** T-F-01
- **Steps:**
  1. Create `tests/eval_cases/TC-001-happy-path.yaml`
  2. Create `tests/eval_cases/TC-002-empty-account.yaml`
  3. Create `tests/eval_cases/TC-003-hallucination-catch.yaml`
  4. Each follows the format from design Section 9.9
- **Definition of Done:**
  - 3 YAML files parse correctly
  - Loader tested with pytest

---

### T-F-03: Deterministic scoring implementation
- **Size:** M
- **Design ref:** Section 9.6
- **Depends on:** T-F-02
- **Steps:**
  1. Create `src/eval_harness/scoring/deterministic.py`
  2. Implement: `score_correctness(expected, actual) -> float`
  3. Rules: count matches, threshold comparison, existence check
- **Definition of Done:**
  - Score in range [0.0, 1.0]
  - Test cases pass expected scores

---

### T-F-04: LLM-as-judge scoring
- **Size:** M
- **Design ref:** Section 9.7
- **Depends on:** T-F-02
- **Steps:**
  1. Create `src/eval_harness/scoring/llm_judge.py`
  2. Use different model than agent (e.g., agent=Claude, judge=GPT-4.1)
  3. Prompt: "Score this RCA explanation 1-10 for accuracy and clarity"
  4. Return structured score + reasoning
- **Definition of Done:**
  - Judge returns 1-10 score with reasoning
  - Different model family from agent

---

### T-F-05: Heuristic scoring for recommendation completeness
- **Size:** S
- **Design ref:** Section 9.6
- **Depends on:** T-F-02
- **Steps:**
  1. Create `src/eval_harness/scoring/heuristic.py`
  2. Check each recommendation has: action, savings, risk, priority
  3. Score = fraction of complete recommendations
- **Definition of Done:**
  - Returns fraction 0.0-1.0
  - Missing fields correctly identified

---

### T-F-06: Eval runner orchestration
- **Size:** M
- **Design ref:** Section 9.10
- **Depends on:** T-F-03, T-F-04, T-F-05
- **Steps:**
  1. Runner loads YAML test cases
  2. For each: runs agent against synthetic input
  3. Applies all 3 scoring methods
  4. Measures latency + token cost
  5. Writes to eval_runs table
- **Definition of Done:**
  - `python -m eval_harness.runner` runs all test cases
  - Results appear in eval_runs table
  - Summary printed with pass/fail count

---

### T-F-07: Pass/fail aggregate criteria + report
- **Size:** S
- **Design ref:** Section 9.12
- **Depends on:** T-F-06
- **Steps:**
  1. Aggregate thresholds:
     - Correctness >= 80%
     - Quality avg >= 7/10
     - p95 latency <= 5 min
     - Avg cost <= $0.50/audit
  2. Print pass/fail report
  3. Exit code 0 (pass) or 1 (fail)
- **Definition of Done:**
  - Runner exits with non-zero on threshold failure
  - Report clearly shows which metric failed

---

### T-F-08: CI/CD integration (GitHub Actions)
- **Size:** M
- **Design ref:** Section 11.8
- **Depends on:** T-F-07
- **Steps:**
  1. Create `.github/workflows/eval.yaml`
  2. Steps: install -> lint -> unit tests -> eval runner
  3. Eval failure blocks merge
- **Definition of Done:**
  - CI runs on every PR
  - Failing eval blocks merge to main

---

## Milestone 4 Complete Criteria

- [ ] 3+ YAML test cases defined
- [ ] All 3 scoring methods work
- [ ] Eval runner produces reports
- [ ] CI blocks deployment on eval failure

---

# MILESTONE 5: Production Hardening

**Goal:** Package, deploy, and monitor the system.

**Definition of Done for M5:**
- 3 Docker images built and pushed to ECR
- ECS Fargate deployment configured
- CloudWatch logs, metrics, alarms in place
- LangSmith traces enabled
- Rollback strategy tested

**Estimated effort:** 12-18 hours

---

### T-A-05: Dockerize finops-agent
- **Size:** M
- **Design ref:** Section 11.3
- **Depends on:** T-E-05
- **Steps:**
  1. Create `docker/finops-agent.Dockerfile`
  2. Multi-stage build (build stage + slim runtime)
  3. Non-root user
  4. Health check endpoint
- **Definition of Done:**
  - Image builds without errors
  - `docker run` starts agent successfully

---

### T-A-06: Dockerize mcp-server
- **Size:** S
- **Design ref:** Section 11.3
- **Depends on:** T-B-10
- **Steps:**
  1. Create `docker/mcp-server.Dockerfile`
  2. Similar structure to finops-agent
- **Definition of Done:**
  - MCP server image builds and runs
  - Tools accessible via network

---

### T-A-07: Dockerize eval-harness
- **Size:** S
- **Design ref:** Section 11.3
- **Depends on:** T-F-08
- **Steps:**
  1. Create `docker/eval-harness.Dockerfile`
- **Definition of Done:**
  - Image builds, eval runner executes in container

---

### T-A-08: Docker Compose for local dev
- **Size:** S
- **Design ref:** Section 11.6
- **Depends on:** T-A-05, T-A-06, T-A-07, T-E-02
- **Steps:**
  1. Create `docker-compose.yml` with:
     - finops-agent
     - mcp-server
     - postgres
     - eval-harness (profile: eval)
  2. Networking: private network
- **Definition of Done:**
  - `docker compose up` starts full stack locally
  - Agent talks to MCP server and Postgres

---

### T-A-09: AWS ECR + ECS Fargate infrastructure (Terraform)
- **Size:** M
- **Design ref:** Section 11.2, 11.6
- **Depends on:** T-A-08
- **Steps:**
  1. Create `infra/terraform/` folder
  2. Modules: VPC, ECR repos, ECS cluster, task definitions, ALB
  3. Reference Terraform MCP module patterns if available
- **Definition of Done:**
  - `terraform plan` produces expected resources
  - Do not apply until reviewed (safety)

---

### T-A-10: Secrets management via AWS Secrets Manager
- **Size:** S
- **Design ref:** Section 11.5
- **Depends on:** T-A-09
- **Steps:**
  1. Create secrets:
     - LLM API keys
     - Postgres credentials
  2. IAM policies for ECS task roles
- **Definition of Done:**
  - Container reads secrets at runtime
  - No secrets in image or env

---

### T-A-11: CloudWatch logs + metrics + alarms
- **Size:** M
- **Design ref:** Section 11.7
- **Depends on:** T-A-09
- **Steps:**
  1. Structured JSON logging in Python code
  2. Custom metrics for tokens/cost per audit
  3. Alarms:
     - Error rate > 5% over 5 min
     - p95 latency > 5 min
     - Cost/audit > $0.50
- **Definition of Done:**
  - Logs streaming to CloudWatch
  - At least 3 alarms configured
  - Test alarm fires when threshold breached

---

### T-A-12: LangSmith trace integration
- **Size:** S
- **Design ref:** Section 11.7
- **Depends on:** T-C-01
- **Steps:**
  1. Add LangSmith SDK
  2. Wrap LLM calls with tracing decorators
  3. Include prompt, completion, tokens, cost per call
- **Definition of Done:**
  - Traces visible in LangSmith UI
  - Multi-agent flow visualization works

---

## Milestone 5 Complete Criteria

- [ ] All 3 Docker images build cleanly
- [ ] Local docker-compose stack works
- [ ] Terraform plan is reviewable
- [ ] Secrets managed via Secrets Manager
- [ ] CloudWatch alarms in place
- [ ] LangSmith tracing active

---

# MILESTONE 6: Polish + Retrospective

**Goal:** Turn the project into a portfolio artifact.

**Definition of Done for M6:**
- README explains the project end-to-end
- Architecture diagrams generated
- SDD retrospective written
- LinkedIn post published
- Portfolio-ready state

**Estimated effort:** 6-10 hours

---

### T-A-13: Write project README
- **Size:** M
- **Design ref:** All sections
- **Depends on:** M5 complete
- **Steps:**
  1. Sections: Overview, Architecture, Getting Started, SDD approach, Results
  2. Include 1-2 architecture diagrams (from design.md)
  3. Screenshots/GIF of CLI in action
- **Definition of Done:**
  - README readable in under 5 minutes
  - Anyone can clone + run basic demo from README alone

---

### T-A-14: SDD retrospective document
- **Size:** M
- **Design ref:** SDD methodology
- **Depends on:** M5 complete
- **Steps:**
  1. Create `docs/SDD_RETROSPECTIVE.md`
  2. Sections:
     - What worked
     - What SDD caught that vibe-coding would have missed
     - Where SDD felt slow but paid off
     - What I would do differently
- **Definition of Done:**
  - Document is honest, specific, and useful for others learning SDD

---

### T-A-15: LinkedIn post + portfolio update
- **Size:** S
- **Design ref:** N/A
- **Depends on:** T-A-13, T-A-14
- **Steps:**
  1. Draft LinkedIn post:
     - Problem statement
     - Architecture highlights (MCP, Memory, Eval Harness)
     - Key SDD learnings
     - Link to GitHub repo
  2. Add project to personal portfolio/website
- **Definition of Done:**
  - Post published
  - Portfolio updated
  - Repo public and clean

---

## Milestone 6 Complete Criteria

- [ ] README complete and demo-able
- [ ] SDD retrospective published
- [ ] LinkedIn post live
- [ ] Portfolio updated
- [ ] Project 6 officially DONE

---

# Final Project 6 Definition of Done

Project 6 is complete when:
- [ ] All 6 milestones complete
- [ ] All acceptance criteria from requirements.md met
- [ ] Design decisions from design.md implemented
- [ ] Eval harness gates every deployment
- [ ] LinkedIn post + retrospective published
- [ ] You can defend every architectural decision in an interview

---

# Ready for AWS Bedrock port (Post-Project 6)

After Project 6 is done, next project = Port to AWS Bedrock AgentCore.
That work will follow the same SDD discipline: requirements.md -> design.md -> tasks.md -> code.
