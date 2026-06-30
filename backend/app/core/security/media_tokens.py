"""Signed, expiring URLs for files served under /uploads.

The /uploads tree (PDFs, videos, course thumbnails) is no longer exposed as
unauthenticated static files. Instead, every /uploads URL handed to a client is
signed with a short-lived HMAC token, and the file-serving route
(`app.api.routes.uploads`) refuses to serve anything without a valid token.

Only code paths that *already* require an authenticated user mint these URLs
(the content/course endpoints), so:
  - a logged-out visitor guessing /uploads/<uuid>_x.pdf gets 403, and
  - a leaked signed link grants access to a single file for a bounded window
    (see below) instead of forever, to anyone.

The signature binds the exact URL path AND the expiry. The expiry is bucketed to
a coarse window so the same file yields a stable, browser-cacheable URL within
that window (the /uploads files are content-addressed and immutable, so caching
them aggressively is safe and desirable — a PDF can weigh tens of MB).

Effective validity of a freshly minted link is (DEFAULT_TTL, DEFAULT_TTL +
_WINDOW] — currently 4h to 8h. DEFAULT_TTL is the *minimum* (long enough that a
URL never expires mid-read), and the bucketing adds up to one extra window. The
front re-mints URLs on every course (re)fetch, so this window only matters for a
link captured/leaked out of band.
"""
import hmac
import time
from hashlib import sha256

from app.core.config import settings

UPLOADS_PREFIX = "/uploads/"

_DOMAIN = b"media-url-v1"      # domain separation: these HMACs are not JWTs
DEFAULT_TTL = 4 * 3600        # minimum lifetime of a freshly minted token (s)
_WINDOW = 4 * 3600           # exp bucket → stable, cacheable URLs per window


def _secret() -> bytes:
    return settings.SECRET_KEY.encode("utf-8")


def _signature(path: str, exp: int) -> str:
    """HMAC-SHA256 over (domain, path, exp). NUL-joined so fields can't blur."""
    msg = b"\x00".join([_DOMAIN, path.encode("utf-8"), str(exp).encode("ascii")])
    return hmac.new(_secret(), msg, sha256).hexdigest()


def _bucketed_exp(now: int, ttl: int) -> int:
    """Round the expiry up to a window boundary so every `now` within a window
    maps to the same exp → an identical (cacheable) URL. Effective validity for a
    URL minted at `now` is therefore in the half-open range (ttl, ttl + _WINDOW]."""
    window_start = now - (now % _WINDOW)
    return window_start + _WINDOW + ttl


def sign_media_url(url, now=None, ttl: int = DEFAULT_TTL):
    """Append a signed `exp`/`token` query to an /uploads URL. Idempotent.

    URLs that are not /uploads paths (YouTube/Vimeo embeds, external links,
    empty/None) are returned unchanged, so this is safe to call on any resource
    or thumbnail URL without inspecting it first.
    """
    if not url or not url.startswith(UPLOADS_PREFIX):
        return url
    if "token=" in url:  # already signed — stay idempotent, never double-sign
        return url
    if now is None:
        now = int(time.time())
    exp = _bucketed_exp(now, ttl)
    sig = _signature(url, exp)
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}exp={exp}&token={sig}"


def verify_media_token(path: str, token, exp, now=None) -> bool:
    """True iff `token` is a valid, unexpired signature for `path`.

    `path` must be the exact URL path that was signed (e.g. "/uploads/abc.pdf").
    Uses a constant-time comparison to avoid signature-timing leaks.
    """
    if not token or not exp:
        return False
    try:
        exp_i = int(exp)
    except (TypeError, ValueError):
        return False
    if now is None:
        now = int(time.time())
    if exp_i < now:
        return False
    expected = _signature(path, exp_i)
    return hmac.compare_digest(expected, str(token))
