<# :
@echo off
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Invoke-Expression ([System.IO.File]::ReadAllText('%~f0'))"
exit /b
#>
# MVIMG 动态照片提取器 — Windows 版
# 双击运行，选择文件夹，自动提取所有 MVIMG 动态照片的视频
# 依赖：Windows 10/11 自带 PowerShell + .NET，无需安装任何东西

Add-Type -AssemblyName System.Windows.Forms

# ─── 选择文件夹 ───
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = "选择包含 MVIMG 动态照片的文件夹"
$dialog.ShowNewFolderButton = $false

if ($dialog.ShowDialog() -ne 'OK') {
    exit
}

$folder = $dialog.SelectedPath

# ─── 查找 MVIMG 文件 ───
$files = Get-ChildItem -Path $folder -Filter "MVIMG*.jpg" | Sort-Object Name
if (-not $files) {
    $files = Get-ChildItem -Path $folder -Filter "MVIMG*.jpeg" | Sort-Object Name
}
if (-not $files) {
    [System.Windows.Forms.MessageBox]::Show(
        "该文件夹中未找到 MVIMG 开头的动态照片。`n`n提示：小米动态照片文件名以 MVIMG 开头。",
        "MVIMG 提取器",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Information
    )
    exit
}

# ─── 提取视频 ───
$total = $files.Count
$ok = 0
$fail = 0
$skip = 0
$results = @()

foreach ($file in $files) {
    $mp4Path = Join-Path $folder ($file.BaseName + '.mp4')
    
    if (Test-Path $mp4Path) {
        $skip++
        continue
    }
    
    try {
        $bytes = [System.IO.File]::ReadAllBytes($file.FullName)
        
        # 搜索 ftyp 标记（MP4 文件头）
        $ftyp = [System.Text.Encoding]::ASCII.GetBytes('ftyp')
        $offset = -1
        
        for ($i = 0; $i -lt $bytes.Length - 7; $i++) {
            if ($bytes[$i] -eq $ftyp[0] -and 
                $bytes[$i+1] -eq $ftyp[1] -and 
                $bytes[$i+2] -eq $ftyp[2] -and 
                $bytes[$i+3] -eq $ftyp[3]) {
                # 验证 ftyp box 的 size 字段
                if ($i -ge 4) {
                    $size = ([uint32]$bytes[$i-4] -shl 24) -bor 
                            ([uint32]$bytes[$i-3] -shl 16) -bor 
                            ([uint32]$bytes[$i-2] -shl 8) -bor 
                            [uint32]$bytes[$i-1]
                    if ($size -ge 8 -and $size -le 1000000) {
                        $offset = $i - 4
                        break
                    }
                }
            }
        }
        
        if ($offset -lt 0) {
            $fail++
            $results += "  ❌  $($file.Name) — 未找到嵌入视频"
            continue
        }
        
        $videoSize = $bytes.Length - $offset
        $videoData = New-Object byte[] $videoSize
        [Array]::Copy($bytes, $offset, $videoData, 0, $videoSize)
        [System.IO.File]::WriteAllBytes($mp4Path, $videoData)
        
        $sizeMB = [math]::Round($videoSize / 1MB, 1)
        $ok++
        $results += "  ✅  $($file.Name) → $($file.BaseName).mp4 ($sizeMB MB)"
    }
    catch {
        $fail++
        $results += "  ❌  $($file.Name) — 处理错误: $($_.Exception.Message)"
    }
}

# ─── 显示结果 ───
$summary = "✅ 成功：$ok 段视频`n❌ 失败：$fail`n⏭ 跳过（已有）：$skip`n`n共扫描 $total 张动态照片`n`n视频保存在：`n$folder"

$result = [System.Windows.Forms.MessageBox]::Show(
    $summary,
    "MVIMG 提取器 — 完成",
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Information
)

if ($result -eq 'Yes') {
    Start-Process explorer.exe -ArgumentList $folder
}
