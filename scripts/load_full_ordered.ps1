param(
    [string]$DbVersion = (Get-Date -Format 'yyyy-MM-dd'),
    [string]$PythonExe = 'python',
    [string[]]$Inputs = @('data/*/samples/pipeline-stage*-nodes.ttl', 'data/*/samples/pipeline-stage*-rels.ttl'),
    [string]$NodesOut = 'tmp/combined-nodes.ttl',
    [string]$RelsOut = 'tmp/combined-rels.ttl',
    [int]$ChunkSize = 50000,
    [int]$BatchSize = 20000,
    [int]$RelBatchSize = 5000,
    [switch]$FastParse,
    [switch]$ProgressNewline,
    [int]$ParseHeartbeatSeconds = 30,
    [switch]$ResetDb
)

$ErrorActionPreference = 'Stop'

Write-Host "Combining stage TTLs into ordered full file..." -ForegroundColor Cyan
$combineCmd = @(
    $PythonExe,
    'scripts/combine_ttl_pipeline.py',
    '--nodes-out', $NodesOut,
    '--rels-out', $RelsOut,
    '--preserve-order',
    '--drop-rels-types',
    '--skip-sanitize',
    '--skip-post-validate'
)

if ($Inputs -and $Inputs.Count -gt 0) {
    $combineCmd += '--inputs'
    $combineCmd += $Inputs
}

& $combineCmd[0] @($combineCmd[1..($combineCmd.Count - 1)])
if ($LASTEXITCODE -ne 0) {
    throw "Combine failed"
}

Write-Host "Loading ordered nodes TTL into Neo4j..." -ForegroundColor Cyan
$loadNodesCmd = @(
    $PythonExe,
    'src/etl/rdf_to_neo4j.py',
    '--ttl', $NodesOut,
    '--chunk-size', $ChunkSize,
    '--batch-size', $BatchSize,
    '--rel-batch-size', $RelBatchSize,
    '--db-version', $DbVersion,
    '--parse-heartbeat-seconds', $ParseHeartbeatSeconds,
    '--nodes-only'
)

if ($FastParse) { $loadNodesCmd += '--fast-parse' }
if ($ProgressNewline) { $loadNodesCmd += '--progress-newline' }
if ($ResetDb) { $loadNodesCmd += '--reset-db' }

& $loadNodesCmd[0] @($loadNodesCmd[1..($loadNodesCmd.Count - 1)])
if ($LASTEXITCODE -ne 0) {
    throw "Nodes load failed"
}

Write-Host "Loading ordered rels TTL into Neo4j..." -ForegroundColor Cyan
$loadRelsCmd = @(
    $PythonExe,
    'src/etl/rdf_to_neo4j.py',
    '--ttl', $RelsOut,
    '--chunk-size', $ChunkSize,
    '--batch-size', $BatchSize,
    '--rel-batch-size', $RelBatchSize,
    '--db-version', $DbVersion,
    '--parse-heartbeat-seconds', $ParseHeartbeatSeconds,
    '--rels-only'
)

if ($FastParse) { $loadRelsCmd += '--fast-parse' }
if ($ProgressNewline) { $loadRelsCmd += '--progress-newline' }

& $loadRelsCmd[0] @($loadRelsCmd[1..($loadRelsCmd.Count - 1)])
if ($LASTEXITCODE -ne 0) {
    throw "Rels load failed"
}
