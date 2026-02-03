# Daily Download Pipeline - Implementation Guide

**Date:** January 22, 2026  
**Status:** ✅ Framework complete, Ready for scheduling

## Overview

A local daily download pipeline that fetches raw data files from all 9 security standards (NVD, MITRE) and stores them in `data/{standard}/raw/` with automatic checksums, versioning, and manifests.

## Architecture

```text
src/ingest/download_manager.py
├─ StandardDownloader (base class)
│  ├─ NVDCPEDownloader        (15 chunks)
│  ├─ NVDCPEMatchDownloader   (55 chunks)
│  ├─ NVDCVEDownloader        (25 year files)
│  ├─ MITRECWEDownloader      (XML)
│  ├─ MITRECAPECDownloader    (XML)
│  ├─ MITREATTACKDownloader   (3 STIX bundles)
│  ├─ MITRED3FENDDownloader   (JSON)
│  ├─ MITRECARDownloader      (YAML/JSON)
│  ├─ MITRESHIELDDownloader   (JSON)
│  └─ MITREENGAGEDownloader   (JSON)
└─ DownloadPipeline (orchestrator)
```

## Features

✅ **Automatic Checksums** — SHA256 for each file  
✅ **Manifest Tracking** — JSON metadata per standard  
✅ **Retry Logic** — 3 attempts with exponential backoff  
✅ **Resumable Downloads** — Skips already-downloaded files  
✅ **Detailed Logging** — `logs/download_manager.log`  
✅ **Summary Report** — `logs/download_summary.json`  

## Usage

### Run Once (Test)

```bash
cd e:\DEVEL\LAIA\KGCS
python -m src.ingest.download_manager
```

Output:

```text
logs/
├─ download_manager.log         (verbose logs)
└─ download_summary.json        (high-level report)

data/
├─ cpe/
│  ├─ raw/
│  │  ├─ nvdcpe-2.0-chunk-00001.json
│  │  ├─ ... (15 total CPE chunks)
│  │  ├─ nvdcpematch-2.0-chunk-00001.json
│  │  ├─ ... (55 total CPEMatch chunks)
│  │  └─ manifest.json    ← Metadata with checksums
│  └─ manifest.json       ← Summary
├─ cve/
│  ├─ raw/
│  │  ├─ nvdcve-2.0-2002.json
│  │  ├─ ... (25 year files)
│  │  └─ manifest.json
├─ cwe/, capec/, attack/, d3fend/, car/, shield/, engage/
│  └─ ... (same pattern)
```

### Manifest Example

**File:** `data/cpe/manifest.json`

```json
{
  "files": [
    {
      "filename": "nvdcpe-2.0-chunk-00001.json",
      "size_bytes": 52500000,
      "sha256": "abc123...",
      "url": "https://nvd.nist.gov/feeds/json/cpe/2.0/nvdcpe-2.0/nvdcpe-2.0-chunk-00001.json",
      "status": "success"
    }
  ],
  "cpematch_files": [
    {
      "filename": "nvdcpematch-2.0-chunk-00001.json",
      "size_bytes": 52500000,
      "sha256": "def456...",
      "url": "https://nvd.nist.gov/feeds/json/cpematch/2.0/nvdcpematch-2.0/nvdcpematch-2.0-chunk-00001.json",
      "status": "success"
    }
  ],
  "source": "https://nvd.nist.gov/feeds/json/cpe/2.0/nvdcpe-2.0/",
  "last_updated": "2026-01-22T16:30:00.000000"
}
```

## Data Flow

```text
NVD API / MITRE GitHub
    ↓
download_manager.py
    ├─ Calculate SHA256
    ├─ Check if already exists
    ├─ Retry up to 3 times
    ├─ Log success/failure
    └─ Update manifest
    ↓
data/{standard}/raw/
    ├─ Raw JSON files (native format)
    ├─ manifest.json (metadata + checksums)
    └─ manifest-history/ (daily snapshots)
```

## Next Steps

### 1. Schedule Daily Execution (Windows Task Scheduler)

Create task to run at 2 AM daily:

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute 'python' -Argument '-m src.ingest.download_manager' -WorkingDirectory 'e:\DEVEL\LAIA\KGCS'
$trigger = New-ScheduledTaskTrigger -Daily -At '2:00 AM'
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME
Register-ScheduledTask -TaskName 'KGCS-Daily-Download' -Action $action -Trigger $trigger -Principal $principal
```

Or use cron on Linux:

```bash
# Crontab entry (run at 2 AM daily)
0 2 * * * cd /path/to/KGCS && python -m src.ingest.download_manager
```

### 2. Add Monitoring (Optional)

```python
# After download completes, check:
- File sizes haven't changed unexpectedly
- No zero-byte files
- Checksums match (if re-downloaded)
- Send email/Slack alert on errors
```

### 3. Migrate to Cloud (Later)

Once local pipeline is stable, extend with:

```python
# src/ingest/storage_sync.py
- Compress files with gzip
- Upload to Azure Blob Storage
- Enable versioning for daily snapshots
- Keep manifests for audit trail
```

## Performance Estimates

| Standard | Files | Size | Est. Time |
| -------- | ----- | ---- | --------- |
| CPE | 15 | 709 MB | 8 min |
| CPEMatch | 55 | 2.7 GB | 30 min |
| CVE | 25 | 1.9 GB | 21 min |
| CWE | 1 | ~5 MB | <1 min |
| CAPEC | 1 | ~4 MB | <1 min |
| ATT&CK | 3 | ~50 MB | 1 min |
| D3FEND | 6 | ~40 MB | 1 min |
| CAR | 1 | ~1 MB | <1 min |
| SHIELD | 1 | ~2 MB | <1 min |
| ENGAGE | 1 | ~1 MB | <1 min |
| **TOTAL** | **109** | **~5.4 GB** | **~63 min** |

> *Includes 3x retry attempts (only on failures)*

## Error Handling

### Retry Logic

- **Attempt 1-2:** Exponential backoff (1s, 2s)
- **Attempt 3:** Final attempt
- **On Failure:** Logged to `logs/download_manager.log`
- **Exit Code:** 1 if any standard fails; 0 if all succeed

### Alert Conditions

- Missing files (zero-byte)
- Hash mismatches
- Network timeouts
- HTTP 404/403 errors
- Disk full errors

## Testing

### Run in Test Mode (Single Standard)

```python
# Modify download_manager.py temporarily:
pipeline = DownloadPipeline()
downloader = NVDCVEDownloader()  # Test just CVE
result = downloader.download()
print(json.dumps(result, indent=2))
```

### Verify Downloaded Files

```bash
cd data/cpe/raw
ls -lh nvdcpe-2.0-chunk-00001.json  # Check size
sha256sum nvdcpe-2.0-chunk-00001.json  # Verify checksum
```

Compare with manifest:

```bash
python -c "import json; m=json.load(open('../manifest.json')); print([f['sha256'] for f in m['files']][0])"
```

## Troubleshooting

### 404 Error on Files

**Cause:** URLs may have changed or NVD API updated  
**Fix:** Update URLs in respective downloader class

### Timeout Errors

**Cause:** Slow network or large file  
**Fix:** Increase timeout in `download_file()` method (default: 30s)

### Disk Space Issues

**Cause:** Raw data is ~5.4 GB  
**Fix:** Ensure `e:\DEVEL\LAIA\KGCS` has at least 10 GB free

### Manifest Not Updating

**Cause:** File already exists (resumable behavior)  
**Fix:** Delete `data/{standard}/raw/` and re-run

## Files Created

- ✅ `src/ingest/download_manager.py` — Main download orchestrator
- ✅ `logs/` directory — For logging
- ✅ `data/{standard}/raw/` — Storage directories (auto-created)

## Future Enhancements

1. **Parallel Downloads** — Download multiple standards simultaneously
2. **Delta Updates** — Only download changed files
3. **Cloud Sync** — Automatically upload to Azure/AWS
4. **Compression** — GZ compress before storage
5. **Notifications** — Email alerts on failures
6. **Retention** — Delete old snapshots (keep last 30 days)
7. **Validation** — Check file integrity post-download

## References

- **NVD API:** <https://nvd.nist.gov/developers/vulnerabilities>
- **NVD Feeds:** <https://nvd.nist.gov/feeds>
- **MITRE ATT&CK:** <https://github.com/mitre-attack/attack-stix-data>
- **MITRE CWE:** <https://cwe.mitre.org/data/downloads/>
- **MITRE CAPEC:** <https://capec.mitre.org/>
- **MITRE D3FEND:** <https://d3fend.mitre.org/>
