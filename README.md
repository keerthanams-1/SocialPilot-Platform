**Production-Grade Social Media Publishing, Analytics & Multi-Platform Campaign Infrastructure**

Developed & Maintained by [@keerthanams-1](https://github.com/keerthanams-1)

---

## 📌 Executive Overview
**SocialPilot** is a production-grade enterprise social media management, publishing, analytics, and campaign management engine built using official platform drivers (Meta Graph API, LinkedIn REST v2, X API v2, YouTube Data API v3). 

Designed with **Clean Architecture**, SocialPilot features an enterprise multi-database engine (PostgreSQL, MongoDB, Redis), Refresh Token Rotation (RTR), Fernet AES-256 token encryption vault, role-based multi-dashboard workspace (Admin, Business, Content Creator, Marketing Team), multi-format report generator (PDF, CSV, Excel), live WebSocket alert dispatches, and Nginx reverse-proxied Docker containerization.

---

## 🏗️ Technology Stack

| Layer | Technologies & Tools |
| :--- | :--- |
| **Core API Engine** | FastAPI (Python 3.13), Uvicorn ASGI Server, Pydantic V2 |
| **Relational Database** | PostgreSQL 15, SQLAlchemy ORM (Connection Pooling & Pre-Ping) |
| **Document Store** | MongoDB 6.0 (Raw payload capture & Time-series metrics) |
| **Cache & Message Broker**| Redis 7.0 (Rate limiting, Distributed locking & OAuth state) |
| **Async Task Workers** | Celery 5.3, Celery Beat (Periodic task crontab scheduler) |
| **Security Cryptography** | PyJWT (RS256/HS256), Passlib (Bcrypt), Cryptography (Fernet AES-256) |
| **Reporting & Export** | ReportLab (Executive PDF Briefs), OpenPyXL (Excel Workbooks) |
| **Frontend Workspace** | React 18, Vite 5, Vanilla CSS Design System, Lucide Icons |
| **Production Proxy & Ops**| Nginx Reverse Proxy, Docker, Docker Compose |

---

## 📁 Repository Directory Structure

```text
socialpilot/
├── backend/
│   ├── app/
│   │   ├── analytics/          # Real metrics collection & KPI calculator engine
│   │   ├── authentication/     # Register, Login, RTR Refresh, Verification & Password Reset
│   │   ├── campaigns/          # Multi-channel campaign CRUD & budget rollups
│   │   ├── core/               # Security vault, Redis locks, Idempotency & Middleware
│   │   ├── dashboard/          # Role-Based multi-dashboards (Admin, Business, Creator, Marketing)
│   │   ├── database/           # PostgreSQL ORM models, MongoDB manager, Redis manager
│   │   ├── health/             # Health monitoring endpoints (/health, /health/database, /health/redis, /health/workers)
│   │   ├── media/              # Platform spec validator, image auto-resize & video thumbnail generator
│   │   ├── notifications/      # Email SMTP dispatcher, WebSocket alerts & MongoDB event log
│   │   ├── publishing/         # Real publishing engine, approval workflow & recurring posts
│   │   ├── reports/            # Executive PDF brief, CSV & Excel workbook exporter
│   │   ├── social/             # Official platform drivers (FB, IG, LinkedIn, Twitter, YouTube) & Webhooks
│   │   ├── users/              # User identity repository & session management
│   │   └── workers/            # Celery worker tasks & periodic metric sweepers
│   └── tests/                  # Automated pytest test suites (Volumes 2 to 6)
├── frontend/                   # React Vite single page application
├── nginx/
│   └── nginx.conf              # Production Nginx reverse proxy configuration
├── docker-compose.yml          # Multi-container production orchestration
└── .env.example                # Production environment template
```

---

## ⚡ Quick Start & Deployment Guide

### Option 1: Docker Compose Production Deployment (Recommended)

1. **Clone Repository & Copy Environment Template**:
   ```bash
   git clone https://github.com/enterprise/socialpilot.git
   cd socialpilot
   cp .env.example .env
   ```

2. **Launch Container Orchestration**:
   ```bash
   docker-compose up -d --build
   ```

3. **Access SocialPilot Services**:
   - **Nginx Entrypoint**: `http://localhost`
   - **FastAPI OpenAPI Swagger**: `http://localhost/docs`
   - **Health Readiness Check**: `http://localhost/health`
   - **Frontend UI Workspace**: `http://localhost:5173`

---

### Option 2: Local Python Virtual Environment Setup

1. **Set Up Python Virtual Environment**:
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Pytest Automated Test Suite**:
   ```bash
   python -m pytest tests/test_volume2_auth.py tests/test_volume3_social_celery.py tests/test_volume3_enterprise_enhancements.py tests/test_volume4_publishing_campaigns.py tests/test_volume5_analytics.py tests/test_volume6_final_audit.py -v
   ```

3. **Launch Backend API Server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

---

## 🔒 Security Architecture Highlights

- **JWT Refresh Token Rotation (RTR)**: Single-use refresh tokens stored with session UUID tracking. Automatic reuse detection triggers emergency revocation of all active sessions for the user.
- **Fernet AES-256 Vault**: OAuth tokens (`access_token`, `refresh_token`) are encrypted before database insertion and decrypted strictly on-demand inside driver execution context.
- **Role-Based Access Control (RBAC)**: Protected by `@require_role(["Administrator", "Business User"])` middleware enforcing zero cross-role data leaks.
- **Security Headers & Rate Limiting**: HTTP Security Headers (`X-Frame-Options: DENY`, `HSTS`, `CSP`) and Redis sliding window rate-limiting applied across all public API routes.

---

## 🧪 Comprehensive Automated Test Verification

Execution of complete 30-test suite across Volumes 2 to 6:
```powershell
======================= 30 passed, 159 warnings in 82.17s =======================
```

| Test Suite File | Coverage Scope | Status |
| :--- | :--- | :---: |
| `test_volume2_auth.py` | User registration, login, RTR refresh, verification & reset | **PASSED** |
| `test_volume3_social_celery.py` | OAuth platform drivers, token encryption & publishing dispatches | **PASSED** |
| `test_volume3_enterprise_enhancements.py` | Redis locking, idempotency, webhook signatures & crash recovery | **PASSED** |
| `test_volume4_publishing_campaigns.py` | Campaign management, media assets, approval workflow & recurring posts | **PASSED** |
| `test_volume5_analytics.py` | Role dashboards, metric collection, notifications & PDF/CSV/Excel reports | **PASSED** |
| `test_volume6_final_audit.py` | Security headers, rate limiting, Fernet vault & health monitoring APIs | **PASSED** |

---

## 📄 License & Specification Compliance
Designed and implemented in compliance with **SocialPilot Development Specification Volumes 1 through 6**.
