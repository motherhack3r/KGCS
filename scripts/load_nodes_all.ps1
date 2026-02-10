param(
    [string]$DbVersion = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$PythonExe = 'python',
    [int]$ChunkSizeCpe = 100000,
    [int]$ChunkSizeCpeMatch = 200000,
    [int]$ChunkSizeCve = 80000,
    [int]$ChunkSizeDefault = 20000,
    [int]$BatchSizeCpe = 20000,
    [int]$BatchSizeCpeMatch = 20000,
    [int]$BatchSizeCve = 15000,
    [int]$BatchSizeDefault = 5000,
    [switch]$FastParse,
    [switch]$ProgressNewline,
    [int]$ParseHeartbeatSeconds = 30
)

$ErrorActionPreference = 'Stop'

function Get-NodePath([string]$preferred, [string]$fallback) {
    if (Test-Path $preferred) { return $preferred }
    if (Test-Path $fallback) { return $fallback }
    return $null
}

$stages = @(
    @{ name = 'CPE';      path = (Get-NodePath 'data/cpe/samples/pipeline-stage1-cpe-nodes.ttl' 'tmp/pipeline-stage1-cpe.ttl'); chunk = $ChunkSizeCpe; batch = $BatchSizeCpe; reset = $true },
    @{ name = 'CPEMatch'; path = (Get-NodePath 'data/cpe/samples/pipeline-stage2-cpematch-nodes.ttl' 'tmp/pipeline-stage2-cpematch.ttl'); chunk = $ChunkSizeCpeMatch; batch = $BatchSizeCpeMatch; reset = $false },
    @{ name = 'CVE';      path = (Get-NodePath 'data/cve/samples/pipeline-stage3-cve-nodes.ttl' 'tmp/pipeline-stage3-cve.ttl'); chunk = $ChunkSizeCve; batch = $BatchSizeCve; reset = $false },
    @{ name = 'CWE';      path = (Get-NodePath 'data/cwe/samples/pipeline-stage7-cwe-nodes.ttl' 'tmp/pipeline-stage7-cwe.ttl'); chunk = $ChunkSizeDefault; batch = $BatchSizeDefault; reset = $false },
    @{ name = 'CAPEC';    path = (Get-NodePath 'data/capec/samples/pipeline-stage6-capec-nodes.ttl' 'tmp/pipeline-stage6-capec.ttl'); chunk = $ChunkSizeDefault; batch = $BatchSizeDefault; reset = $false },
    @{ name = 'ATTACK';   path = (Get-NodePath 'data/attack/samples/pipeline-stage4-attack-nodes.ttl' 'tmp/pipeline-stage4-attack.ttl'); chunk = $ChunkSizeDefault; batch = $BatchSizeDefault; reset = $false },
    @{ name = 'D3FEND';   path = (Get-NodePath 'data/d3fend/samples/pipeline-stage5-d3fend-nodes.ttl' 'tmp/pipeline-stage5-d3fend.ttl'); chunk = $ChunkSizeDefault; batch = $BatchSizeDefault; reset = $false },
    @{ name = 'CAR';      path = (Get-NodePath 'data/car/samples/pipeline-stage8-car-nodes.ttl' 'tmp/pipeline-stage8-car.ttl'); chunk = $ChunkSizeDefault; batch = $BatchSizeDefault; reset = $false },
    @{ name = 'SHIELD';   path = (Get-NodePath 'data/shield/samples/pipeline-stage9-shield-nodes.ttl' 'tmp/pipeline-stage9-shield.ttl'); chunk = $ChunkSizeDefault; batch = $BatchSizeDefault; reset = $false },
    @{ name = 'ENGAGE';   path = (Get-NodePath 'data/engage/samples/pipeline-stage10-engage-nodes.ttl' 'tmp/pipeline-stage10-engage.ttl'); chunk = $ChunkSizeDefault; batch = $BatchSizeDefault; reset = $false }
)

foreach ($s in $stages) {
    if (-not $s.path -or -not (Test-Path $s.path)) {
        Write-Host "Skipping missing file: $($s.name)" -ForegroundColor Yellow
        continue
    }

    $cmd = @(
        $PythonExe,
        'src/etl/rdf_to_neo4j.py',
        '--ttl', $s.path,
        '--nodes-only',
        '--chunk-size', $s.chunk,
        '--batch-size', $s.batch,
        '--db-version', $DbVersion,
        '--parse-heartbeat-seconds', $ParseHeartbeatSeconds
    )

    if ($FastParse) { $cmd += '--fast-parse' }
    if ($ProgressNewline) { $cmd += '--progress-newline' }
    if ($s.reset) { $cmd += '--reset-db' }

    Write-Host "Loading nodes for $($s.name): $($s.path)" -ForegroundColor Cyan
    & $cmd[0] @($cmd[1..($cmd.Count - 1)])
    if ($LASTEXITCODE -ne 0) {
        throw "Nodes load failed for $($s.name)"
    }
}
