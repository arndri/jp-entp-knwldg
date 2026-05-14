param(
  [Parameter(Mandatory=$true)]
  [string]$Path,

  [string]$AccessLevel = "public"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$body = @{
  path = $Path
  access_level = $AccessLevel
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/ingest" `
  -ContentType "application/json" `
  -Body $body
