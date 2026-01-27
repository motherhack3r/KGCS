"""
Downloader for cybersecurity standards raw files
Downloads files from MITRE and NIST sources
"""

import logging
import asyncio
import os
import argparse
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import aiohttp
import random
import json
import mimetypes
import hashlib
import zipfile
from urllib.parse import urlparse

from src.ingest.ingest_config import APIEndpoints, ETLConfig

# On Windows avoid Proactor shutdown issues by using the SelectorEventLoopPolicy
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StandardsDownloader:
    """Downloads raw files from cybersecurity standards sources"""
    
    def __init__(self, output_dir: str = "./data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        # Optionally use GITHUB_TOKEN to increase GitHub API rate limits
        # Base headers include a User-Agent to satisfy endpoints like NVD
        headers = {"User-Agent": "metadata-downloader/1.0"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        # Use a larger total timeout to support very large downloads (CPE match, CVE archives)
        timeout = aiohttp.ClientTimeout(total=600)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run(self, cve_start_year: int = 2002, cve_end_year: Optional[int] = None):
        """Execute downloads for all standards"""
        logger.info("Starting cybersecurity standards download")
        
        try:
            tasks = [
                self.download_mitre_attack(),
                self.download_mitre_capec(),
                self.download_mitre_d3fend(),
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("Download completed")
        except Exception as e:
            logger.error(f"Download failed: {str(e)}", exc_info=True)
            raise
    
    async def download_file(self, url: str, output_path: Path, standard: str = "", headers: Optional[dict] = None) -> bool:
        """Download a single file from URL"""
        if self.session is None:
            raise RuntimeError("Session not initialized. Use 'async with StandardsDownloader()' context manager.")
        max_attempts = 5
        attempt = 0
        base_backoff = 1.0

        while attempt < max_attempts:
            attempt += 1
            try:
                logger.info(f"Downloading: {url} (attempt {attempt})")
                # Default Accept to */* so servers like NVD respond correctly
                req_headers = dict(headers or {})
                req_headers.setdefault("Accept", "*/*")

                # Check for an existing partial file to resume
                existing_size = 0
                if output_path.exists():
                    try:
                        existing_size = output_path.stat().st_size
                    except Exception:
                        existing_size = 0

                # If we have a partial file, probe via HEAD to decide resume vs skip vs redownload
                will_resume = False
                if existing_size > 0:
                    try:
                        async with self.session.head(url, headers={"Accept": "*/*"}) as head_resp:
                            accept_ranges = head_resp.headers.get('Accept-Ranges', '').lower()
                            content_length = head_resp.headers.get('Content-Length')
                            # If server reported a length, compare to our existing file
                            if content_length is not None:
                                try:
                                    remote_len = int(content_length)
                                except Exception:
                                    remote_len = None
                            else:
                                remote_len = None

                            # If sizes match, assume file complete and skip
                            if remote_len is not None and existing_size == remote_len:
                                logger.info(f"File already complete, skipping download: {output_path}")
                                # Ensure metadata exists/updated
                                try:
                                    # compute sha256 if missing
                                    if output_path.exists():
                                        h = hashlib.sha256()
                                        with open(output_path, 'rb') as exf:
                                            for chunk in iter(lambda: exf.read(64 * 1024), b''):
                                                h.update(chunk)
                                        self._update_metadata(output_path.parent, output_path.name, url,
                                                              size_bytes=existing_size,
                                                              content_type=head_resp.headers.get('Content-Type'),
                                                              last_modified=head_resp.headers.get('Last-Modified'),
                                                              etag=head_resp.headers.get('ETag'),
                                                              sha256=h.hexdigest())
                                except Exception:
                                    logger.exception("Failed to update metadata for existing complete file %s", output_path)
                                # Skip download
                                return True

                            # If local file is larger than remote, remove it and re-download
                            if remote_len is not None and existing_size > remote_len:
                                logger.warning(f"Local file larger than remote; removing and re-downloading: {output_path}")
                                try:
                                    output_path.unlink()
                                except Exception:
                                    logger.exception("Failed to remove oversized file %s", output_path)
                                existing_size = 0

                            # Otherwise if remote supports ranges, request resume
                            if 'bytes' in accept_ranges and (remote_len is None or existing_size < (remote_len or 0)):
                                req_headers['Range'] = f'bytes={existing_size}-'
                                will_resume = True
                            # If HEAD returned but no ranges supported, will do full GET
                    except Exception:
                        # HEAD failed; don't assume resume works — fall back to full GET
                        logger.debug("HEAD probe failed for %s; will attempt full GET", url)

                async with self.session.get(url, headers=req_headers) as response:
                    # Accept 200 OK (fresh download) or 206 Partial Content (resume)
                    if response.status in (200, 206):
                        # Decide file open mode
                        append_mode = (response.status == 206 and existing_size > 0)
                        mode = 'ab' if append_mode else 'wb'

                        # Prepare hasher: if resuming, incorporate existing bytes
                        hasher = hashlib.sha256()
                        if append_mode:
                            try:
                                with open(output_path, 'rb') as exf:
                                    for chunk in iter(lambda: exf.read(64 * 1024), b''):
                                        hasher.update(chunk)
                            except Exception:
                                # If reading existing file fails, fall back to full rewrite
                                hasher = hashlib.sha256()
                                mode = 'wb'

                        # Stream response to disk
                        with open(output_path, mode) as f:
                            async for chunk in response.content.iter_chunked(64 * 1024):
                                if chunk:
                                    f.write(chunk)
                                    try:
                                        hasher.update(chunk)
                                    except Exception:
                                        pass

                        # After successful write, collect metadata and persist
                        try:
                            size = output_path.stat().st_size
                        except Exception:
                            size = None

                        content_type = response.headers.get('Content-Type')
                        last_modified = response.headers.get('Last-Modified')
                        etag = response.headers.get('ETag')

                        sha256 = None
                        try:
                            sha256 = hasher.hexdigest()
                        except Exception:
                            sha256 = None

                        # Update per-folder metadata.json (include etag + sha256)
                        try:
                            self._update_metadata(output_path.parent, output_path.name, url,
                                                  size_bytes=size,
                                                  content_type=content_type,
                                                  last_modified=last_modified,
                                                  etag=etag,
                                                  sha256=sha256)
                        except Exception:
                            logger.exception("Failed to update metadata for %s", output_path)

                        # If this is a ZIP for one of the expected standards, extract members
                        try:
                            suffix = output_path.suffix.lower()
                            std = (standard or '').lower()
                            if suffix == '.zip' and any(k in std for k in ('cve', 'cpe', 'cpematch', 'cwe')):
                                logger.info(f"Extracting ZIP contents: {output_path}")
                                # Offload extraction to a thread to avoid blocking the event loop
                                await asyncio.to_thread(self._extract_zip_and_update_metadata, output_path, url, standard)
                        except Exception:
                            logger.exception("Failed to extract ZIP %s", output_path)

                        logger.info(f"Saved: {output_path}")
                        return True
                    else:
                        # Treat some response codes as transient
                        if response.status in (429, 500, 502, 503, 504):
                            raise RuntimeError(f"Transient HTTP {response.status}")
                        logger.warning(f"✗ HTTP {response.status}: {url}")
                        return False
            except Exception as e:
                logger.warning(f"Download attempt {attempt} failed for {url}: {e}")
                if attempt >= max_attempts:
                    logger.error(f"✗ Failed to download after {attempt} attempts: {url}")
                    return False
                # Exponential backoff with jitter
                sleep_for = base_backoff * (2 ** (attempt - 1))
                sleep_for = sleep_for + random.random() * 0.5
                logger.info(f"Retrying in {sleep_for:.1f}s...")
                await asyncio.sleep(sleep_for)
                continue
        # All attempts exhausted
        return False
    
    # MITRE ATT&CK
    async def download_mitre_attack(self):
        """Download MITRE ATT&CK files"""
        logger.info("Processing MITRE ATT&CK")
        attack_dir = self.output_dir / "attack" / "raw"
        attack_dir.mkdir(parents=True, exist_ok=True)
        
        domains = {
            0: "enterprise-attack.json",
            1: "ics-attack.json",
            2: "mobile-attack.json",
            3: "pre-attack.json"
        }
        
        tasks = []
        for idx, url in enumerate(APIEndpoints.MITRE_ATTACK):
            output_file = attack_dir / domains[idx]
            tasks.append(self.download_file(url, output_file, "MITRE ATT&CK"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"MITRE ATT&CK: {sum(1 for r in results if r is True)}/{len(results)} files downloaded")
    
    # MITRE CAPEC
    async def download_mitre_capec(self):
        """Download MITRE CAPEC file"""
        logger.info("Processing MITRE CAPEC")
        capec_dir = self.output_dir / "capec" / "raw"
        capec_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = capec_dir / "capec_latest.xml"
        await self.download_file(APIEndpoints.MITRE_CAPEC, output_file, "MITRE CAPEC")
    
    # MITRE D3FEND
    async def download_mitre_d3fend(self):
        """Download MITRE D3FEND ontology files (json/owl/ttl)"""
        logger.info("Processing MITRE D3FEND")
        d3_dir = self.output_dir / "d3fend" / "raw"
        d3_dir.mkdir(parents=True, exist_ok=True)

        base = APIEndpoints.MITRE_D3FEND_BASE
        files = getattr(APIEndpoints, 'MITRE_D3FEND_FILES', [])
        if not files:
            logger.warning("No D3FEND files configured")
            return

        tasks = []
        for fname in files:
            url = f"{base}{fname}"
            output_file = d3_dir / fname
            tasks.append(self.download_file(url, output_file, "MITRE D3FEND"))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"MITRE D3FEND: {sum(1 for r in results if r is True)}/{len(results)} files downloaded")

    def _extract_zip_and_update_metadata(self, zip_path: Path, source_url: str, standard: str):
        """Extract ZIP archive members into the same folder and add metadata for each extracted file.

        This runs synchronously and is intended to be executed via `asyncio.to_thread()`.
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    member_name = Path(info.filename)
                    # Prevent path traversal
                    if '..' in member_name.parts or member_name.is_absolute():
                        logger.warning("Skipping suspicious zip member: %s", info.filename)
                        continue

                    target = zip_path.parent / member_name
                    target.parent.mkdir(parents=True, exist_ok=True)

                    # Extract file content and write (use read to compute hash without reopening)
                    with zf.open(info) as src, open(target, 'wb') as dst:
                        data = src.read()
                        dst.write(data)

                    # Compute metadata for extracted file
                    try:
                        h = hashlib.sha256()
                        h.update(data)
                        sha256 = h.hexdigest()
                    except Exception:
                        sha256 = None

                    try:
                        size = target.stat().st_size
                    except Exception:
                        size = None

                    content_type = mimetypes.guess_type(target.name)[0]

                    # Use a composite URL to indicate the member inside the ZIP
                    member_url = f"{source_url}!{info.filename}"

                    try:
                        self._update_metadata(target.parent, target.name, member_url,
                                              size_bytes=size,
                                              content_type=content_type,
                                              last_modified=None,
                                              etag=None,
                                              sha256=sha256)
                    except Exception:
                        logger.exception("Failed to update metadata for extracted member %s", target)
        except Exception:
            logger.exception("Failed to extract ZIP file: %s", zip_path)

    def _update_metadata(self, directory: Path, filename: str, url: str, *, size_bytes: Optional[int] = None, content_type: Optional[str] = None, last_modified: Optional[str] = None, etag: Optional[str] = None, sha256: Optional[str] = None):
        """Create or update metadata.json in `directory` recording file metadata.

        Schema:
        {
          "generated_at": "2026-01-23T00:00:00Z",
          "files": {
             "name.yaml": {
                 "url": "...",
                 "source": "raw.githubusercontent.com",
                 "saved_at": "2026-01-23T...Z",
                 "last_modified": "...",
                 "size_bytes": 12345,
                 "content_type": "application/x-yaml"
             }
          }
        }
        """
        directory.mkdir(parents=True, exist_ok=True)
        meta_path = directory / "metadata.json"
        now = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

        # Load existing metadata if present
        data = {"generated_at": now, "files": {}}
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
            except Exception:
                # If load fails, start fresh but keep going
                data = {"generated_at": now, "files": {}}

        # Determine source host for convenience
        try:
            source = urlparse(url).netloc
        except Exception:
            source = None

        entry = {
            "url": url,
            "source": source,
            "saved_at": now,
            "last_modified": last_modified,
            "size_bytes": size_bytes,
            "content_type": content_type,
            "etag": etag,
            "sha256": sha256
        }

        # Normalize missing content_type using mimetypes
        if not entry.get('content_type'):
            entry['content_type'] = mimetypes.guess_type(filename)[0]

        # Insert/replace entry
        files = data.get('files') or {}
        files[filename] = entry
        data['files'] = files
        data['generated_at'] = now

        # Atomic write
        tmp = meta_path.with_suffix('.json.tmp')
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        tmp.replace(meta_path)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Download raw cybersecurity standards data")
    parser.add_argument("--output", "-o", default="./data", help="Output directory")
    parser.add_argument("--cve-start", type=int, default=2020, help="CVE start year")
    parser.add_argument("--cve-end", type=int, default=None, help="CVE end year (inclusive)")
    args = parser.parse_args()

    async with StandardsDownloader(output_dir=args.output) as downloader:
        await downloader.run(cve_start_year=args.cve_start, cve_end_year=args.cve_end)


if __name__ == "__main__":
    asyncio.run(main())
