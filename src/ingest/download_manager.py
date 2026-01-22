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
                    
                    # Find the extracted JSON file
                    json_files = list(self.raw_dir.glob("*.json"))
                    if json_files:
                        # Use the first JSON file found
                        extracted_file = json_files[0]
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
                    
                    # Delete ZIP after extraction
                    try:
                        temp_zip.unlink()
                    except Exception as e:
                        logger.warning(f"Could not delete {temp_zip}: {e}")

                size_bytes = file_path.stat().st_size
                sha256 = self.calculate_sha256(file_path)
                
                logger.info(f"✓ Downloaded {filename}: {size_bytes} bytes")
                
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
        manifest['last_updated'] = datetime.utcnow().isoformat()
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
        
        # CAR data model files - try various URL formats
        base_urls = [
            'https://raw.githubusercontent.com/mitre-attack/car/master/data_model',
            'https://raw.githubusercontent.com/mitre-attack/car/main/data_model'
        ]
        
        # Common CAR JSON files
        files = [
            'CAR_analytic_objects.json',
            'CAR_analytic_rules.json'
        ]
        
        for base_url in base_urls:
            for filename in files:
                url = f"{base_url}/{filename}"
                try:
                    file_meta = self.download_file(url, filename, extract_zip=False)
                    if file_meta:
                        files_metadata.append(file_meta)
                        break  # File found, stop trying other base URLs for this file
                except Exception as e:
                    logger.debug(f"Failed to download {filename}: {e}")
                    continue
        
        if files_metadata:
            manifest['files'] = files_metadata
            manifest['source'] = 'https://github.com/mitre-attack/car'
            self.save_manifest(manifest)
        else:
            logger.warning("Could not download CAR files from any source")
        
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
        
        # SHIELD data from GitHub - try various URL formats
        base_urls = [
            'https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/master/_data',
            'https://raw.githubusercontent.com/MITRECND/mitrecnd.github.io/main/_data',
            'https://raw.githubusercontent.com/mitre-shield/mitre-shield.github.io/master/data'
        ]
        
        # Common SHIELD JSON files
        files = [
            'shield-deception-techniques.json',
            'shield-techniques.json',
            'shield.json'
        ]
        
        for base_url in base_urls:
            for filename in files:
                url = f"{base_url}/{filename}"
                try:
                    file_meta = self.download_file(url, filename, extract_zip=False)
                    if file_meta:
                        files_metadata.append(file_meta)
                        break
                except Exception as e:
                    logger.debug(f"Failed to download {filename} from {base_url}: {e}")
                    continue
            if files_metadata:
                break
        
        if files_metadata:
            manifest['files'] = files_metadata
            manifest['source'] = 'https://github.com/MITRECND/mitrecnd.github.io'
            self.save_manifest(manifest)
        else:
            logger.warning("Could not download SHIELD files from any source")
        
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
        
        # ENGAGE data from GitHub - try various URL formats and paths
        base_urls = [
            'https://raw.githubusercontent.com/mitre/engage/main/Data/json',
            'https://raw.githubusercontent.com/mitre/engage/master/Data/json'
        ]
        
        # Common ENGAGE files
        files = [
            'engage-objects.json',
            'engage-objects-detailed.json',
            'engage-datasets.json',
            'engage.json'
        ]
        
        for base_url in base_urls:
            for filename in files:
                url = f"{base_url}/{filename}"
                try:
                    file_meta = self.download_file(url, filename, extract_zip=False)
                    if file_meta:
                        files_metadata.append(file_meta)
                        break
                except Exception as e:
                    logger.debug(f"Failed to download {filename} from {base_url}: {e}")
                    continue
            if files_metadata:
                break
        
        if files_metadata:
            manifest['files'] = files_metadata
            manifest['source'] = 'https://github.com/mitre/engage'
            self.save_manifest(manifest)
        else:
            logger.warning("Could not download ENGAGE files from any source")
        
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

    def run(self) -> Dict:
        """Execute all downloads."""
        logger.info("=" * 70)
        logger.info("KGCS Daily Download Pipeline Starting")
        logger.info("=" * 70)
        
        start_time = datetime.now()
        
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
    summary = pipeline.run()
    
    # Exit with error if any download failed
    failed = [r for r in summary['results'] if r.get('status') == 'error']
    if failed:
        logger.error(f"Pipeline completed with {len(failed)} errors")
        return 1
    
    logger.info("Pipeline completed successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())
