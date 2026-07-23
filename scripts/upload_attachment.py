#!/usr/bin/env python3
import argparse
import hashlib
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
ALLOWED_DOMAIN_SUFFIXES = (".backlog.com", ".backlog.jp", ".backlogtool.com")


class AttachmentError(RuntimeError):
    pass


def _is_sensitive_name(name: str) -> bool:
    normalized = name.replace("\\", "/").lower()
    parts = [part for part in normalized.split("/") if part]
    base = parts[-1] if parts else normalized
    if normalized.startswith("/") or ".." in parts:
        return True
    if base == ".env" or base.startswith(".env."):
        return True
    if base in {
        "auth.json",
        "credentials.json",
        "service-account.json",
        "id_rsa",
        "id_ed25519",
    }:
        return True
    if base.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    return bool(re.search(r"(^|[._-])(secret|api[-_]?key)([._-]|$)", base))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_file(file_path: str | Path) -> dict:
    candidate = Path(file_path).expanduser()
    if candidate.is_symlink():
        raise AttachmentError("symlink attachments are not allowed")
    path = candidate.resolve(strict=True)
    if not path.is_file():
        raise AttachmentError("attachment path is not a regular file")
    if _is_sensitive_name(path.name):
        raise AttachmentError("sensitive attachment filename is blocked")
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise AttachmentError(
            "attachment exceeds the 10 MiB safety ceiling; "
            "the Backlog plan may impose a lower limit"
        )

    members: list[str] = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            members = sorted(info.filename for info in archive.infolist())
        blocked = [name for name in members if _is_sensitive_name(name)]
        if blocked:
            raise AttachmentError(
                "sensitive ZIP member is blocked: " + ", ".join(blocked)
            )

    mime_type = mimetypes.guess_type(path.name)[0]
    return {
        "path": str(path),
        "name": path.name,
        "mime_type": mime_type or "application/octet-stream",
        "size": size,
        "sha256": _sha256(path),
        "zip_members": members,
    }


def require_digest(file_path: str | Path, expected_sha256: str) -> dict:
    metadata = inspect_file(file_path)
    if metadata["sha256"] != expected_sha256.lower():
        raise AttachmentError(
            "file SHA-256 changed after approval; inspect and approve again"
        )
    return metadata


def build_multipart(
    filename: str, data: bytes, mime_type: str, boundary: str
) -> tuple[bytes, str]:
    safe_name = filename.replace("\\", "_").replace('"', "_")
    prefix = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; '
        f'filename="{safe_name}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode()
    suffix = f"\r\n--{boundary}--\r\n".encode()
    return prefix + data + suffix, f"multipart/form-data; boundary={boundary}"


def _validated_domain(value: str) -> str:
    domain = value.strip().lower().rstrip(".")
    if "://" in domain or "/" in domain:
        raise AttachmentError("BACKLOG_DOMAIN must be a hostname")
    if not re.fullmatch(r"[a-z0-9.-]+", domain):
        raise AttachmentError("BACKLOG_DOMAIN contains invalid characters")
    if not domain.endswith(ALLOWED_DOMAIN_SUFFIXES):
        raise AttachmentError("BACKLOG_DOMAIN is not a supported Backlog host")
    return domain


def upload_file(file_path: str | Path, expected_sha256: str) -> dict:
    metadata = require_digest(file_path, expected_sha256)
    domain = _validated_domain(os.environ.get("BACKLOG_DOMAIN", ""))
    api_key = os.environ.get("BACKLOG_API_KEY", "")
    if not api_key:
        raise AttachmentError("BACKLOG_API_KEY is not set")

    data = Path(metadata["path"]).read_bytes()
    boundary = "codex-" + uuid.uuid4().hex
    body, content_type = build_multipart(
        metadata["name"], data, metadata["mime_type"], boundary
    )
    url = (
        f"https://{domain}/api/v2/space/attachment?apiKey="
        + urllib.parse.quote(api_key, safe="")
    )
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": content_type, "Content-Length": str(len(body))},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise AttachmentError(
            f"Backlog upload failed with HTTP {error.code}"
        ) from None
    except urllib.error.URLError:
        raise AttachmentError("Backlog upload failed with a network error") from None
    return {"id": result["id"], "name": result["name"], "size": result["size"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("file")
    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("file")
    upload_parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()

    try:
        result = (
            inspect_file(args.file)
            if args.command == "inspect"
            else upload_file(args.file, args.expected_sha256)
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (AttachmentError, OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"attachment error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
