from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.db.models import Incident, IncidentEmbedding
from app.db.session import AsyncSessionLocal
from app.services.rag import embed_text

MOCK_SPECS: list[dict] = [
    {
        "title": "Payment API latency spike after canary deploy",
        "severity": "P2",
        "status": "resolved",
        "service": "payment-api",
        "description": (
            "p95 latency jumped from 120ms to 950ms minutes after a canary rollout. "
            "Errors remained low but checkout funnel conversion dipped. The spike correlated "
            "with increased calls to a new PSP endpoint."
        ),
        "deployment_ref": "a3f9c2d1",
        "resolution": (
            "Rolled back canary to 0% traffic, restored baseline latency, then fixed timeout "
            "configuration before a phased re-rollout."
        ),
    },
    {
        "title": "Checkout pod OOMKilled during peak traffic",
        "severity": "P1",
        "status": "resolved",
        "service": "checkout-service",
        "description": (
            "Kubernetes evicted checkout pods with OOMKilled reason during a flash sale. "
            "HPA could not add capacity fast enough while memory limits were set too low."
        ),
        "deployment_ref": "INC-1042",
        "resolution": "Raised memory limits, tuned HPA cooldown, and pre-warmed replicas ahead of events.",
    },
    {
        "title": "Orders DB connection pool exhausted",
        "severity": "P1",
        "status": "resolved",
        "service": "orders-service",
        "description": (
            "orders-service exhausted its Postgres pool causing cascading timeouts. "
            "A batch job held connections longer than expected while traffic remained high."
        ),
        "deployment_ref": "b7e2a91c",
        "resolution": "Separated batch connection DSN, increased pool size, and added pool wait metrics.",
    },
    {
        "title": "Auth deployment rollback after failed migration",
        "severity": "P2",
        "status": "resolved",
        "service": "auth-service",
        "description": (
            "A schema migration partially applied and caused login failures. "
            "The pipeline automatically rolled back the deployment within minutes."
        ),
        "deployment_ref": "d4adbeef",
        "resolution": "Rollback completed; migration fixed offline and re-applied in maintenance window.",
    },
    {
        "title": "CI/CD pipeline failure blocking main merges",
        "severity": "P3",
        "status": "resolved",
        "service": "ci-platform",
        "description": (
            "GitHub Actions workflows failed on main due to an expired OIDC trust configuration. "
            "No production deploy occurred but release cadence stalled."
        ),
        "deployment_ref": "cafebabe",
        "resolution": "Refreshed OIDC thumbprints and rotated workload identity bindings.",
    },
    {
        "title": "Auth service sustained high CPU",
        "severity": "P2",
        "status": "resolved",
        "service": "auth-service",
        "description": (
            "CPU saturation on auth-service nodes correlated with JWT introspection storms. "
            "Latency increased modestly but error budget remained intact."
        ),
        "deployment_ref": "e11e7e55",
        "resolution": "Scaled out replicas, added caching for introspection responses, and rate-limited noisy clients.",
    },
    {
        "title": "Redis miss storm overloads primary database",
        "severity": "P1",
        "status": "resolved",
        "service": "catalog-api",
        "description": (
            "A bad cache key versioning change caused near-zero hit rate. "
            "Read traffic collapsed onto Postgres primaries."
        ),
        "deployment_ref": "badc0de8",
        "resolution": "Reverted key format, warmed caches, and temporarily scaled DB read replicas.",
    },
    {
        "title": "api-gateway SSL certificate expiry warning",
        "severity": "P4",
        "status": "resolved",
        "service": "api-gateway",
        "description": (
            "Monitoring flagged a TLS certificate expiring in 14 days on the public gateway. "
            "No customer impact yet; renewal automation had stalled on a failed DNS challenge."
        ),
        "deployment_ref": "ssl-rotate-12",
        "resolution": "Manual DNS challenge completed and cert renewed; automation repaired.",
    },
    {
        "title": "Elasticsearch cluster health yellow",
        "severity": "P3",
        "status": "open",
        "service": "search-index",
        "description": (
            "Elasticsearch reports yellow status after a single data node disk crossed 85%. "
            "Query latency is slightly elevated but searches still succeed."
        ),
        "deployment_ref": "f00dfaced",
        "resolution": None,
    },
    {
        "title": "Ingress 502s after nginx config change",
        "severity": "P1",
        "status": "mitigating",
        "service": "edge-ingress",
        "description": (
            "A config map update introduced an invalid upstream block causing intermittent 502s. "
            "Mitigation in progress while validating the corrected manifest."
        ),
        "deployment_ref": "nginx-cfg-9",
        "resolution": None,
    },
    {
        "title": "Memory leak suspected in order-processor workers",
        "severity": "P2",
        "status": "open",
        "service": "order-processor",
        "description": (
            "RSS grows steadily on long-lived workers until periodic restarts. "
            "Heap profiles suggest a retained batch buffer after Kafka poll batches."
        ),
        "deployment_ref": "leak-hunt-01",
        "resolution": None,
    },
    {
        "title": "Critical disk usage on centralized logging node",
        "severity": "P2",
        "status": "mitigating",
        "service": "logging-node",
        "description": (
            "A logging node reached 92% disk utilization due to retained compressed archives. "
            "Ingest is still accepting logs but rotation jobs are backlogged."
        ),
        "deployment_ref": "disk-INC-2201",
        "resolution": None,
    },
    {
        "title": "Checkout pods failing readiness probes",
        "severity": "P1",
        "status": "open",
        "service": "checkout-service",
        "description": (
            "Readiness failures caused endpoints to flap during rollout. "
            "The readiness check hits a dependency that occasionally times out under load."
        ),
        "deployment_ref": "probe-fix-3",
        "resolution": None,
    },
    {
        "title": "JWT validation errors spike in user-service",
        "severity": "P2",
        "status": "open",
        "service": "user-service",
        "description": (
            "A key rotation mismatch caused elevated 401s for a subset of clients still pinned "
            "to the previous JWKS kid."
        ),
        "deployment_ref": "jwt-kid-7",
        "resolution": None,
    },
    {
        "title": "Rate limiter blocks legitimate checkout traffic",
        "severity": "P1",
        "status": "mitigating",
        "service": "edge-ingress",
        "description": (
            "A mis-tuned WAF rate rule began throttling shared NAT egress IPs used by enterprise customers."
        ),
        "deployment_ref": "waf-rl-44",
        "resolution": None,
    },
    {
        "title": "Mesh DNS resolution failures for inventory calls",
        "severity": "P1",
        "status": "open",
        "service": "service-mesh-dns",
        "description": (
            "CoreDNS saturation led to intermittent NXDOMAIN-like failures for internal service names."
        ),
        "deployment_ref": "dns-mesh-2",
        "resolution": None,
    },
    {
        "title": "gRPC timeouts between inventory and warehouse",
        "severity": "P2",
        "status": "open",
        "service": "inventory-service",
        "description": (
            "Warehouse upstream began rejecting slow calls; inventory-service hit deadline exceeded errors."
        ),
        "deployment_ref": "grpc-tmo-aa",
        "resolution": None,
    },
    {
        "title": "Kafka consumer lag spike on order-events",
        "severity": "P2",
        "status": "open",
        "service": "order-events-consumer",
        "description": (
            "A poison message pattern caused repeated rebalances and lag climbed into hours."
        ),
        "deployment_ref": "kafka-lag-88",
        "resolution": None,
    },
    {
        "title": "S3 policy change blocks artifact uploads",
        "severity": "P2",
        "status": "mitigating",
        "service": "release-artifacts",
        "description": (
            "A tightened bucket policy denied PutObject for the build role used by release pipelines."
        ),
        "deployment_ref": "s3-pol-13",
        "resolution": None,
    },
    {
        "title": "HPA scaling delay during sudden traffic surge",
        "severity": "P2",
        "status": "open",
        "service": "checkout-service",
        "description": (
            "Autoscaler reacted slowly due to conservative scale-up stabilization while traffic doubled in minutes."
        ),
        "deployment_ref": "hpa-surge-4",
        "resolution": None,
    },
]


def _log_snapshot(service: str, idx: int) -> str:
    base = f"svc={service} idx={idx}"
    lines = [
        f"2026-05-10T10:{idx:02d}:01Z ERROR {base} request_id=r-{idx} upstream_timeout=1300ms",
        f"2026-05-10T10:{idx:02d}:03Z WARN {base} request_id=r-{idx} retry=1/3 backoff=250ms",
        f"2026-05-10T10:{idx:02d}:05Z INFO {base} request_id=r-{idx} circuit=half_open",
        f"2026-05-10T10:{idx:02d}:07Z ERROR {base} request_id=r-{idx} status=503 detail=upstream_unavailable",
        f"2026-05-10T10:{idx:02d}:09Z INFO {base} request_id=r-{idx} autoscale_signal=cpu_high",
        f"2026-05-10T10:{idx:02d}:11Z WARN {base} request_id=r-{idx} saturation=p95_latency",
    ]
    return "\n".join(lines)


def _metrics(service: str, idx: int) -> str:
    return (
        f"p95 latency {420 + idx}ms (baseline 140ms), error rate {(0.02 + idx * 0.001):.3f}, "
        f"CPU {72 + (idx % 5)}% on {service} pods."
    )


async def seed_incidents() -> None:
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Incident))
        if count and count > 0:
            return

        now = datetime.now(timezone.utc)
        incidents: list[Incident] = []
        for i, spec in enumerate(MOCK_SPECS):
            started = now - timedelta(days=30 - i)
            incidents.append(
                Incident(
                    title=spec["title"],
                    severity=spec["severity"],
                    status=spec["status"],
                    service=spec["service"],
                    environment="production",
                    description=spec["description"],
                    log_snapshot=_log_snapshot(spec["service"], i),
                    metrics_summary=_metrics(spec["service"], i),
                    deployment_ref=spec["deployment_ref"],
                    resolution=spec.get("resolution"),
                    started_at=started,
                    resolved_at=(started + timedelta(hours=2)) if spec["status"] == "resolved" else None,
                )
            )
        session.add_all(incidents)
        await session.flush()

        texts = [
            f"{inc.title}\n{inc.description}\n{inc.log_snapshot}"
            for inc in incidents
        ]
        vectors = embed_text(texts)
        for inc, vec in zip(incidents, vectors, strict=True):
            session.add(IncidentEmbedding(incident_id=inc.id, embedding=vec))
        await session.commit()
