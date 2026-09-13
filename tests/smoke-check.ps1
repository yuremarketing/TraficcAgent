$html=Get-Content -Raw (Resolve-Path .\dist\mvp.html); if($html -notmatch 'localStorage'){throw 'Local persistence missing'}; Write-Output 'Smoke checks passed'
