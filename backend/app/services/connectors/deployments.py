from datetime import datetime, timedelta, timezone


def _iso(ts: datetime) -> str:
    return ts.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_recent_deployments(service: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    t0 = now - timedelta(minutes=15)
    t1 = now - timedelta(hours=3)
    t2 = now - timedelta(days=1)
    risky = "feat: migrate payment processor to new provider"
    return [
        {
            "sha": "a3f9c2d1",
            "deployed_at": _iso(t0),
            "deployed_by": "github-actions",
            "status": "failed",
            "message": risky if "payment" in service.lower() else "feat: tighten timeouts on checkout paths",
        },
        {
            "sha": "b1d4e9a7",
            "deployed_at": _iso(t1),
            "deployed_by": "github-actions",
            "status": "success",
            "message": "chore: update dependency versions",
        },
        {
            "sha": "c0ffee12",
            "deployed_at": _iso(t2),
            "deployed_by": "spinnaker",
            "status": "success",
            "message": "fix: correct nginx upstream keepalive settings",
        },
    ]
