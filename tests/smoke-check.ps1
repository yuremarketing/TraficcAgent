foreach($f in '.\dist\mvp.html','.\dist\index.html'){$html=Get-Content -Raw (Resolve-Path $f); if($html -notmatch 'localStorage'){throw "Local persistence missing in $f"}}
Write-Output 'Smoke checks passed'
