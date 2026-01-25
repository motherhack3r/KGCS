"""Download Manager: Fetch all security standards from authoritative sources.

Daily pipeline to download:
- NVD CPE/CVE data (JSON from NVD API or bulk files)
- CWE catalog (XML from MITRE)
- CAPEC/ATT&CK/D3FEND/CAR/SHIELD/ENGAGE (from MITRE/GitHub)

Saves to data/{standard}/raw/ with checksums, versioning, and manifests.
"""

import os
import sys
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import gzip
import importlib.util
import asyncio
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/download_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StandardDownloader(ABC):
    """Base class for downloading security standards."""

    def __init__(self, standard_name: str, base_dir: str = 'data'):
        self.standard_name = standard_name
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / standard_name / 'raw'
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.raw_dir.parent / 'manifest.json'

    def calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def download_file(self, url: str, filename: str, retries: int = 3, extract_zip: bool = False) -> Optional[Dict]:
        """Download a file with retry logic and optional ZIP extraction."""
        file_path = self.raw_dir / filename
        
        # Skip if already exists (for resumable downloads)
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            return {
                'filename': filename,
                'size_bytes': file_path.stat().st_size,
                'sha256': self.calculate_sha256(file_path),
                'url': url,
                'status': 'cached'
            }
        
        # If extracting ZIP, temporarily save with .zip extension
        temp_zip = self.raw_dir / f"{filename}.zip" if extract_zip else file_path

        for attempt in range(retries):
            try:
                logger.info(f"Downloading {url} (attempt {attempt + 1}/{retries})...")
                
                # Add User-Agent to avoid 403 errors
                req = Request(url, headers={'User-Agent': 'KGCS-DownloadManager/1.0'})
                
                # Download in chunks to handle large files and improve reliability
                with urlopen(req, timeout=60) as response:
                    chunk_size = 1024 * 1024  # 1 MB chunks
                    downloaded = 0
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(temp_zip, 'wb') as f:
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                logger.debug(f"Progress: {progress:.1f}% ({downloaded} / {total_size} bytes)")
                
                # Extract ZIP if needed
                if extract_zip:
                    import zipfile
                    logger.info(f"Extracting {temp_zip}...")
                    with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                        # Extract all files
                        zip_ref.extractall(self.raw_dir)
                    
                    # Find the extracted JSON or XML file
                    json_files = list(self.raw_dir.glob("*.json"))
                    xml_files = list(self.raw_dir.glob("*.xml"))
                    all_files = json_files + xml_files
                    
                    # Check for chunked directories (e.g., nvdcpe-2.0-chunks/)
                    chunk_dirs = list(self.raw_dir.glob("*-chunks"))
                    
                    if chunk_dirs:
                        # Handle chunked archives (like NVD CPE)
                        chunk_dir = chunk_dirs[0]
                        logger.info(f"Found chunked data directory: {chunk_dir.name}")
                        file_path = chunk_dir  # Use the chunk directory as the "file"
                    elif all_files:
                        # Use the first extracted file found
                        extracted_file = all_files[0]
                        # Only rename if it doesn't match expected filename
                        if extracted_file.name != filename and extracted_file.name.replace('.json', '') in filename:
                            try:
                                extracted_file.rename(self.raw_dir / filename)
                                file_path = self.raw_dir / filename
                            except Exception as e:
                                # If rename fails, use the extracted file as-is
                                logger.warning(f"Could not rename {extracted_file.name} to {filename}: {e}")
                                file_path = extracted_file
                        else:
                            file_path = extracted_file
                    else:
                        raise FileNotFoundError(f"No JSON/XML files found after extracting {temp_zip}")
                    
                    # Delete ZIP after extraction
                    try:
                        temp_zip.unlink()
                    except Exception as e:
                        logger.warning(f"Could not delete {temp_zip}: {e}")

                # Handle both files and directories (for chunked archives)
                if file_path.is_dir():
                    size_bytes = sum(f.stat().st_size for f in file_path.rglob('*') if f.is_file())
                    sha256 = 'chunked-archive'  # For directories, use a placeholder
                else:
                    size_bytes = file_path.stat().st_size
                    sha256 = self.calculate_sha256(file_path)
                
                logger.info(f"[OK] Downloaded {filename}: {size_bytes} bytes")
                
                return {
                    'filename': filename,
                    'size_bytes': size_bytes,
                    'sha256': sha256,
                    'url': url,
                    'status': 'success'
                }

            except (URLError, HTTPError, TimeoutError) as e:
                logger.warning(f"Download failed (attempt {attempt + 1}): {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to download {url} after {retries} attempts")
                    return {
                        'filename': filename,
                        'url': url,
                        'status': 'failed',
                        'error': str(e)
                    }
            except Exception as e:
                # Catch all other exceptions (including network errors)
                logger.warning(f"Download error (attempt {attempt + 1}): {type(e).__name__}: {e}")
                if attempt == retries - 1:
                    logger.error(f"Failed to download {url} after {retries} attempts: {e}")
                    return {
                        'filename': filename,
                        'url': url,
                        'status': 'failed',
                        'error': str(e)
                    }

    def load_manifest(self) -> Dict:
        """Load existing manifest."""
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r') as f:
                return json.load(f)
        return {'files': [], 'last_updated': None}

    def save_manifest(self, manifest: Dict) -> None:
        """Save manifest with metadata."""
        manifest['last_updated'] = datetime.now().isoformat()
        with open(self.manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved: {self.manifest_file}")

    @abstractmethod
    def download(self) -> Dict:
        """Download standard data. Subclasses implement this."""
        pass


class NVDCPEDownloader(StandardDownloader):
    """Download NVD CPE data (bulk ZIP file)."""

    def __init__(self):
        super().__init__('cpe')
        self.base_url = 'https://nvd.nist.gov/feeds/json/cpe/2.0'

    def download(self) -> Dict:
        """Download CPE bulk ZIP."""
        logger.info("Starting NVD CPE download...")
        
        manifest = self.load_manifest()
        filename = 'nvdcpe-2.0.json'
        url = f"{self.base_url}/nvdcpe-2.0.zip"
        
        file_meta = self.download_file(url, filename, extract_zip=True)
        
        if file_meta:
            manifest['files'] = [file_meta]
            manifest['source'] = 'https://nvd.nist.gov/feeds/json/cpe/2.0/'
            self.save_manifest(manifest)
        
        return {'standard': 'cpe', 'files': [file_meta] if file_meta else []}


class NVDCPEMatchDownloader(StandardDownloader):
    """Download NVD CPEMatch data (bulk ZIP file)."""

    def __init__(self):
        super().__init__('cpe')  # Save to same directory as CPE
        self.base_url = 'https://nvd.nist.gov/feeds/json/cpematch/2.0'

    def download(self) -> Dict:
        """Download CPEMatch bulk ZIP."""
        logger.info("Starting NVD CPEMatch download...")
        
        manifest = self.load_manifest()
        filename = 'nvdcpematch-2.0.json'
        url = f"{self.base_url}/nvdcpematch-2.0.zip"
        
        file_meta = self.download_file(url, filename, extract_zip=True)
        
        if file_meta:
            if 'cpematch_files' not in manifest:
                manifest['cpematch_files'] = []
            manifest['cpematch_files'] = [file_meta]
            manifest['source'] = 'https://nvd.nist.gov/feeds/json/cpematch/2.0/'
            self.save_manifest(manifest)
        
        return {'standard': 'cpematch', 'files': [file_meta] if file_meta else []}



class NVDCVEDownloader(StandardDownloader):
    """Download NVD CVE data (yearly ZIP files: 2002-2026)."""

    def __init__(self):
        super().__init__('cve')
        self.base_url = 'https://nvd.nist.gov/feeds/json/cve/2.0'

    def download(self) -> Dict:
        """Download all CVE yearly ZIP files."""
        logger.info("Starting NVD CVE download...")
        
        manifest = self.load_manifest()
        files_metadata = []
        
        # Download CVE for years 2002-2026
        for year in range(2002, 2027):
            filename = f"nvdcve-2.0-{year}.json"
            url = f"{self.base_url}/nvdcve-2.0-{year}.json.zip"
            
            file_meta = self.download_file(url, filename, extract_zip=True)
            if file_meta:
                files_metadata.append(file_meta)
        
        manifest['files'] = files_metadata
        manifest['source'] = 'https://nvd.nist.gov/feeds/json/cve/2.0/'
        self.save_manifest(manifest)
        
        return {'standard': 'cve', 'files': files_metadata}


class MITRECWEDownloader(StandardDownloader):
    """Download MITRE CWE catalog (XML)."""

    def __init__(self):
        super().__init__('cwe')

    def download(self) -> Dict:
        """Download CWE from MITRE."""
        logger.info("Starting MITRE CWE download...")
        
        # CWE provides XML format in ZIP
        url = 'https://cwe.mitre.org/data/xml/cwec_latest.xml.zip'
        filename = 'cwec_latest.xml'
        
        manifest = self.load_manifest()
        file_meta = self.download_file(url, filename, extract_zip=True)
        
        if file_meta:
            manifest['files'] = [file_meta]
            manifest['source'] = 'https://cwe.mitre.org/'
            self.save_manifest(manifest)
        
        return {'standard': 'cwe', 'files': [file_meta] if file_meta else []}


class MITRECAPECDownloader(StandardDownloader):
    """Download MITRE CAPEC attack patterns."""

    def __init__(self):
        super().__init__('capec')

    def download(self) -> Dict:
        """Download CAPEC from MITRE."""
        logger.info("Starting MITRE CAPEC download...")
        
        url = 'https://capec.mitre.org/data/xml/capec_latest.xml'
        filename = 'capec_latest.xml'
        
        manifest = self.load_manifest()
        file_meta = self.download_file(url, filename, extract_zip=False)
        
        if file_meta:
            manifest['files'] = [file_meta]
            manifest['source'] = 'https://capec.mitre.org/'
            self.save_manifest(manifest)
        
        return {'standard': 'capec', 'files': [file_meta] if file_meta else []}


class MITREATTACKDownloader(StandardDownloader):
    """Download ATT&CK from MITRE GitHub (JSON bundles)."""

    def __init__(self):
        super().__init__('attack')

    def download(self) -> Dict:
        """Download ATT&CK matrices from GitHub."""
        logger.info("Starting MITRE ATT&CK download...")
        
        manifest = self.load_manifest()
        files_metadata = []
        
        # Download enterprise, ics, mobile, and pre matrices
        matrices = ['enterprise-attack', 'ics-attack', 'mobile-attack', 'pre-attack']
        base_url = 'https://github.com/mitre/cti/raw/refs/heads/master'
        
        for matrix in matrices:
            filename = f"{matrix}.json"
            url = f"{base_url}/{matrix}/{filename}"
            
            file_meta = self.download_file(url, filename, extract_zip=False)
            if file_meta:
                files_metadata.append(file_meta)
        
        manifest['files'] = files_metadata
        manifest['source'] = 'https://github.com/mitre/cti'
        self.save_manifest(manifest)
        
        return {'standard': 'attack', 'files': files_metadata}


class MITRED3FENDDownloader(StandardDownloader):
    """Download MITRE D3FEND defenses."""

    def __init__(self):
        super().__init__('d3fend')

    def download(self) -> Dict:
        """Download D3FEND ontology from MITRE."""
        logger.info("Starting MITRE D3FEND download...")
        
        # Try D3FEND OWL ontology - various possible formats
        urls_to_try = [
            'https://d3fend.mitre.org/ontologies/d3fend.owl',
            'https://raw.githubusercontent.com/mitre-engenuity/d3fend/master/d3fend.owl',
            'https://d3fend.mitre.org/api/json/d3fend.json'
        ]
        
        manifest = self.load_manifest()
        file_meta = None
        
        for url in urls_to_try:
            try:
                filename = url.split('/')[-1]
                file_meta = self.download_file(url, filename, extract_zip=False)
                if file_meta:
                    break
            except Exception as e:
                logger.debug(f"Failed to download from {url}: {e}")
                continue
        
        if file_meta:
            manifest['files'] = [file_meta]
            manifest['source'] = 'https://d3fend.mitre.org/'
            self.save_manifest(manifest)
        else:
            logger.warning("Could not download D3FEND from any source")
        
        return {'standard': 'd3fend', 'files': [file_meta] if file_meta else []}


class MITRECARDownloader(StandardDownloader):
    """Download MITRE CAR analytics rules."""

    def __init__(self):
        super().__init__('car')

    def download(self) -> Dict:
        """Download CAR data model from MITRE GitHub."""
        logger.info("Starting MITRE CAR download...")
        
        manifest = self.load_manifest()
        files_metadata = []
        
        # Use GitHub API to list available YAML files
        api_url = 'https://api.github.com/repos/mitre-attack/car/contents/data_model'
        base_download_url = 'https://raw.githubusercontent.com/mitre-attack/car/refs/heads/master/data_model'
        
        try:
            # Fetch directory listing from GitHub API
            req = Request(api_url, headers={'User-Agent': 'KGCS-DownloadManager/1.0'})
            with urlopen(req, timeout=30) as response:
                files_list = json.loads(response.read().decode('utf-8'))
            
            # Filter for .yaml files and download them
            for item in files_list:
                if item.get('type') == 'file' and item.get('name', '').endswith('.yaml'):
                    filename = item['name']
                    url = f"{base_download_url}/{filename}"
                    try:
                        file_meta = self.download_file(url, filename, extract_zip=False)
                        if file_meta:
                            files_metadata.append(file_meta)
                    except Exception as e:
                        logger.debug(f"Could not download {filename}: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Could not fetch CAR file listing from GitHub API: {e}")
        
        if files_metadata:
            manifest['files'] = files_metadata
            manifest['source'] = 'https://github.com/mitre-attack/car/tree/master/data_model'
            self.save_manifest(manifest)
        else:
            logger.warning("Could not download any CAR files")
        
        return {'standard': 'car', 'files': files_metadata}
        
        manifest['files'] = files_metadata
        manifest['source'] = 'https://github.com/mitre-attack/car/tree/master/data_model'
        self.save_manifest(manifest)
        
        return {'standard': 'car', 'files': files_metadata}


class MITRESHIELDDownloader(StandardDownloader):
    """Download MITRE SHIELD defensive techniques."""

    def __init__(self):
        super().__init__('shield')

    def download(self) -> Dict:
        """Download SHIELD deception techniques from GitHub."""
        logger.info("Starting MITRE SHIELD download...")
        
        manifest = self.load_manifest()
        files_metadata = []
        # Prefer using the GitHub API to list files and download the canonical
        # raw URLs. This is more resilient than hard-coding raw paths.
        api_candidates = [
            ('https://api.github.com/repos/MITRECND/mitrecnd.github.io/contents/_data', 'https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/master/_data/'),
            ('https://api.github.com/repos/MITRECND/mitrecnd.github.io/contents/_data?ref=main', 'https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/refs/heads/main/_data/'),
            ('https://api.github.com/repos/mitre-shield/mitre-shield.github.io/contents/data', 'https://raw.githubusercontent.com/mitre-shield/mitre-shield.github.io/refs/heads/master/data/'),
        ]

        token = os.environ.get('GITHUB_TOKEN')
        headers = {'User-Agent': 'KGCS-DownloadManager/1.0'}
        if token:
            headers['Authorization'] = f'token {token}'

        tried_any = False
        for api_url, raw_base in api_candidates:
            try:
                req = Request(api_url, headers=headers)
                with urlopen(req, timeout=30) as resp:
                    files_list = json.loads(resp.read().decode('utf-8'))

                # Filter for .json files
                json_files = [f for f in files_list if f.get('type') == 'file' and f.get('name', '').endswith('.json')]
                if not json_files:
                    logger.debug(f'No JSON files listed at {api_url}')
                    continue

                tried_any = True
                for item in json_files:
                    filename = item.get('name')
                    # Use the API-provided download_url when present, otherwise construct raw URL
                    download_url = item.get('download_url') or f"{raw_base}{filename}"
                    try:
                        file_meta = self.download_file(download_url, filename, extract_zip=False)
                        if file_meta:
                            files_metadata.append(file_meta)
                    except Exception as e:
                        logger.debug(f'Failed to download {filename} from {download_url}: {e}')
                        continue

                if files_metadata:
                    manifest['files'] = files_metadata
                    manifest['source'] = api_url.split('/contents')[0]
                    self.save_manifest(manifest)
                    return {'standard': 'shield', 'files': files_metadata}
            except Exception as e:
                logger.debug(f'Failed to fetch SHIELD listing from {api_url}: {e}')
                continue

        if not tried_any:
            logger.warning('No SHIELD GitHub API endpoints available to try')
        else:
            logger.warning('Could not download any SHIELD files from GitHub API candidates')

        return {'standard': 'shield', 'files': files_metadata}


class MITREENGAGEDownloader(StandardDownloader):
    """Download MITRE ENGAGE recommendations."""

    def __init__(self):
        super().__init__('engage')

    def download(self) -> Dict:
        """Download ENGAGE from GitHub."""
        logger.info("Starting MITRE ENGAGE download...")
        manifest = self.load_manifest()
        files_metadata = []

        api_url = 'https://api.github.com/repos/mitre/engage/contents/Data/json'
        raw_base = 'https://raw.githubusercontent.com/mitre/engage/refs/heads/master/Data/json/'

        token = os.environ.get('GITHUB_TOKEN')
        headers = {'User-Agent': 'KGCS-DownloadManager/1.0'}
        if token:
            headers['Authorization'] = f'token {token}'

        try:
            req = Request(api_url, headers=headers)
            with urlopen(req, timeout=30) as resp:
                files_list = json.loads(resp.read().decode('utf-8'))

            json_files = [f for f in files_list if f.get('type') == 'file' and f.get('name', '').endswith('.json')]
            if not json_files:
                logger.warning('No ENGAGE JSON files found via GitHub API')
                return {'standard': 'engage', 'files': files_metadata}

            for item in json_files:
                filename = item.get('name')
                download_url = item.get('download_url') or f"{raw_base}{filename}"
                try:
                    file_meta = self.download_file(download_url, filename, extract_zip=False)
                    if file_meta:
                        files_metadata.append(file_meta)
                except Exception as e:
                    logger.debug(f'Failed to download {filename} from {download_url}: {e}')
                    continue

            if files_metadata:
                manifest['files'] = files_metadata
                manifest['source'] = 'https://github.com/mitre/engage'
                self.save_manifest(manifest)
            else:
                logger.warning('Could not download ENGAGE files from GitHub API')

        except Exception as e:
            logger.warning(f'Failed to fetch ENGAGE listing from GitHub API: {e}')

        return {'standard': 'engage', 'files': files_metadata}


class DownloadPipeline:
    """Orchestrate downloads for all standards."""

    def __init__(self, base_dir: str = 'data', skip_large_files: bool = False):
        self.base_dir = base_dir
        self.skip_large_files = skip_large_files
        self.downloaders = [
            NVDCPEDownloader() if not skip_large_files else None,
            NVDCPEMatchDownloader() if not skip_large_files else None,
            NVDCVEDownloader() if not skip_large_files else None,
            MITRECWEDownloader(),
            MITRECAPECDownloader(),
            MITREATTACKDownloader(),
            MITRED3FENDDownloader(),
            MITRECARDownloader(),
            MITRESHIELDDownloader(),
            MITREENGAGEDownloader(),
        ]
        # Filter out None values
        self.downloaders = [d for d in self.downloaders if d is not None]
        self.results = []

    async def run(self) -> Dict:
        """Execute all downloads: async MITRE standards first, then sync downloaders for others."""
        logger.info("=" * 70)
        logger.info("KGCS Daily Download Pipeline Starting")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        
        # 1. Run async downloader for MITRE standards (ATT&CK, CAPEC, D3FEND)
        try:
            # Add data-raw to path for import
            # StandardsDownloader is now in src/ingest/
            from src.ingest.downloader import StandardsDownloader as AsyncStandardsDownloader
            logger.info("Running async downloader for MITRE standards...")
            async with AsyncStandardsDownloader(output_dir=self.base_dir) as d:
                await d.run()
            
            # Filter out standards that async downloaded
            owned_by_async = {'attack', 'capec', 'd3fend'}
            self.downloaders = [d for d in self.downloaders if getattr(d, 'standard_name', None) not in owned_by_async]
            logger.info(f"Async downloader succeeded; remaining sync downloaders: {[d.standard_name for d in self.downloaders]}")
        except ImportError as e:
            logger.warning(f"Could not import async downloader: {e}; proceeding with sync-only")
        except Exception as e:
            logger.warning(f"Async downloader failed: {e}; proceeding with sync downloaders")
        
        # 2. Run sync downloaders for remaining standards (CPE, CVE, CWE, CAR, SHIELD, ENGAGE)
        for downloader in self.downloaders:
            try:
                result = downloader.download()
                self.results.append(result)
            except Exception as e:
                logger.error(f"Error downloading {downloader.standard_name}: {e}")
                self.results.append({
                    'standard': downloader.standard_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        for downloader in self.downloaders:
            try:
                result = downloader.download()
                self.results.append(result)
            except Exception as e:
                logger.error(f"Error downloading {downloader.standard_name}: {e}")
                self.results.append({
                    'standard': downloader.standard_name,
                    'status': 'error',
                    'error': str(e)
                })
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Save summary
        summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'results': self.results
        }
        
        summary_file = Path('logs/download_summary.json')
        summary_file.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("=" * 70)
        logger.info(f"Download pipeline completed in {duration:.1f} seconds")
        logger.info(f"Summary saved to {summary_file}")
        logger.info("=" * 70)
        
        return summary


def main():
    """Main entry point."""
    import sys
    os.makedirs('logs', exist_ok=True)
    
    # Check for command line argument to skip large files
    skip_large = '--skip-large' in sys.argv
    if skip_large:
        logger.info("Skipping large NVD files (CPE, CPEMatch, CVE)")
    
    pipeline = DownloadPipeline(skip_large_files=skip_large)
    asyncio.run(pipeline.run())
    
    # Exit with error if any download failed
    failed = [r for r in pipeline.results if r.get('status') == 'error']
    if failed:
        logger.error(f"Pipeline completed with {len(failed)} errors")
        return 1
    
    logger.info("Pipeline completed successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())
