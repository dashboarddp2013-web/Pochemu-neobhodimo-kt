# Уменьшение растровых исходников макета (assets/img/src) средствами Windows (System.Drawing, PowerShell 5.1).
#
# Что делает (шаг -Step выбирает одно из двух):
#   photos (по умолчанию):
#   * src/xray-hands.jpg -> assets/img/xray-hands.jpg, 2000x1334, JPEG качество 82 (готовый файл);
#   * src/logo-white.png -> <OutDir>/gdi-logo-white.png, 436x259, с прозрачностью (промежуточный файл);
#   * src/hero-xray.png  -> <OutDir>/gdi-hero-xray.png, 1242x1641, с прозрачностью (промежуточный файл).
#   Промежуточные PNG потом пережимает без потерь tools/build_assets.py (у System.Drawing PNG тяжелее).
#   Ресемплинг: HighQualityBicubic, края — WrapMode TileFlipXY (без полупрозрачной каймы).
#   jpeg (таск F7, лёгкие картинки для мобильного интернета):
#   * assets/img/<имя>.png -> assets/img/<имя>.jpg для каждого имени из -Jpeg (через запятую, без
#     расширения), тот же пиксельный размер, без пересчёта пикселей, JPEG качество -JpegQuality
#     (обычный, не прогрессивный: GDI+ прогрессивные не пишет). Иллюстрации непрозрачные — фон не нужен.
#     Список имён и качество задаёт tools/build_assets.py (JPEG_NAMES, JPEG_QUALITY).
#
# Обычно запускается из tools/build_assets.py. Вручную, из корня сайта:
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/resize.ps1 -OutDir <папка для промежуточных PNG>
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/resize.ps1 -Step jpeg -Jpeg see-01,step-2 -JpegQuality 82
# Скачивать ничего не нужно; файлы в assets/img/src не меняются.

param(
  [string]$OutDir = $env:TEMP,
  [ValidateSet('photos', 'jpeg')][string]$Step = 'photos',
  [string]$Jpeg = '',
  [int]$JpegQuality = 82
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$Root = Split-Path -Parent $PSScriptRoot
$Src = Join-Path $Root 'assets\img\src'
$Img = Join-Path $Root 'assets\img'

function Resize-Image {
  param([string]$From, [string]$To, [int]$W, [int]$H, [string]$Format = 'png', [long]$Quality = 82)
  $img = [System.Drawing.Image]::FromFile($From)
  try {
    $bmp = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $bmp.SetResolution(72, 72)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CompositingMode = [System.Drawing.Drawing2D.CompositingMode]::SourceCopy
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $attr = New-Object System.Drawing.Imaging.ImageAttributes
    $attr.SetWrapMode([System.Drawing.Drawing2D.WrapMode]::TileFlipXY)
    $rect = New-Object System.Drawing.Rectangle(0, 0, $W, $H)
    $g.DrawImage($img, $rect, 0, 0, $img.Width, $img.Height, [System.Drawing.GraphicsUnit]::Pixel, $attr)
    $g.Dispose()
    if ($Format -eq 'jpeg') {
      $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
      $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
      $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, $Quality)
      $rgb = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
      $rgb.SetResolution(72, 72)
      $g2 = [System.Drawing.Graphics]::FromImage($rgb)
      $g2.Clear([System.Drawing.Color]::White)
      $g2.DrawImageUnscaled($bmp, 0, 0)
      $g2.Dispose()
      $rgb.Save($To, $codec, $ep)
      $rgb.Dispose()
    } else {
      $bmp.Save($To, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    $bmp.Dispose()
  } finally {
    $img.Dispose()
  }
  Write-Output ("{0} {1}x{2} {3} bytes" -f (Split-Path -Leaf $To), $W, $H, (Get-Item $To).Length)
}

# PNG -> JPEG того же размера: пиксели копируются 1:1 (NearestNeighbor, без пересчёта), без прозрачности.
function Convert-ToJpeg {
  param([string]$From, [string]$To, [long]$Quality)
  $img = [System.Drawing.Image]::FromFile($From)
  try {
    $W = $img.Width
    $H = $img.Height
    $rgb = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $rgb.SetResolution(72, 72)
    $g = [System.Drawing.Graphics]::FromImage($rgb)
    $g.Clear([System.Drawing.Color]::White)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::Half
    $rect = New-Object System.Drawing.Rectangle(0, 0, $W, $H)
    $g.DrawImage($img, $rect, 0, 0, $W, $H, [System.Drawing.GraphicsUnit]::Pixel)
    $g.Dispose()
    $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
    $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, $Quality)
    $rgb.Save($To, $codec, $ep)
    $rgb.Dispose()
  } finally {
    $img.Dispose()
  }
  Write-Output ("{0} {1}x{2} q{3} {4} bytes" -f (Split-Path -Leaf $To), $W, $H, $Quality, (Get-Item $To).Length)
}

if ($Step -eq 'jpeg') {
  $names = @($Jpeg -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  if ($names.Count -eq 0) { throw 'Шаг jpeg: не заданы имена картинок (-Jpeg имя1,имя2).' }
  foreach ($name in $names) {
    Convert-ToJpeg -From (Join-Path $Img ($name + '.png')) -To (Join-Path $Img ($name + '.jpg')) -Quality $JpegQuality
  }
} else {
  New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
  Resize-Image -From (Join-Path $Src 'logo-white.png') -To (Join-Path $OutDir 'gdi-logo-white.png') -W 436 -H 259
  Resize-Image -From (Join-Path $Src 'hero-xray.png') -To (Join-Path $OutDir 'gdi-hero-xray.png') -W 1242 -H 1641
  Resize-Image -From (Join-Path $Src 'xray-hands.jpg') -To (Join-Path $Img 'xray-hands.jpg') -W 2000 -H 1334 -Format jpeg -Quality 82
}
