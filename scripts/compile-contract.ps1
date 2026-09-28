param(
    [string]$SolcVersion = "0.8.24"
)

$projectRoot = Split-Path -Parent $PSScriptRoot
$outputDirectory = Join-Path $projectRoot "artifacts\solc"

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

docker run --rm `
    --volume "${projectRoot}:/sources" `
    "ethereum/solc:$SolcVersion" `
    --optimize `
    --via-ir `
    --evm-version shanghai `
    --abi `
    --bin `
    --output-dir /sources/artifacts/solc `
    /sources/ProductOriginChain.sol

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Contrato compilado em artifacts/solc."
