param(
    [string]$DbVersion = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$PythonExe = 'python',
    [int]$ChunkSizeCpe = 100000,
    [int]$ChunkSizeCpeMatch = 200000,
    [int]$ChunkSizeCve = 80000,
    [int]$ChunkSizeDefault = 20000,
    [int]$RelBatchCpe = 500,
    [int]$RelBatchCpeDeprecates = 100,
    [int]$RelBatchCpeMatch = 1000,
    [int]$RelBatchCve = 500,
    [int]$RelBatchDefault = 200,
    [switch]$FastParse,
    [switch]$ProgressNewline,
    [int]$ParseHeartbeatSeconds = 30,
    [switch]$SkipDeprecates
)

$ErrorActionPreference = 'Stop'

function Get-RelsPath([string[]]$preferred, [string]$fallback) {
    foreach ($p in $preferred) {
        if ($p -and (Test-Path $p)) { return $p }
    }
    if ($fallback -and (Test-Path $fallback)) { return $fallback }
    return $null
}

$stages = @(
    @{ name = 'CPE';      path = (Get-RelsPath @('artifacts/pipeline-stage1-cpe-rels-dedup-other.ttl', 'artifacts/pipeline-stage1-cpe-rels-dedup.ttl', 'data/cpe/samples/pipeline-stage1-cpe-rels.ttl') 'tmp/pipeline-stage1-cpe.ttl'); chunk = $ChunkSizeCpe; relBatch = $RelBatchCpe },
    @{ name = 'CPE-Deprecates'; path = (Get-RelsPath @('artifacts/pipeline-stage1-cpe-rels-dedup-https___example.org_sec_core_deprecates.ttl') $null); chunk = $ChunkSizeCpe; relBatch = $RelBatchCpeDeprecates },
    @{ name = 'CPEMatch'; path = (Get-RelsPath @('artifacts/pipeline-stage2-cpematch-rels-dedup.ttl', 'data/cpe/samples/pipeline-stage2-cpematch-rels.ttl') 'tmp/pipeline-stage2-cpematch.ttl'); chunk = $ChunkSizeCpeMatch; relBatch = $RelBatchCpeMatch },
    @{ name = 'CVE';      path = (Get-RelsPath @('data/cve/samples/pipeline-stage3-cve-rels.ttl') 'tmp/pipeline-stage3-cve.ttl'); chunk = $ChunkSizeCve; relBatch = $RelBatchCve },
    @{ name = 'CWE';      path = (Get-RelsPath @('data/cwe/samples/pipeline-stage7-cwe-rels.ttl') 'tmp/pipeline-stage7-cwe.ttl'); chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'CAPEC';    path = (Get-RelsPath @('data/capec/samples/pipeline-stage6-capec-rels.ttl') 'tmp/pipeline-stage6-capec.ttl'); chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'ATTACK';   path = (Get-RelsPath @('data/attack/samples/pipeline-stage4-attack-rels.ttl') 'tmp/pipeline-stage4-attack.ttl'); chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'D3FEND';   path = (Get-RelsPath @('data/d3fend/samples/pipeline-stage5-d3fend-rels.ttl') 'tmp/pipeline-stage5-d3fend.ttl'); chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'CAR';      path = (Get-RelsPath @('data/car/samples/pipeline-stage8-car-rels.ttl') 'tmp/pipeline-stage8-car.ttl'); chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'SHIELD';   path = (Get-RelsPath @('data/shield/samples/pipeline-stage9-shield-rels.ttl') 'tmp/pipeline-stage9-shield.ttl'); chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'ENGAGE';   path = (Get-RelsPath @('data/engage/samples/pipeline-stage10-engage-rels.ttl') 'tmp/pipeline-stage10-engage.ttl'); chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault }
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
        '--rels-only',
        '--chunk-size', $s.chunk,
        '--rel-batch-size', $s.relBatch,
        '--db-version', $DbVersion,
        '--parse-heartbeat-seconds', $ParseHeartbeatSeconds
    )

    if ($FastParse) { $cmd += '--fast-parse' }
    if ($ProgressNewline) { $cmd += '--progress-newline' }
    if ($SkipDeprecates) { $cmd += '--skip-deprecates' }

    Write-Host "Loading relationships for $($s.name): $($s.path)" -ForegroundColor Cyan
    & $cmd[0] @($cmd[1..($cmd.Count - 1)])
    if ($LASTEXITCODE -ne 0) {
        throw "Relationships load failed for $($s.name)"
    }
}
