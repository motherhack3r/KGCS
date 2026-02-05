# KGCS Neo4j Loading Commands - PowerShell Version
# For 22.42 GB combined-pipeline.ttl file

Write-Host ""
Write-Host "╔═════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  KGCS Neo4j Loading - Optimized for 22GB TTL File      ║" -ForegroundColor Cyan
Write-Host "╚═════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Ensure conda is activated
Write-Host "Activating conda environment..." -ForegroundColor Yellow
(E:\DEVEL\software\miniconda\shell\condabin\conda-hook.ps1)
conda activate E:\DEVEL\software\miniconda\envs\metadata

cd e:\DEVEL\LAIA\KGCS

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "STEP 1: VALIDATE COMBINED TTL FILE (5-10 min)" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

python src/etl/rdf_to_neo4j.py `
    --ttl tmp/combined-pipeline.ttl `
    --dry-run `
    --fast-parse `
    --parse-heartbeat-seconds 30

$validationResult = $LASTEXITCODE
if ($validationResult -ne 0) {
    Write-Host ""
    Write-Host "❌ Validation failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Validation passed. Proceeding to load..." -ForegroundColor Green
Write-Host ""

# Ask user for confirmation
$confirmation = Read-Host "Start loading nodes? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Cancelled by user." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "STEP 2A: LOAD NODES ONLY (15-30 min)" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

$nodeStartTime = Get-Date
python src/etl/rdf_to_neo4j.py `
    --ttl tmp/combined-pipeline.ttl `
    --nodes-only `
    --fast-parse `
    --batch-size 3000 `
    --database neo4j-2026-02-03 `
    --reset-db

$nodeResult = $LASTEXITCODE
$nodeEndTime = Get-Date
$nodeDuration = ($nodeEndTime - $nodeStartTime).TotalMinutes

if ($nodeResult -ne 0) {
    Write-Host ""
    Write-Host "❌ Node loading failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Node loading complete ($([math]::Round($nodeDuration, 1)) min)" -ForegroundColor Green
Write-Host ""

# Ask user for confirmation
$confirmation = Read-Host "Start loading relationships? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Cancelled by user. Nodes are loaded but relationships are pending." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "STEP 2B: LOAD RELATIONSHIPS (30-60 min)" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

$relStartTime = Get-Date
python src/etl/rdf_to_neo4j.py `
    --ttl tmp/combined-pipeline.ttl `
    --fast-parse `
    --rel-batch-size 2000 `
    --batch-size 1 `
    --database neo4j-2026-02-03

$relResult = $LASTEXITCODE
$relEndTime = Get-Date
$relDuration = ($relEndTime - $relStartTime).TotalMinutes

if ($relResult -ne 0) {
    Write-Host ""
    Write-Host "❌ Relationship loading failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Relationship loading complete ($([math]::Round($relDuration, 1)) min)" -ForegroundColor Green
Write-Host ""

$totalDuration = ($relEndTime - $nodeStartTime).TotalMinutes

Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "SUMMARY" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Validation:   Complete (dry-run)" -ForegroundColor Green
Write-Host "✅ Nodes:        ~2.5M loaded ($([math]::Round($nodeDuration, 1)) min)" -ForegroundColor Green
Write-Host "✅ Relationships: ~26M loaded ($([math]::Round($relDuration, 1)) min)" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Total Time: $([math]::Round($totalDuration, 1)) minutes" -ForegroundColor Cyan
Write-Host "💾 Database: neo4j-2026-02-03" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 Neo4j loading complete!" -ForegroundColor Green
Write-Host ""

# Show Neo4j stats
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Verify causal chain in Neo4j:"
Write-Host "   MATCH (v:Vulnerability)-[:caused_by]->(w:Weakness)-[:exploited_by]->(c:AttackPattern)-[:implements]->(t:Technique)"
Write-Host "   RETURN count(DISTINCT v) as cves, count(DISTINCT t) as techniques"
Write-Host ""
Write-Host "2. Check D3FEND relationships:"
Write-Host "   MATCH (d:DefensiveTechnique)-[:mitigates]->(t:Technique)"
Write-Host "   RETURN count(*) as defense_links"
Write-Host ""
Write-Host "3. Graph statistics:"
Write-Host "   CALL db.stats.retrieve('GRAPH COUNTS')"
Write-Host ""
