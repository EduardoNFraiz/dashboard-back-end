# AI Constitution - The Band Project

This document defines the fundamental rules and standards that any AI Agent working on this project must follow.

## 1. Architectural Rules (Senior Designer)

### 1.1 Django & Extraction Architecture
- **Models Layer**: Standard Django models in `apps/<app_name>/models.py`.
- **Extraction Layer**: Specialized handlers in `apps/core/extract_<source>/`.
- **API Layer**: Django Rest Framework (DRF) in `apps/<app_name>/api/`.
- **Services**: Business logic decoupled from models when complexity grows.

### 1.2 Design Patterns
- **Strategy Pattern (MANDATORY)**: Apply the Strategy Pattern when multiple algorithms or behaviors are required for a specific task (e.g., different extraction methods, different data normalization rules).
- **Dependency Injection**: Always inject extraction strategies via constructors.

### 1.3 Data Integrity & Idempotency
- **Idempotency**: All extraction pipelines must be idempotent. Use "get_or_create" or similar logic to prevent duplicates.
- **Relational Integrity**: Maintain strict foreign key relationships and ontological consistency.

---

## 2. Testing Rules (Senior QA)

### 2.1 Test-Driven Development (TDD)
- **MANDATORY**: Implement test cases defined in the `implementation_plan.md` **BEFORE** the implementation code.
- **Coverage**: Every new feature, logic branch, or bugfix must have corresponding tests using Django's testing framework or pytest.

### 2.2 Testing Framework & Patterns
- **Pytest/Django Test**: Use `pytest-django` or standard `django.test`.
- **Mocking**: Use `unittest.mock` to isolate external API calls (e.g., GitHub API).
- **No Side Effects**: Tests must NEVER reach out to real external services or production databases.
- **AAA Pattern**: Follow the Arrange-Act-Assert pattern for clarity.
- **Cleanup**: Ensure temporary test states are handled by the test runner.

---

## 3. Process & Quality Standards (Senior PM)

### 3.1 Agile & Project Management
- **@agile-standards**: Follow the `.agent/workflows/agile-standards.md` workflow strictly.
- **Documentation First**: Update documentation in `docs/` before implementing any feature.
- **Issue Tracking (MANDATORY)**: Every task must be preceded by a GitHub Issue. No code should be written without a corresponding Issue ID in a feature branch.

### 3.2 Code Quality
- **Type Hinting**: All Python functions must have full type annotations.
- **Docstrings**: Use Google-style docstrings for all modules, classes, and functions.
- **Linting**: Ensure code passes `black`, `flake8`, and `isort`.
- **Observability (MANDATORY)**: All critical actions and state changes MUST be logged (Info/Error) with appropriate context.

### 3.3 GitHub Interaction
- **MCP Usage**: Use `github-mcp-server` for all remote operations (PRs, Issues, Releases, Branches).
- **GitFlow**: Follow the `main` -> `developing` -> `feature/fix` branching strategy.

---

## 4. Proactiveness & Communication

- **Question Decisions**: If a requirement is ambiguous or if a design violates these rules, the AI must question the user.
- **Technical Proposals**: Always provide a technical plan in `implementation_plan.md` and wait for approval before coding.
- **Walkthroughs**: After completing a task, provide a `walkthrough.md` with proof of work, including test results and (if applicable) screenshots/recordings.
