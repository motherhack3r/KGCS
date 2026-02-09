<#
.SYNOPSIS
  Wrapper script to run the KGCS loader in a nodes-first then relationships-second flow.

.DESCRIPTION
  This PowerShell script calls `python src/etl/rdf_to_neo4j.py` with tuned defaults
  and captures stdout/stderr into timestamped log files under `logs/`.

  The script assumes you have activated the `metadata` conda env before running.

.PARAMETER TtlNodes
  Path to the nodes TTL (default: tmp/combined-nodes.ttl)

.PARAMETER TtlRels
  Path to the relationships TTL (default: tmp/combined-rels.ttl)

.PARAMETER DbVersion
  Version suffix for the database name (e.g. 2026-02-08)

.PARAMETER DryRun
  If set, perform only a dry-run estimation of counts.

.EXAMPLE
  .\scripts\load_to_neo4j.ps1 -DbVersion 2026-02-08
#>

param(
  [string]$TtlNodes = 'tmp/combined-nodes.ttl',
  [string]$TtlRels  = 'tmp/combined-rels.ttl',
  [string]$DbVersion = (Get-Date -Format yyyy-MM-dd),
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ScriptStart = Get-Date

$LogDir = Join-Path -Path (Get-Location) -ChildPath 'logs'
If (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

$ts = $ScriptStart.ToString('yyyyMMddTHHmmss')
$nodesLog = Join-Path $LogDir "load-nodes-$ts.log"
$relsLog = Join-Path $LogDir "load-rels-$ts.log"

Write-Host "Load wrapper starting at $ScriptStart"
Write-Host "Nodes TTL: $TtlNodes"; Write-Host "Rels TTL: $TtlRels"

if ($DryRun) {
  Write-Host "Running dry-run estimation..."
  $cmd = @(
    'python', 'src/etl/rdf_to_neo4j.py',
    '--ttl', $TtlNodes,
    '--chunk-size', '50000',
    '--fast-parse',
    '--dry-run',
    '--workers', '4',
    '--progress-newline'
  ) -join ' '
  Write-Host $cmd
  & python src/etl/rdf_to_neo4j.py --ttl $TtlNodes --chunk-size 50000 --fast-parse --dry-run --workers 4 --progress-newline | Tee-Object -FilePath (Join-Path $LogDir "dryrun-$ts.log")
  exit $LASTEXITCODE
}

# Nodes load (reset DB)
Write-Host "Starting nodes load (reset DB)..."
$nodesArgs = @(
  'src/etl/rdf_to_neo4j.py',
  '--ttl', $TtlNodes,
  '--chunk-size', '50000',
  '--fast-parse',
  '--batch-size', '5000',
  '--db-version', $DbVersion,
  '--reset-db',
  '--nodes-only',
  '--progress-newline',
  '--parse-heartbeat-seconds', '30'
)

Write-Host "Executing: python $($nodesArgs -join ' ')"
& python $nodesArgs 2>&1 | Tee-Object -FilePath $nodesLog
if ($LASTEXITCODE -ne 0) {
  Write-Error "Nodes load failed (exit code $LASTEXITCODE). See $nodesLog"
  exit $LASTEXITCODE
}

Write-Host "Nodes load completed. Log: $nodesLog"

# Relationships load
Write-Host "Starting relationships load..."
$relsArgs = @(
  'src/etl/rdf_to_neo4j.py',
  '--ttl', $TtlRels,
  '--chunk-size', '50000',
  '--fast-parse',
  '--batch-size', '5000',
  '--rel-batch-size', '1000',
  '--db-version', $DbVersion,
  '--rels-only',
  '--progress-newline',
  '--parse-heartbeat-seconds', '30'
)

Write-Host "Executing: python $($relsArgs -join ' ')"
& python $relsArgs 2>&1 | Tee-Object -FilePath $relsLog
if ($LASTEXITCODE -ne 0) {
  Write-Error "Relationships load failed (exit code $LASTEXITCODE). See $relsLog"
  exit $LASTEXITCODE
}

Write-Host "Relationships load completed. Log: $relsLog"

$ScriptEnd = Get-Date
Write-Host "Load wrapper finished at $ScriptEnd (duration: $($ScriptEnd - $ScriptStart))"
exit 0
