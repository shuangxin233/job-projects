param([string]$Session = 'window1', [string]$UserId = 'A', [string]$EnvFile = '')
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:AGENT_DATA_DIR = Join-Path ([Environment]::GetFolderPath('Desktop')) '项目制作过程\最小Agent运行数据'
$env:PYTHONPYCACHEPREFIX = Join-Path $env:AGENT_DATA_DIR 'pycache'
if (-not $EnvFile) {
    $taskConfig = Join-Path ([Environment]::GetFolderPath('Desktop')) '项目制作过程\最小Agent-API配置.env'
    if (Test-Path -LiteralPath $taskConfig) { $EnvFile = $taskConfig }
    else { $EnvFile = Join-Path $PSScriptRoot '.env' }
}
Push-Location $PSScriptRoot
try {
    python -m mini_agent --user $UserId --session $Session --env-file $EnvFile --trace
    $agentExit = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $agentExit
