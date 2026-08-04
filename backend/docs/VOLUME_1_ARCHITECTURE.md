# Volume 1 Architecture & Infrastructure Specification

## 1. Overview
Volume 1 establishes the foundational Clean Architecture, production multi-database engine (PostgreSQL + MongoDB), security cryptography vault, and Docker Compose orchestration for SocialPilot.

## 2. Multi-Database Architecture

### A. PostgreSQL (Relational Data Engine)
- **Purpose**: Core entity persistence requiring ACID guarantees, foreign key constraints, and relational joins.
- **Entities**:
  - `users` (Account management, status, identity).
  - `roles`, `permissions`, `role_permissions` (Granular RBAC).
  - `teams`, `team_members` (Workspace isolation).
  - `social_accounts` (OAuth connected profiles with Fernet-encrypted token storage).
  - `posts` (Drafts, scheduled dispatches, recurrence rules).
  - `campaigns` (Strategic groupings, date boundaries, budget caps).
  - `publishing_logs` (Relational audit log per dispatch).

### B. MongoDB (Unstructured & Analytics Engine)
- **Purpose**: Fast document storage for high-frequency raw social API responses, time-series engagement metrics, and webhook event payloads.
- **Collections**:
  - `raw_metrics`: Exact JSON payloads retrieved from Meta Graph, LinkedIn, X, and YouTube APIs.
  - `webhook_events`: Inbound real-time platform event logs.
  - `audit_traces`: Detailed security and background job execution traces.

### C. Redis (Broker & Dynamic Cache)
- **Purpose**: Celery message broker, background task status storage, OAuth state parameter validation, and rate-limiting.

## 3. Cryptography & Secrets Vault
- Sensitive credentials (`access_token`, `refresh_token`, platform secrets) are encrypted before writing to PostgreSQL using **Fernet AES-256 symmetric encryption** (`app/core/crypto.py`).
- Plaintext secrets are never written to logs or standard database dumps.

## 4. Docker Infrastructure
Orchestrated via `docker-compose.yml`:
- `socialpilot_postgres`: PostgreSQL 15 on port 5432 with health check ping.
- `socialpilot_mongodb`: MongoDB 6 on port 27017.
- `socialpilot_redis`: Redis 7 on port 6379 with health check ping.
- `socialpilot_backend`: FastAPI app service on port 8000.
- `socialpilot_celery_worker`: Background execution worker cluster.
- `socialpilot_celery_beat`: Cron scheduler executing periodic jobs.
- `socialpilot_frontend`: Nginx-served React SPA on port 5173.
