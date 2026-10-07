# Уменьшение растровых исходников макета (assets/img/src) средствами Windows (System.Drawing, PowerShell 5.1).
#
# Что делает (шаг -Step выбирает один из трёх):
#   photos (по умолчанию):
#   * src/xray-hands.jpg -> assets/img/xray-hands.jpg, 2000x1334, JPEG качество 82 (готовый файл);
#   * src/xray-hands.jpg -> assets/img/xray-hands-1000.jpg, 1000x667, JPEG качество 82 (таск F8: лёгкая
#     версия для телефона, страница берёт её через srcset), ресемплинг прямо с исходника, а не с 2000-px файла;
#   * src/logo-white.png -> <OutDir>/gdi-logo-white.png, 436x259, с прозрачностью (промежуточный файл);
#   * src/hero-xray.png  -> <OutDir>/gdi-hero-xray.png, 1242x1641, с прозрачностью (промежуточный файл).
#   Промежуточные PNG потом пережимает без потерь tools/build_assets.py (у System.Drawing PNG тяжелее).
#   Ресемплинг: HighQualityBicubic, края — WrapMode TileFlipXY (без полупрозрачной каймы).
#   jpeg (таск F7, лёгкие картинки для мобильного интернета):
#   * assets/img/<имя>.png -> assets/img/<имя>.jpg для каждого имени из -Jpeg (через запятую, без
#     расширения), тот же пиксельный размер, без пересчёта пикселей, JPEG качество -JpegQuality
#     (обычный, не прогрессивный: GDI+ прогрессивные не пишет). Иллюстрации непрозрачные — фон не нужен.
#     Список имён и качество задаёт tools/build_assets.py (JPEG_NAMES, JPEG_QUALITY).
#   og (таск F8, превью ссылки в мессенджере):
#   * assets/img/og-preview.jpg, 1200x630, JPEG качество -OgQuality: фон страницы (тёмно-синее свечение
#     как у первого экрана), слева белый логотип assets/img/logo-white.png, справа иллюстрация
#     assets/img/step-2.png в карточке (фон белый) со скруглением 24 px и мягкой тенью. Берёт готовые файлы
#     из assets/img, поэтому запускается после шагов photos и сборки иллюстраций.
#
# Обычно запускается из tools/build_assets.py. Вручную, из корня сайта:
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/resize.ps1 -OutDir <папка для промежуточных PNG>
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/resize.ps1 -Step jpeg -Jpeg see-01,step-2 -JpegQuality 82
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/resize.ps1 -Step og
# Скачивать ничего не нужно; файлы в assets/img/src не меняются.

param(
  [string]$OutDir = $env:TEMP,
  [ValidateSet('photos', 'jpeg', 'og')][string]$Step = 'photos',
  [string]$Jpeg = '',
  [int]$JpegQuality = 82,
  [int]$OgQuality = 90
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

# Скруглённый прямоугольник как контур (для карточки и её тени).
function New-RoundedPath {
  param([single]$X, [single]$Y, [single]$W, [single]$H, [single]$R)
  $d = $R * 2
  $path = New-Object System.Drawing.Drawing2D.GraphicsPath
  $path.AddArc($X, $Y, $d, $d, 180, 90)
  $path.AddArc($X + $W - $d, $Y, $d, $d, 270, 90)
  $path.AddArc($X + $W - $d, $Y + $H - $d, $d, $d, 0, 90)
  $path.AddArc($X, $Y + $H - $d, $d, $d, 90, 90)
  $path.CloseFigure()
  return ,$path
}

# Превью ссылки 1200x630: фон-свечение, слева логотип, справа иллюстрация в белой скруглённой карточке.
function New-OgPreview {
  param([string]$To, [long]$Quality)
  $W = 1200; $H = 630
  $Margin = 60; $Radius = 24
  $CardW = 520; $CardX = $W - $Margin - $CardW
  $logo = [System.Drawing.Image]::FromFile((Join-Path $Img 'logo-white.png'))
  $art = [System.Drawing.Image]::FromFile((Join-Path $Img 'step-2.png'))
  try {
    $CardH = [int][Math]::Round($CardW * $art.Height / $art.Width)
    $CardY = [int][Math]::Round(($H - $CardH) / 2)

    # Картинка карточки: масштаб HighQualityBicubic в готовый битмап, дальше он идёт кистью по контуру со сглаживанием.
    $scaled = New-Object System.Drawing.Bitmap($CardW, $CardH, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $scaled.SetResolution(72, 72)
    $gs = [System.Drawing.Graphics]::FromImage($scaled)
    $gs.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $gs.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $attr = New-Object System.Drawing.Imaging.ImageAttributes
    $attr.SetWrapMode([System.Drawing.Drawing2D.WrapMode]::TileFlipXY)
    $gs.DrawImage($art, (New-Object System.Drawing.Rectangle(0, 0, $CardW, $CardH)), 0, 0, $art.Width, $art.Height, [System.Drawing.GraphicsUnit]::Pixel, $attr)
    $gs.Dispose()

    $bmp = New-Object System.Drawing.Bitmap($W, $H, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $bmp.SetResolution(72, 72)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

    # Фон: цвета свечения первого экрана страницы (--hero-bg, --hero-glow-1..3), центр смещён к карточке.
    $g.Clear([System.Drawing.ColorTranslator]::FromHtml('#101317'))
    $glowPath = New-Object System.Drawing.Drawing2D.GraphicsPath
    $glowPath.AddEllipse(-380, -300, 1760, 1230)
    $glow = New-Object System.Drawing.Drawing2D.PathGradientBrush($glowPath)
    $glow.CenterPoint = New-Object System.Drawing.PointF(($CardX + $CardW / 2 - 140), ($H / 2))
    $glow.SurroundColors = @([System.Drawing.ColorTranslator]::FromHtml('#101317'))
    $blend = New-Object System.Drawing.Drawing2D.ColorBlend(4)
    $blend.Positions = [single[]]@(0.0, 0.18, 0.55, 1.0)
    $blend.Colors = [System.Drawing.Color[]]@(
      [System.Drawing.ColorTranslator]::FromHtml('#101317'),
      [System.Drawing.ColorTranslator]::FromHtml('#101B29'),
      [System.Drawing.ColorTranslator]::FromHtml('#102542'),
      [System.Drawing.ColorTranslator]::FromHtml('#12305A'))
    $glow.InterpolationColors = $blend
    $g.FillPath($glow, $glowPath)

    # Логотип слева — по центру свободной левой половины, в натуральном размере.
    $leftW = $CardX - $Margin
    $lx = [int][Math]::Round($Margin + ($leftW - $logo.Width) / 2)
    $ly = [int][Math]::Round(($H - $logo.Height) / 2)
    $g.DrawImage($logo, (New-Object System.Drawing.Rectangle($lx, $ly, $logo.Width, $logo.Height)), 0, 0, $logo.Width, $logo.Height, [System.Drawing.GraphicsUnit]::Pixel)

    # Тень карточки: слои с растущим контуром и малой прозрачностью, смещены вниз.
    for ($i = 16; $i -ge 1; $i--) {
      $shadow = New-RoundedPath ($CardX - $i * 2) ($CardY + 14 - $i * 2) ($CardW + $i * 4) ($CardH + $i * 4) ($Radius + $i * 2)
      $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(9, 0, 0, 0))
      $g.FillPath($brush, $shadow)
      $brush.Dispose(); $shadow.Dispose()
    }

    # Сама карточка: иллюстрация (у неё свой белый фон) со скруглёнными краями; без белой подложки — она давала светлую кайму.
    $card = New-RoundedPath $CardX $CardY $CardW $CardH $Radius
    $tex = New-Object System.Drawing.TextureBrush($scaled, [System.Drawing.Drawing2D.WrapMode]::Clamp)
    $tex.TranslateTransform($CardX, $CardY)
    $g.FillPath($tex, $card)
    $g.Dispose()

    $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
    $ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, $Quality)
    $bmp.Save($To, $codec, $ep)
    $bmp.Dispose(); $scaled.Dispose(); $tex.Dispose(); $card.Dispose(); $glow.Dispose(); $glowPath.Dispose()
  } finally {
    $logo.Dispose()
    $art.Dispose()
  }
  Write-Output ("{0} {1}x{2} q{3} {4} bytes" -f (Split-Path -Leaf $To), $W, $H, $Quality, (Get-Item $To).Length)
}

if ($Step -eq 'og') {
  New-OgPreview -To (Join-Path $Img 'og-preview.jpg') -Quality $OgQuality
} elseif ($Step -eq 'jpeg') {
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
  Resize-Image -From (Join-Path $Src 'xray-hands.jpg') -To (Join-Path $Img 'xray-hands-1000.jpg') -W 1000 -H 667 -Format jpeg -Quality 82
}
