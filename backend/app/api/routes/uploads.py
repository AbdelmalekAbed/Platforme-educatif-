"""Authenticated file serving for /uploads (PDFs, videos, course thumbnails).

Replaces the old unauthenticated `StaticFiles` mount. A file is served only when
the request carries a valid signed token minted by
`app.core.security.media_tokens` on a code path that requires an authenticated
user. Without a valid token the request is rejected with 403 — guessing or
leaking a raw /uploads/<uuid>_x.pdf URL no longer grants access, even to a
logged-out visitor.

Behaviour-preserving notes vs. the old mount:
  - Files are streamed via Starlette `FileResponse` (same engine `StaticFiles`
    used), so media type is inferred from the extension and PDFs/videos still
    render inline in the browser.
  - This Starlette version's `FileResponse` does not implement HTTP Range, which
    matches the previous `StaticFiles` behaviour (no regression in seeking).
"""
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status
from starlette.responses import FileResponse

from app.core.security.media_tokens import verify_media_token

router = APIRouter(tags=["Uploads"])

# backend/app/api/routes/uploads.py -> parents[3] == backend/  (matches content.py
# and main.py, which both resolve the upload dir to backend/uploads).
UPLOAD_DIR = (Path(__file__).resolve().parents[3] / "uploads").resolve()

# Long cache: files are content-addressed (name = random hash) so a given signed
# URL never changes its bytes. `private` (not `public`) because the content is now
# access-controlled and must not be retained by shared/proxy caches.
_CACHE_CONTROL = "private, max-age=31536000, immutable"


@router.get("/uploads/{file_path:path}")
async def serve_upload(file_path: str, request: Request):
    url_path = f"/uploads/{file_path}"
    if not verify_media_token(
        url_path,
        request.query_params.get("token"),
        request.query_params.get("exp"),
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lien de fichier invalide ou expiré",
        )

    # Defense in depth: a valid token already pins the exact path, but make sure
    # the resolved target stays inside UPLOAD_DIR (block traversal / symlink escape).
    target = (UPLOAD_DIR / file_path).resolve()
    if not target.is_relative_to(UPLOAD_DIR) or not target.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier introuvable",
        )

    response = FileResponse(str(target))
    response.headers["Cache-Control"] = _CACHE_CONTROL
    return response
