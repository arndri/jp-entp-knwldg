param(
  [Parameter(Mandatory=$true)]
  [string]$Question,

  [string[]]$AccessLevels = @("public")
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Net.Http

$body = @{
  question = $Question
  access_levels = $AccessLevels
} | ConvertTo-Json -Depth 5

$client = [System.Net.Http.HttpClient]::new()
$content = [System.Net.Http.StringContent]::new(
  $body,
  [System.Text.Encoding]::UTF8,
  "application/json"
)

try {
  $response = $client.PostAsync("http://127.0.0.1:8000/api/chat", $content).GetAwaiter().GetResult()
  $bytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
  $text = [System.Text.Encoding]::UTF8.GetString($bytes)

  if (-not $response.IsSuccessStatusCode) {
    throw $text
  }

  $result = $text | ConvertFrom-Json
  Write-Output ""
  Write-Output "Answer:"
  Write-Output $result.answer
  Write-Output ""
  Write-Output "Citations:"
  foreach ($citation in $result.citations) {
    Write-Output ("- {0}, page {1}, score {2}" -f $citation.title, $citation.page_number, $citation.score)
  }
}
finally {
  if ($null -ne $content) {
    $content.Dispose()
  }
  if ($null -ne $client) {
    $client.Dispose()
  }
}
