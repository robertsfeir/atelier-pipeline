# Docker & Infrastructure Reference

Jerome reads this when designing infrastructure, deployment, or container
architecture. Eva reads when verifying CI/CD.

---

<section id="docker-compose">

## Docker Compose (Local Dev + Single-Server Production)

### MyApp Stack
```yaml
services:
  postgres:    # PostgreSQL 16 — primary data store
  redis:       # Redis 7 — cache + Celery broker
  backend:     # FastAPI (uvicorn) — port 8000
  frontend:    # Next.js — port 3000
```

### Health Checks (Always Include)
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U myapp"]
  interval: 5s
  timeout: 5s
  retries: 5
```

Services should use `depends_on` with `condition: service_healthy`:
```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
```

### Volume Strategy
- **Named volumes** for persistent data (postgres_data, redis_data).
- **Bind mounts** for development hot-reload (`./backend:/app`).
- Never use anonymous volumes for important data.

### Resource Limits (Production)
```yaml
deploy:
  resources:
    limits:
      cpus: "1.0"
      memory: 512M
    reservations:
      cpus: "0.25"
      memory: 128M
```

### Restart Policies
- Development: `restart: "no"` (crash fast, fix fast).
- Production: `restart: unless-stopped`.

### Profiles (Multi-Environment)
```yaml
services:
  backend-dev:
    profiles: ["dev"]
    command: uvicorn app.main:app --reload
  backend-prod:
    profiles: ["prod"]
    command: uvicorn app.main:app --workers 4
```

Run with: `docker compose --profile dev up`

### Networking
- Services communicate by service name (`postgres`, `redis`).
- Only expose ports that need external access.
- Backend talks to DB via `postgres:5432`, not `localhost:5432`.

</section>

---

<section id="dockerfile-best-practices">

## Dockerfile Best Practices

### Multi-Stage Builds
```dockerfile
# Builder stage — install dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Runtime stage — minimal image
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Next.js Standalone
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

Requires `output: 'standalone'` in `next.config.js`.

### Rules
- Pin base image versions (`:3.11-slim`, not `:latest`).
- Use `.dockerignore` to exclude `.git`, `node_modules`, `.env`, `__pycache__`.
- Non-root user in production images.
- Minimize layers — combine RUN commands with `&&`.
- Order layers by change frequency (deps before source code).

</section>

---

<section id="podman-compatibility">

## Podman Compatibility

Podman is a drop-in replacement for Docker with a similar CLI but important differences. Use this section when running containers on systems with Podman instead of Docker.

### CLI Differences

| Task | Docker | Podman |
|------|--------|--------|
| Start services | `docker compose up` | `podman-compose up` or `docker compose up` (if Podman emulation enabled) |
| Build image | `docker build` | `podman build` |
| Run container | `docker run` | `podman run` |
| List containers | `docker ps` | `podman ps` |
| Push to registry | `docker push` | `podman push` |

**Note:** Podman v4.0+ includes `docker` command emulation. If available on your system, `docker compose` works directly. Otherwise, use `podman-compose` (Python wrapper or native Go implementation).

### Rootless by Default

Podman runs rootless (non-root user) by default — a security advantage over Docker:
- No daemon requiring root privilege.
- Containers run as the invoking user.
- **Implication:** Bind mounts use user-namespace mappings. Files created inside a container may have unexpected UID/GID on the host.
  - Solution: Use named volumes for persistent data instead of bind mounts in production.
  - Development: Bind mounts work but ownership may require `chown` post-container.

### Pod Concepts

Podman's "pod" is a group of containers sharing network namespace (like Kubernetes pods):
- Useful for multi-container services on a single machine.
- `podman pod create` → `podman run --pod=<name>` for each service.
- For most uses, stick with `podman-compose` (manages pods under the hood).

### Systemd Integration

Podman containers can be managed by systemd for automatic restart and service management:
```bash
# Generate systemd unit file
podman generate systemd --name <container> > /etc/systemd/user/container.service

# Enable and start
systemctl --user enable container.service
systemctl --user start container.service
```

**Benefit:** Containers restart on system reboot or failure — useful for production single-server deployments.

### Compose Spec Compatibility

`podman-compose` supports Docker Compose v3.x syntax but with limitations:
- `depends_on` with `condition: service_healthy` — supported.
- `profiles` — supported (Podman 4.0+).
- `deploy.resources.limits` — **not fully supported** (Podman respects but reports differ).
- `healthcheck` — supported.

**Recommendation:** Test your `docker-compose.yml` with Podman before production. Most standard files work without changes.

### Common Gotchas When Switching from Docker

1. **Container networking:** Podman rootless containers use a user-space network. DNS resolution works, but host-to-container port access requires explicit binding (always use `ports: ["8000:8000"]` in Compose; omitting it breaks access from the host).

2. **Volume permissions:** Rootless user can't read files owned by root (UID 0). If you have existing Docker volumes owned by root, copy data to a new Podman volume first.

3. **Build cache:** Podman's build cache is separate from Docker's. `podman build` may rebuild layers Docker would cache.

4. **Registry credentials:** Podman stores credentials in `~/.local/share/containers/auth.json` (user-level), not `/root/.docker/config.json`. Use `podman login` to authenticate to registries.

5. **Systemd socket activation:** Podman supports `podman.socket` (similar to Docker's daemon.sock) but requires explicit enablement. For CI/CD, use direct `podman` commands instead of socket access.

6. **Container images:** Images are stored in `~/.local/share/containers/storage/` (user rootless) vs `/var/lib/docker` (Docker daemon). Keep in mind when estimating disk usage.

### Migration Path

To migrate a Docker Compose stack to Podman:
1. Use the same `docker-compose.yml` file.
2. Replace `docker compose` with `podman-compose` (or `docker compose` if emulation is available).
3. Test `up`, `down`, `logs`, and service health checks.
4. For production, generate systemd units and test restart behavior.
5. Adjust volume bind mounts to use named volumes if running rootless.

</section>

---

<section id="postgresql-architecture">

## PostgreSQL Architecture

### Connection Pooling
- SQLAlchemy `pool_size=10, max_overflow=20` for moderate load.
- For production scale: PgBouncer in front of Postgres.
- Always `pool_pre_ping=True` to detect stale connections.

### Migrations (Alembic)
- Forward-only in production. Never edit applied migrations.
- Test `upgrade` AND `downgrade` paths.
- Data migrations use raw SQL, not ORM models (models change, SQL doesn't).
- Always review autogenerated migrations before committing.

### Indexing Strategy
- Primary keys auto-indexed.
- Add indexes on: foreign keys, columns in WHERE clauses, columns in ORDER BY.
- For MyApp: `symbol` (frequent lookups), `created_at` (time-series queries),
  `user_id` (per-user filtering).
- Composite indexes for multi-column queries.
- Use `EXPLAIN ANALYZE` before and after to verify index impact.

### Backup Strategy
- `pg_dump` for logical backups (development, small databases).
- WAL archiving + `pg_basebackup` for production point-in-time recovery.
- Test restores regularly — untested backups aren't backups.

</section>

---

<section id="redis-architecture">

## Redis Architecture

### Use Cases for MyApp
- **Cache:** Analysis results, persona sentiment (TTL-based expiry).
- **Session store:** User sessions (if not using JWT).
- **Queue broker:** Celery task queue for async LLM jobs.
- **Rate limiting:** Per-user LLM call limits.

### Key Naming Convention
```
myapp:{domain}:{identifier}
myapp:analysis:AAPL:1w         # cached analysis
myapp:persona:AAPL:latest      # latest persona sentiment
myapp:ratelimit:user:123       # rate limit counter
```

### TTL Strategy
- Analysis cache: 1 hour (market data changes).
- Persona sentiment: 30 minutes (LLM-generated, expensive).
- Rate limit counters: 1 minute sliding window.
- Session tokens: match JWT expiry.

### Persistence
- `appendonly yes` for Celery job queue (don't lose jobs on restart).
- RDB snapshots for cache (losing cache is okay, losing queue isn't).

</section>

---

<section id="production-deployment-patterns">

## Production Deployment Patterns

### Single-Server (MVP / Early Stage)
Docker Compose + reverse proxy (nginx/Traefik). Suitable for MyApp v1.
- Traefik for automatic HTTPS (Let's Encrypt).
- Watchtower or manual `docker compose pull && docker compose up -d` for deploys.

### Container Orchestration (Scale Stage)
When single-server isn't enough:
- **AWS:** ECS Fargate (serverless containers) or EKS (Kubernetes).
- **GCP:** Cloud Run (serverless) or GKE (Kubernetes).
- **Azure:** Container Apps (serverless) or AKS (Kubernetes).

### CI/CD Pipeline Shape
```
Push → Lint/Type Check → Tests → Build Images → Push to Registry → Deploy
```
- Backend: `pytest` → Docker build → push to ECR/GCR/ACR.
- Frontend: `npm run lint && npm run build` → Docker build → push.
- Database: Run `alembic upgrade head` as a deploy step (before new backend).

### Environment Strategy
| Env | Purpose | Data |
|-----|---------|------|
| `development` | Local Docker Compose | Seed data |
| `staging` | Pre-production, identical to prod | Anonymized prod data |
| `production` | Live | Real data |

### Secrets Management
- Development: `.env` file (gitignored).
- Production: AWS Secrets Manager / GCP Secret Manager / Azure Key Vault.
- Never bake secrets into Docker images.
- Use environment variables or mounted secret files at runtime.

</section>

---

<section id="monitoring-observability">

## Monitoring & Observability (Future)

### Application Metrics
- Request latency (p50, p95, p99).
- Error rate by endpoint.
- LLM call latency and token usage.
- Cache hit/miss ratio.

### Infrastructure Metrics
- CPU, memory, disk for each container.
- Database connection pool utilization.
- Redis memory usage and eviction rate.

### Logging
- Structured JSON logging in production.
- Correlation IDs across services (request ID in headers).
- Never log sensitive data (API keys, passwords, PII).

### Tools (When Ready)
- **APM:** Sentry, Datadog, or OpenTelemetry.
- **Logs:** ELK stack, Grafana Loki, or CloudWatch.
- **Metrics:** Prometheus + Grafana or Datadog.
- **Uptime:** Simple health check ping (UptimeRobot, Checkly).

</section>
