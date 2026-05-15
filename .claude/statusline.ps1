# Claude Code status line script
# Shows: current directory | model name | remaining context percentage

$jsonInput = [Console]::In.ReadToEnd()
$data = $jsonInput | ConvertFrom-Json

$dir = Split-Path $data.workspace.current_dir -Leaf
$model = $data.model.display_name
$remaining = $data.context_window.remaining_percentage

if ($null -ne $remaining) {
    $pct = [math]::Round($remaining)
    Write-Output "${dir} | ${model} | Context: ${pct}% remaining"
} else {
    Write-Output "${dir} | ${model}"
}
