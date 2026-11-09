# Windows wrapper for run_all.R (tests, main run, tables, figures, Distribution
# experiment and report, checksums). Usage:
#   ./reproduce.ps1 -Workers 16 [-Rscript 'C:\Program Files\R\R-4.6.2\bin\x64\Rscript.exe']
param([int]$Workers = 16, [string]$Rscript = '')
$ErrorActionPreference = 'Stop'
if (-not $Rscript) {
    $cmd = Get-Command Rscript -ErrorAction SilentlyContinue
    if ($cmd) { $Rscript = $cmd.Source }
    else {
        $found = Get-ChildItem 'C:\Program Files\R\R-*\bin\x64\Rscript.exe' -ErrorAction SilentlyContinue |
                 Sort-Object FullName -Descending | Select-Object -First 1
        if (-not $found) { throw 'Rscript not found; pass -Rscript <path>.' }
        $Rscript = $found.FullName
    }
}
& $Rscript (Join-Path $PSScriptRoot 'run_all.R') --workers $Workers
if ($LASTEXITCODE -ne 0) { throw "run_all.R failed (exit $LASTEXITCODE)" }
