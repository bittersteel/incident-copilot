from fastapi import Depends, Header, HTTPException

from app.config import settings
from app.db.session import get_db


async def verify_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


APIKeyDep = Depends(verify_api_key)
DBDep = Depends(get_db)
