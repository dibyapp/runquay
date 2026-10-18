@echo off
setlocal
set "RUNQUAY_INSTALLER_FILE=%~f0"
set "RUNQUAY_INSTALLER_MODE=%~1"
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; try { $source=Get-Content -Raw -LiteralPath $env:RUNQUAY_INSTALLER_FILE; $marker=':__RUNQUAY_POWERSHELL__'; $at=$source.LastIndexOf($marker); if($at -lt 0){throw 'Installer is incomplete'}; . ([scriptblock]::Create($source.Substring($at+$marker.Length))) } catch { Write-Host ('Runquay install stopped: '+$_.Exception.Message) -ForegroundColor Red; exit 2 }"
if errorlevel 1 (
  echo Read the error above, then press any key to close.
  pause >nul
  exit /b 2
)
exit /b 0
:__RUNQUAY_POWERSHELL__
$ErrorActionPreference='Stop'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
$headers=@{'User-Agent'='Runquay-Installer'; 'Accept'='application/vnd.github+json'}
$release=Invoke-RestMethod -Uri 'https://api.github.com/repos/dibyapp/runquay/releases/latest' -Headers $headers
if($release.tag_name -notmatch '^v([0-9]+\.[0-9]+\.[0-9]+)$'){throw 'The latest release has an unexpected version.'}
$version=$Matches[1]
$archiveName="runquay-$version-source.zip"
$archive=@($release.assets | Where-Object { $_.name -ceq $archiveName })
$checksum=@($release.assets | Where-Object { $_.name -ceq "$archiveName.sha256" })
if($archive.Count -ne 1 -or $checksum.Count -ne 1){throw 'The audited source ZIP and checksum are missing from the release.'}
foreach($asset in @($archive[0],$checksum[0])){
  if($asset.browser_download_url -notlike "https://github.com/dibyapp/runquay/releases/download/v$version/*"){
    throw 'The release asset address is unexpected.'
  }
}
Write-Host "Runquay $version - verified release found."
if($env:RUNQUAY_INSTALLER_MODE -ceq '--check'){
  Write-Host 'Check only: no download, installation or AI request was started.'
  return
}
$installRoot=Join-Path $env:LOCALAPPDATA 'Runquay'
$versions=Join-Path $installRoot 'versions'
$target=Join-Path $versions $version
$scratch=Join-Path ([IO.Path]::GetTempPath()) ('runquay-install-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $scratch -Force | Out-Null
try {
  if($env:RUNQUAY_INSTALLER_MODE -ceq '--verify' -or -not (Test-Path -LiteralPath (Join-Path $target 'runquay.py'))){
    $zip=Join-Path $scratch $archiveName
    $sum=Join-Path $scratch "$archiveName.sha256"
    Invoke-WebRequest -Uri $archive[0].browser_download_url -Headers $headers -OutFile $zip
    Invoke-WebRequest -Uri $checksum[0].browser_download_url -Headers $headers -OutFile $sum
    $line=[IO.File]::ReadAllText($sum).Trim()
    if($line -cnotmatch ('^([a-f0-9]{64})  '+[regex]::Escape($archiveName)+'$')){throw 'The release checksum file is invalid.'}
    $expected=$Matches[1]
    $hasher=[Security.Cryptography.SHA256]::Create()
    $stream=[IO.File]::OpenRead($zip)
    try { $actual=([BitConverter]::ToString($hasher.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $hasher.Dispose() }
    if($actual -cne $expected){throw 'The downloaded ZIP does not match its release checksum.'}
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $package=[IO.Compression.ZipFile]::OpenRead($zip)
    try {
      $total=0
      foreach($item in $package.Entries){
        $name=$item.FullName
        $segments=$name.Split('/')
        if(-not $name.StartsWith('runquay/',[StringComparison]::Ordinal) -or
           $name.Contains('\') -or $segments -contains '..' -or $segments -contains '.' -or
           $name -match '[\x00-\x1f]' -or $name.StartsWith('/') -or
           (($item.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000){
          throw 'The release ZIP has an unsafe file path or link.'
        }
        $total += $item.Length
        if($total -gt 150MB){throw 'The release ZIP expands beyond its allowed size.'}
      }
    } finally { $package.Dispose() }
    $extracted=Join-Path $scratch 'extracted'
    [IO.Compression.ZipFile]::ExtractToDirectory($zip,$extracted)
    $source=Join-Path $extracted 'runquay'
    if(-not (Test-Path -LiteralPath (Join-Path $source 'runquay.py')) -or
       -not (Test-Path -LiteralPath (Join-Path $source 'setup.cmd'))){throw 'The release ZIP is missing Runquay.'}
    if($env:RUNQUAY_INSTALLER_MODE -ceq '--verify'){
      Write-Host 'Archive and checksum verified. No installation or AI request was started.'
      return
    }
    New-Item -ItemType Directory -Path $versions -Force | Out-Null
    if(Test-Path -LiteralPath $target){throw 'An incomplete installation exists for this version. Remove that version folder and retry.'}
    Move-Item -LiteralPath $source -Destination $target
    Write-Host 'Installed Runquay in your user folder.'
  } else { Write-Host 'This release is already installed.' }
  $menu=Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'
  New-Item -ItemType Directory -Path $menu -Force | Out-Null
  $shortcut=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $menu 'Runquay.lnk'))
  $shortcut.TargetPath=Join-Path $target 'setup.cmd'
  $shortcut.WorkingDirectory=$target
  $shortcut.Description='Open Runquay and its guided setup'
  $shortcut.Save()
  Write-Host 'Runquay is in your Start menu. Opening setup now.'
  Start-Process -FilePath (Join-Path $target 'setup.cmd') -WorkingDirectory $target
} finally {
  if(Test-Path -LiteralPath $scratch){Remove-Item -LiteralPath $scratch -Recurse -Force}
}
