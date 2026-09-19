[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$CampaignDirectory
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$installer = Join-Path $PSScriptRoot 'reconquered_ptbr_native_media.py'
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    Write-Error 'Instalador nativo ausente. Extraia o pacote RC3 completo.' -ErrorAction Continue
    exit 1
}

$versionCheck = 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'
foreach ($name in @('py', 'python3', 'python')) {
    $command = Get-Command -Name $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $command) { continue }
    $prefix = @()
    if ($name -eq 'py') { $prefix = @('-3') }
    try {
        & $command.Source @prefix -c $versionCheck 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { continue }
    } catch {
        continue
    }

    & $command.Source @prefix $installer install $CampaignDirectory
    exit $LASTEXITCODE
}

Write-Error 'Python 3.11 ou superior nao encontrado. Instale-o e disponibilize py, python3 ou python no PATH.' -ErrorAction Continue
exit 1
