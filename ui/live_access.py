"""Server-side opt-in gate for the non-synthetic research UI.

No access configuration => public demo only. Do not allow a client-supplied
toggle, query argument, cookie, or API key to enable live providers.
"""

import hashlib
import hmac
import os
import re

FLAG = "AGENT_LIVE_RESEARCH_ENABLED"
HASH = "AGENT_LIVE_ACCESS_SHA256"


def live_access_configured(env=None):
    """Require both explicit server opt-in and a valid hashed high-entropy token."""
    e = os.environ if env is None else env
    digest = str(e.get(HASH, "")).strip().lower()
    return (str(e.get(FLAG, "")).strip() == "1"
            and re.fullmatch(r"[a-f0-9]{64}", digest) is not None)


def verify_live_token(token, env=None):
    """Constant-time comparison; never log or return the provided token."""
    e = os.environ if env is None else env
    if not live_access_configured(e) or not isinstance(token, str) or not token:
        return False
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expected_hash = str(e[HASH]).strip().lower()
    return hmac.compare_digest(token_hash, expected_hash)
