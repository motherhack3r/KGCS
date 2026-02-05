#!/usr/bin/env pwsh
# Monitor ETL pipeline progress

while ($true) {
    Clear-Host
    Write-Host "=== ETL Pipeline Progress ===" -ForegroundColor Green
    Write-Host "Time: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
    Write-Host ""
    
    # Check output files
    Write-Host "Output files:" -ForegroundColor Yellow
    Get-ChildItem tmp/pipeline-stage*.ttl -ErrorAction SilentlyContinue | 
        Select-Object @{N="Stage";E={$_.Name -replace 'pipeline-stage(\d+)-(.+)\.ttl','$2'}}, 
                      @{N="Size (MB)";E={[math]::Round($_.Length/1MB,2)}} | 
        Sort-Object Stage -ErrorAction SilentlyContinue | Format-Table -AutoSize
    
    # Get last lines from log
    Write-Host "Recent activity:" -ForegroundColor Yellow
    Get-Content logs/etl_run_20260203.log -ErrorAction SilentlyContinue -Tail 5 | ForEach-Object {
        if ($_ -match "Loading|Done|STAGE|Error") {
            Write-Host $_
        }
    }
    
    # Check if still running
    $running = Get-Job -Name "ETL*" -ErrorAction SilentlyContinue
    if ($running) {
        Write-Host "" -ForegroundColor Cyan
        Write-Host "Pipeline is running... (Press Ctrl+C to stop monitoring)" -ForegroundColor Cyan
    } else {
        Write-Host "" -ForegroundColor Green
        Write-Host "Pipeline appears to be complete!" -ForegroundColor Green
        break
    }
    
    Start-Sleep -Seconds 10
}
