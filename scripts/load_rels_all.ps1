param(
    [string]$DbVersion = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$PythonExe = 'python',
    [int]$ChunkSizeCpe = 100000,
    [int]$ChunkSizeCpeMatch = 200000,
    [int]$ChunkSizeCve = 80000,
    [int]$ChunkSizeDefault = 20000,
    [int]$RelBatchCpe = 500,
    [int]$RelBatchCpeMatch = 1000,
    [int]$RelBatchCve = 500,
    [int]$RelBatchDefault = 200,
    [switch]$FastParse,
    [switch]$ProgressNewline,
    [int]$ParseHeartbeatSeconds = 30,
    [switch]$SkipDeprecates = $true
)

# Relationship loader policy:
# - Canonical inputs only: data/*/samples/pipeline-stage*-rels.ttl
# - No artifacts/tmp fallbacks to avoid stale or deprecated files
# - DEPRECATES relationships are skipped by default; use -SkipDeprecates:$false to include them

$ErrorActionPreference = 'Stop'

$stages = @(
    @{ name = 'CPE';      path = 'data/cpe/samples/pipeline-stage1-cpe-rels.ttl'; chunk = $ChunkSizeCpe; relBatch = $RelBatchCpe },
    @{ name = 'CPEMatch'; path = 'data/cpe/samples/pipeline-stage2-cpematch-rels.ttl'; chunk = $ChunkSizeCpeMatch; relBatch = $RelBatchCpeMatch },
    @{ name = 'CVE';      path = 'data/cve/samples/pipeline-stage3-cve-rels.ttl'; chunk = $ChunkSizeCve; relBatch = $RelBatchCve },
    @{ name = 'ATTACK';   path = 'data/attack/samples/pipeline-stage4-attack-rels.ttl'; chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'D3FEND';   path = 'data/d3fend/samples/pipeline-stage5-d3fend-rels.ttl'; chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'CAPEC';    path = 'data/capec/samples/pipeline-stage6-capec-rels.ttl'; chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'CWE';      path = 'data/cwe/samples/pipeline-stage7-cwe-rels.ttl'; chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'CAR';      path = 'data/car/samples/pipeline-stage8-car-rels.ttl'; chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'SHIELD';   path = 'data/shield/samples/pipeline-stage9-shield-rels.ttl'; chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault },
    @{ name = 'ENGAGE';   path = 'data/engage/samples/pipeline-stage10-engage-rels.ttl'; chunk = $ChunkSizeDefault; relBatch = $RelBatchDefault }
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
