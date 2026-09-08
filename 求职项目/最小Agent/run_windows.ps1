param([string]$Session = 'window1', [string]$UserId = 'A', [string]$EnvFile = '', [string]$DataDir = '')
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
if (-not $DataDir) { $DataDir = Join-Path $PSScriptRoot '.runtime' }
$env:AGENT_DATA_DIR = $DataDir
$env:PYTHONPYCACHEPREFIX = Join-Path $env:AGENT_DATA_DIR 'pycache'
if (-not $EnvFile) {
    $EnvFile = Join-Path $PSScriptRoot '.env'
}
$taskPython = Get-Command python -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$taskPythonArgs = @()
if (-not $taskPython -or $taskPython.Source -like '*\WindowsApps\*') {
    $taskPython = Get-Command py -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    $taskPythonArgs = @('-3')
}
if (-not $taskPython) {
    Write-Host '未找到 Python。请按 QUICKSTART.md 安装 Python 3.10+，然后重新打开终端。'
    exit 1
}
& $taskPython.Source @taskPythonArgs -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if ($LASTEXITCODE -ne 0) { Write-Host '需要 Python 3.10 或以上版本。'; exit 1 }
Push-Location $PSScriptRoot
try {
    & $taskPython.Source @taskPythonArgs -m mini_agent --user $UserId --session $Session --env-file $EnvFile --trace
    $agentExit = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $agentExit
