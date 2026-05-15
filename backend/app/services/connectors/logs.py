from datetime import datetime, timedelta, timezone
import hashlib


def _iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_logs(service: str, incident_id: str) -> str:
    base = hashlib.sha256(f"{service}:{incident_id}".encode()).hexdigest()[:6]
    now = datetime.now(timezone.utc)
    lines: list[str] = []
    svc = service.lower()
    templates: list[tuple[str, str, str]] = [
        ("INFO", "request", f"incoming GET /health trace_id=tr-{base}"),
        ("WARN", "upstream", f"slow dependency call latency_ms=842 service={svc}"),
        ("ERROR", "worker", f"processing failed: transient timeout talking to downstream"),
        ("ERROR", "http", f"GET /v1/orders 503 upstream_error=connection_reset"),
        ("WARN", "cache", f"redis SET took 120ms key_prefix={svc}:session"),
        ("INFO", "deploy", f"rolling restart observed pod={svc}-7d9c4b8-xk2m1"),
        ("ERROR", "db", f"pool exhausted active=200 max=200 waiting=47"),
        ("WARN", "k8s", f"OOMKilled risk: rss_mb=1800 limit_mb=2048 container={svc}"),
        ("ERROR", "grpc", f"rpc error: code=DeadlineExceeded desc=context deadline exceeded"),
        ("INFO", "auth", f"jwt validation failures last_5m=0 (baseline check)"),
    ]
    if "payment" in svc:
        templates[2] = ("ERROR", "payments", "card capture failed: upstream PSP latency spike")
    if "checkout" in svc:
        templates[2] = ("ERROR", "cart", "checkout finalize failed: inventory lock wait timeout")
    if "auth" in svc:
        templates[2] = ("ERROR", "oauth", "token introspection error: 500 from idp")
    if "order" in svc:
        templates[2] = ("ERROR", "orders", "order write failed: FK constraint on line_items")

    for i, (level, comp, msg) in enumerate(templates[:9]):
        ts = _iso(now - timedelta(seconds=30 * (9 - i)))
        lines.append(f"{ts} {level} {svc} {comp} incident_id={incident_id} msg=\"{msg}\"")
    return "\n".join(lines)
