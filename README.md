AI Social Platform — Initial Release
This is the initial hackathon-ready build of an AI-powered social media platform with a Next.js web client, a FastAPI API gateway, and supporting workers, where automated posting is enabled for Twitter and other platforms are stubbed for demo in this version.
To run locally, provide the required .env files and start the full stack via Docker Compose as described below.

Overview
Monorepo layout with apps/, services/, infra/, prisma/, and docs/ to keep frontend, API, workers, and infra cleanly separated.

Web client uses React/Next.js with JWT auth, dashboard, scheduling UI, chatbot surface, and API integration to the gateway.

API gateway is FastAPI with routes for auth, posts, scheduling, OAuth, and publishing, exposing REST endpoints on port 8000.

This release publishes to Twitter via the gateway; other platforms return demo responses to unblock the flow.

Status
Automated posting: Twitter enabled through the publish endpoint and a TwitterClient call path.

LinkedIn/Instagram: UI, routes, and skeleton workers in place with demo mode responses pending full automation.

Flow aligns to the hackathon sequence: Account Linking → Chatbot → Content Editing → Scheduling → Automated Posting.

Features
Twitter publishing via FastAPI route that invokes a Twitter client and marks posts published with an external_id on success.

Calendar/scheduling UI in the web client that displays stats and recent posts from the posts and posts/stats endpoints.

Monorepo infra with Docker Compose bringing up Postgres, Redis, API gateway, worker-scheduler, automation-backend, and web-client.

Clear separation of concerns: web-client (Next.js), api-gateway (FastAPI), automation-backend (Python), worker-scheduler (Node/TS).

Architecture
apps/web-client: Next.js frontend with pages for dashboard, calendar, chatbot, and settings, plus components such as Header, Sidebar, and PostCard.

apps/worker-scheduler: Node.js service for queued jobs and schedule execution, designed to trigger publishing via the API gateway.

services/api-gateway: FastAPI service exposing auth, posts, schedule, and chatbot routes, with platform integrations and Redis use.

services/automation-backend: Python service for headless automation paths and HTTP replay helpers, prepared for multi-platform posting.

infra/docker-compose.yml: Multi-service local orchestration with health checks and inter-service networking on a backend bridge.

Monorepo Structure
Root contains apps/, services/, infra/, prisma/, and docs/ to support development, deployment, and documentation.

The structure is optimized for the hackathon flow and keeps worker and scraping logic isolated from the API gateway.

Environment Variables
Create .env files before running, keeping real secrets out of version control and committing only sanitized .env.example for teammates.

services/api-gateway/.env

JWT_SECRET, GEMINI_API_KEY, DATABASE_URL, REDIS_URL as required by the gateway and integrations.

services/automation-backend/.env

API_BASE_URL and REDIS_URL for internal service calls and job coordination.

apps/worker-scheduler/.env

REDIS_URL, API_BASE_URL, and TZ to run scheduled tasks against the gateway.

apps/web-client/.env.local

NEXT_PUBLIC_API_URL so the frontend points to the gateway, following Next.js env conventions.

Quick Start with Docker
From the project root, validate Compose and ensure env files resolve correctly to avoid path issues.

Build and start the full stack with health-checked dependencies and service ordering.

Commands:

powershell
# Validate from repo root
docker compose -f infra\docker-compose.yml config

# Build fresh images
docker compose -f infra\docker-compose.yml build --pull

# Start core infra, then services
docker compose -f infra\docker-compose.yml up -d db redis
docker compose -f infra\docker-compose.yml up -d api-gateway automation-backend worker-scheduler
docker compose -f infra\docker-compose.yml up -d web-client

# Check status
docker compose -f infra\docker-compose.yml ps
Notes:

If the API gateway fails to import app.main, ensure the service working_dir is /app so uvicorn loads app.main correctly.

Always run Compose from the repo root or use ../ prefixes in env_file paths to ensure Docker resolves files properly.

Local Development (Optional)
Run services in Docker but point the editor to container interpreters or local venvs to resolve imports and types.

For Python editing without Docker interpreters, create .venv per service and install requirements.txt to mirror container deps.

API Overview
Auth endpoints: login/register and me are exposed by the gateway for the frontend session flow.

Posts endpoints: GET /posts, GET /posts/stats, CRUD operations, and POST /posts/{id}/publish for platform publishing.

The frontend calls posts and stats on dashboard load and renders totals plus recent posts.

Git and Secrets
Ensure .env and .env.* are ignored at every directory level, keeping secrets out of the repo and committing only .env.example.

If a secret was ever tracked, remove it from the index with git rm --cached and rely on .gitignore to prevent re-add.

Roadmap
Complete LinkedIn and Instagram automation in the gateway and automation-backend to move from demo to full publish.

Expand analytics and calendar insights to align with the hackathon’s dashboard expectation and deliverable checklist.

Harden scheduling, retries, and per-platform content validation across workers to ensure reliable, compliant posting.

How This Aligns With the Hackathon
The stack covers the required areas: social integrations, AI chatbot, calendar scheduling, and automated posting.

The README, Docker setup, and monorepo structure support a smooth demo and meet the documentation deliverable.

Useful Ports
Web client: http://localhost:3000 for the Next.js app and dashboard interface.

API gateway: http://localhost:8000 for auth, posts, and integration endpoints consumed by the frontend.

Contributing
Follow the monorepo layout and keep secrets out of Git by reusing the provided ignore rules and .env.example pattern.

PRs focusing on LinkedIn/Instagram publishing, analytics, and calendar UX refinements are most impactful next.

If any service fails to build or start, re-run the build with --no-cache and verify env file paths from the project root.