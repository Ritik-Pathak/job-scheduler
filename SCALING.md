# One-pager: Scaling Strategy

**Traffic target**: ~10,000 global users, ~1,000 services, ~6,000 API req/min

## Move from single-node APScheduler to distributed scheduling
- **Why**: APScheduler is great for POC and single-instance. For horizontal scale and HA,
  use **Celery (or RQ) + Celery Beat** (or Airflow/Temporal for complex workflows).
- **Pattern**
  - API service: stateless FastAPI behind a load balancer (NLB/ALB/Ingress).
  - Scheduler: Celery Beat schedules tasks into a **broker** (RabbitMQ/Redis).
  - Workers: Celery workers consume tasks; autoscale via HPA (K8s), ASG, or Nomad.
  - Caching: Redis for idempotency keys, rate limits, and dedupe.
  - Observability: Prometheus + Grafana, OpenTelemetry traces, ELK/CloudWatch logs.
  - Reliability: Exactly-once semantics via idempotent task design + outbox pattern.
- **Multi-region**
  - Run per-region worker pools. Keep a single *source-of-truth* scheduler or per-region
    schedulers with leader election and clock skew safeguards.
  - Store timestamps in UTC; compute user-local times at the edge.

## API & Data
- **DB**: SQLite with connection pooling (PgBouncer), proper indexes on `status`, `next_run_at`, `created_at`.
- **Read replication**: Route reads (`GET /jobs`) to replicas; writes to primary.
- **Pagination**: Always paginate list endpoints; provide filters.
- **Backpressure**: Use async DB drivers and bounded queues; shed load with 429s gracefully.

## Ops
- **Containers**: Docker images, distroless base, non-root user.
- **Kubernetes**: separate Deployments for API, Beat, Workers; HPA on CPU/QPS/queue depth.
- **Security**: OIDC/JWT auth gateway; network policies; secrets via KMS/Sealed Secrets.
- **CI/CD**: lint, type-check (mypy), tests, SAST; progressive delivery (blue/green/canary).

## Migration path (POC -> Prod)
1. Start with this APScheduler service (single pod). 
2. Introduce Celery + Redis, keep API unchanged (adapter in `scheduler.service`).
3. Swap APScheduler with Celery Beat; run 2+ workers; add metrics & alerts.
4. Add sharding/tenancy & region-aware scheduling if needed.
