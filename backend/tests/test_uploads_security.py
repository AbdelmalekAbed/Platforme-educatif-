"""Security tests for /uploads access control.

Proves the fix for the original vulnerability: the /uploads tree used to be a
public StaticFiles mount, so anyone (even logged out) could download a file by
guessing/leaking its URL. Now a file is served only with a valid signed token.

These tests are self-contained: the /uploads route does not touch the database,
so they run with FastAPI's TestClient and require no Neon connection. They run
under pytest OR standalone:

    cd backend
    ./venv/bin/python -m pytest tests/test_uploads_security.py     # if pytest is installed
    ./venv/bin/python tests/test_uploads_security.py               # always works
"""
import os
import sys
import time

# Make `app` importable and load settings from backend/.env regardless of CWD.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(_HERE)
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)
os.chdir(_BACKEND)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.api.routes.uploads import UPLOAD_DIR  # noqa: E402
from app.core.security.media_tokens import (  # noqa: E402
    sign_media_url,
    verify_media_token,
    _signature,
)

client = TestClient(app)

PROBE_NAME = "zz_security_probe_delete_me.pdf"
PROBE_PATH = UPLOAD_DIR / PROBE_NAME
PROBE_URL = f"/uploads/{PROBE_NAME}"
PROBE_BYTES = b"%PDF-1.4\n-- secret enrolled-only content --\n%%EOF\n"


def setup_module(module=None):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PROBE_PATH.write_bytes(PROBE_BYTES)


def teardown_module(module=None):
    try:
        PROBE_PATH.unlink()
    except FileNotFoundError:
        pass


# --------------------------------------------------------------------------
# The core vulnerability: unauthenticated / unsigned access must be denied.
# --------------------------------------------------------------------------

def test_raw_url_without_token_is_denied():
    """The exact attack from the report: GET /uploads/<file> with no token."""
    r = client.get(PROBE_URL)
    assert r.status_code == 403, f"expected 403, got {r.status_code}"
    assert PROBE_BYTES not in r.content, "file bytes leaked without a token!"


def test_query_without_token_is_denied():
    r = client.get(PROBE_URL, params={"exp": str(int(time.time()) + 3600)})
    assert r.status_code == 403


def test_token_without_exp_is_denied():
    sig = _signature(PROBE_URL, int(time.time()) + 3600)
    r = client.get(PROBE_URL, params={"token": sig})
    assert r.status_code == 403


# --------------------------------------------------------------------------
# A valid signed URL still works (legitimate access is not broken).
# --------------------------------------------------------------------------

def test_signed_url_serves_the_file():
    signed = sign_media_url(PROBE_URL)
    assert signed != PROBE_URL and "token=" in signed and "exp=" in signed
    r = client.get(signed)
    assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}"
    assert r.content == PROBE_BYTES
    # Access-controlled content must not be cached by shared proxies.
    assert "private" in r.headers.get("cache-control", "")
    # PDFs must be served with the right media type so they render inline.
    assert r.headers.get("content-type", "").startswith("application/pdf")


# --------------------------------------------------------------------------
# Forged / tampered / expired tokens are rejected.
# --------------------------------------------------------------------------

def test_tampered_token_is_denied():
    signed = sign_media_url(PROBE_URL)
    # Flip the last hex char of the token.
    flipped = "0" if signed[-1] != "0" else "1"
    bad = signed[:-1] + flipped
    r = client.get(bad)
    assert r.status_code == 403


def test_expired_token_is_denied():
    past = int(time.time()) - 60
    sig = _signature(PROBE_URL, past)  # a *correctly signed* but expired token
    r = client.get(PROBE_URL, params={"exp": str(past), "token": sig})
    assert r.status_code == 403


def test_token_for_a_different_path_is_denied():
    """A token minted for file A must not unlock file B (path is bound)."""
    other = sign_media_url("/uploads/some_other_file.pdf")
    # Reuse the other file's exp+token on the probe URL.
    qs = other.split("?", 1)[1]
    r = client.get(f"{PROBE_URL}?{qs}")
    assert r.status_code == 403


# --------------------------------------------------------------------------
# Path traversal cannot escape the uploads dir, even with a valid signature.
# --------------------------------------------------------------------------

def test_path_traversal_is_blocked():
    traversal = "/uploads/../app/main.py"
    signed = sign_media_url(traversal)  # we *can* sign it; the route must still refuse
    r = client.get(signed)
    assert r.status_code in (403, 404), f"traversal returned {r.status_code}"
    assert b"create_app" not in r.content and b"FastAPI" not in r.content


# --------------------------------------------------------------------------
# Unit-level checks on the signing primitives.
# --------------------------------------------------------------------------

def test_verify_roundtrip_and_failures():
    now = 1_000_000
    exp = now + 3600
    sig = _signature(PROBE_URL, exp)
    assert verify_media_token(PROBE_URL, sig, str(exp), now=now) is True
    assert verify_media_token(PROBE_URL, sig, str(exp), now=exp + 1) is False  # expired
    assert verify_media_token(PROBE_URL, sig, str(exp + 1), now=now) is False  # exp tampered
    assert verify_media_token("/uploads/other.pdf", sig, str(exp), now=now) is False  # path
    assert verify_media_token(PROBE_URL, None, str(exp), now=now) is False
    assert verify_media_token(PROBE_URL, sig, None, now=now) is False
    assert verify_media_token(PROBE_URL, sig, "not-an-int", now=now) is False


def test_sign_is_idempotent_and_selective():
    once = sign_media_url(PROBE_URL)
    assert sign_media_url(once) == once  # never double-sign
    # Non-/uploads URLs pass through untouched.
    assert sign_media_url("https://youtube.com/watch?v=x") == "https://youtube.com/watch?v=x"
    assert sign_media_url("") == ""
    assert sign_media_url(None) is None


def test_stable_url_within_window_for_caching():
    """Same file signed at two close instants yields the same URL (cacheable)."""
    a = sign_media_url(PROBE_URL, now=1_000_000)
    b = sign_media_url(PROBE_URL, now=1_000_000 + 60)  # 1 min later, same window
    assert a == b


def test_prod_refuses_placeholder_secret_key():
    """The whole /uploads boundary is the HMAC: a known SECRET_KEY = forgeable.
    The app must fail closed in production (DEBUG=False) on placeholder/short keys."""
    from app.core.config.settings import Settings
    for bad in (
        "CHANGE-ME-IN-PRODUCTION-USE-LONG-RANDOM-STRING",
        "change-me-in-production-use-long-random-secret-key",
        "too-short",
    ):
        raised = False
        try:
            Settings(DEBUG=False, SECRET_KEY=bad)
        except Exception:
            raised = True
        assert raised, f"prod must reject weak SECRET_KEY {bad!r}"
    # A strong key in prod is accepted, and the placeholder is fine in local dev.
    Settings(DEBUG=False, SECRET_KEY="0123456789abcdef0123456789abcdef0123456789ab")
    Settings(DEBUG=True, SECRET_KEY="change-me-in-production-use-long-random-secret-key")


def test_homework_attachment_urls_are_signed():
    """Latent-gap fix: homework attachment URLs must be signed like other /uploads URLs."""
    import uuid
    from datetime import datetime, timezone
    from app.modules.homework.schemas import HomeworkResponse, SubmissionResponse

    now = datetime.now(timezone.utc)
    h = HomeworkResponse(id=uuid.uuid4(), course_id=uuid.uuid4(), title="t", max_grade=100,
                         attachment_url="/uploads/hw.pdf", is_published=True, created_at=now)
    assert "token=" in h.model_dump()["attachment_url"]

    s = SubmissionResponse(id=uuid.uuid4(), homework_id=uuid.uuid4(), student_id=uuid.uuid4(),
                           attachment_url="/uploads/sub.pdf", submitted_at=now, status="submitted")
    assert "token=" in s.model_dump()["attachment_url"]

    # None attachment passes through untouched.
    h2 = HomeworkResponse(id=uuid.uuid4(), course_id=uuid.uuid4(), title="t", max_grade=100,
                          is_published=True, created_at=now)
    assert h2.model_dump()["attachment_url"] is None


# --------------------------------------------------------------------------
# Standalone runner (no pytest needed).
# --------------------------------------------------------------------------

def _run_standalone() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    setup_module()
    failures = 0
    try:
        for t in tests:
            try:
                t()
                print(f"PASS  {t.__name__}")
            except AssertionError as e:
                failures += 1
                print(f"FAIL  {t.__name__}: {e}")
            except Exception as e:  # noqa: BLE001
                failures += 1
                print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    finally:
        teardown_module()
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_standalone())
