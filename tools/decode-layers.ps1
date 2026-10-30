$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$dll='D:/codex/2026-10-08/zhe/work/atri-tools/GARbro'
Add-Type -AssemblyName PresentationCore,WindowsBase
[Reflection.Assembly]::LoadFrom((Join-Path $dll 'GameRes.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $dll 'ArcFormats.dll')) | Out-Null
$format=New-Object GameRes.Formats.KiriKiri.TlgFormat
$plan=Get-Content -LiteralPath (Join-Path $root 'reports/tlg-plan.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$done=0
foreach($p in $plan){
 [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($p.output))|Out-Null
 if(!(Test-Path -LiteralPath $p.output)){
  if([IO.Path]::GetExtension($p.input) -eq '.png'){Copy-Item -LiteralPath $p.input -Destination $p.output}
  else{
   $stream=[GameRes.BinaryStream]::FromFile($p.input)
   try{$meta=$format.ReadMetaData($stream);if(!$meta){throw 'Invalid TLG'};$stream.Position=0;$decoded=$format.Read($stream,$meta)
    $encoder=New-Object System.Windows.Media.Imaging.PngBitmapEncoder
    $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($decoded.Bitmap))
    $output=[IO.File]::Create($p.output);try{$encoder.Save($output)}finally{$output.Dispose()}
   }finally{$stream.Dispose()}
  }
 }
 $done++;if(($done%100)-eq 0){Write-Output ('DECODED_LAYERS '+$done)}
}
Write-Output ('COMPLETE_LAYERS '+$done)
