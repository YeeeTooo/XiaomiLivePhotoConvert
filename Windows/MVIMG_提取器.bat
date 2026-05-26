<# :
@echo off
powershell -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Invoke-Expression ([System.IO.File]::ReadAllText('%~f0'))"
exit /b
#>
# MVIMG 动态照片提取器 — Windows 版
# 支持拖拽文件夹或文件到图标上，自动识别处理模式
# 依赖：Windows 10/11 自带 PowerShell + .NET，无需安装任何东西

Add-Type -AssemblyName System.Windows.Forms

# ══════════════════════════════
#  Detect input mode: FILE or FOLDER
# ══════════════════════════════

$droppedFiles = @()
$droppedFolders = @()

if ($args.Count -gt 0) {
    # Drag-and-drop mode: inspect each dropped item
    foreach ($arg in $args) {
        if (Test-Path $arg -PathType Leaf) {
            $droppedFiles += (Resolve-Path $arg).Path
        } elseif (Test-Path $arg -PathType Container) {
            $droppedFolders += (Resolve-Path $arg).Path
        }
    }
}

if ($droppedFiles.Count -eq 0 -and $droppedFolders.Count -eq 0) {
    # Double-click mode: show picker dialog
    $pickForm = New-Object System.Windows.Forms.Form
    $pickForm.Text = "MVIMG 提取器"
    $pickForm.Size = New-Object System.Drawing.Size(320, 160)
    $pickForm.StartPosition = "CenterScreen"
    $pickForm.FormBorderStyle = "FixedDialog"
    $pickForm.MaximizeBox = $false
    $pickForm.MinimizeBox = $false
    $pickForm.TopMost = $true

    $lblPrompt = New-Object System.Windows.Forms.Label
    $lblPrompt.Text = "请选择操作方式："
    $lblPrompt.Location = New-Object System.Drawing.Point(30, 20)
    $lblPrompt.Size = New-Object System.Drawing.Size(260, 24)
    $pickForm.Controls.Add($lblPrompt)

    $btnFolder = New-Object System.Windows.Forms.Button
    $btnFolder.Text = "选择文件夹"
    $btnFolder.Location = New-Object System.Drawing.Point(30, 55)
    $btnFolder.Size = New-Object System.Drawing.Size(110, 35)
    $btnFolder.DialogResult = [System.Windows.Forms.DialogResult]::Yes
    $pickForm.Controls.Add($btnFolder)

    $btnFile = New-Object System.Windows.Forms.Button
    $btnFile.Text = "选择文件"
    $btnFile.Location = New-Object System.Drawing.Point(160, 55)
    $btnFile.Size = New-Object System.Drawing.Size(110, 35)
    $btnFile.DialogResult = [System.Windows.Forms.DialogResult]::No
    $pickForm.Controls.Add($btnFile)

    $result = $pickForm.ShowDialog()
    $pickForm.Dispose()

    if ($result -eq 'Yes') {
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = "选择包含 MVIMG 动态照片的文件夹"
        $dialog.ShowNewFolderButton = $false
        if ($dialog.ShowDialog() -ne 'OK') { exit }
        $droppedFolders += $dialog.SelectedPath
    } elseif ($result -eq 'No') {
        $fileDialog = New-Object System.Windows.Forms.OpenFileDialog
        $fileDialog.Title = "选择 MVIMG 动态照片文件（可多选）"
        $fileDialog.Filter = "MVIMG 文件|MVIMG*.jpg;MVIMG*.jpeg|JPEG 图片|*.jpg;*.jpeg|所有文件|*.*"
        $fileDialog.Multiselect = $true
        if ($fileDialog.ShowDialog() -ne 'OK') { exit }
        $droppedFiles = $fileDialog.FileNames
    } else {
        exit
    }
}

# ══════════════════════════════
#  Core extraction function
# ══════════════════════════════

function Extract-MVIMG($filePath) {
    $mp4Path = Join-Path (Split-Path $filePath) ([System.IO.Path]::GetFileNameWithoutExtension($filePath) + '.mp4')

    if (Test-Path $mp4Path) {
        return @{ Status = "skipped" }
    }

    try {
        $bytes = [System.IO.File]::ReadAllBytes($filePath)
        $ftyp = [System.Text.Encoding]::ASCII.GetBytes('ftyp')
        $offset = -1

        for ($i = 0; $i -lt $bytes.Length - 7; $i++) {
            if ($bytes[$i] -eq $ftyp[0] -and
                $bytes[$i+1] -eq $ftyp[1] -and
                $bytes[$i+2] -eq $ftyp[2] -and
                $bytes[$i+3] -eq $ftyp[3]) {
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
            return @{ Status = "fail"; Name = [System.IO.Path]::GetFileName($filePath); Msg = "未找到嵌入视频" }
        }

        $videoSize = $bytes.Length - $offset
        $videoData = New-Object byte[] $videoSize
        [Array]::Copy($bytes, $offset, $videoData, 0, $videoSize)
        [System.IO.File]::WriteAllBytes($mp4Path, $videoData)

        return @{
            Status = "ok"
            Name = [System.IO.Path]::GetFileName($filePath)
            OutputName = [System.IO.Path]::GetFileName($mp4Path)
            SizeMB = [math]::Round($videoSize / 1MB, 1)
        }
    } catch {
        return @{ Status = "fail"; Name = [System.IO.Path]::GetFileName($filePath); Msg = $_.Exception.Message }
    }
}

function Is-MVIMG($path) {
    $name = [System.IO.Path]::GetFileName($path)
    return $name.StartsWith("MVIMG", [System.StringComparison]::OrdinalIgnoreCase) -and
           ($name.EndsWith(".jpg", [System.StringComparison]::OrdinalIgnoreCase) -or
            $name.EndsWith(".jpeg", [System.StringComparison]::OrdinalIgnoreCase))
}

# ══════════════════════════════
#  Process files mode
# ══════════════════════════════

$totalOk = 0; $totalFail = 0; $totalSkip = 0; $totalIgnored = 0
$resultsText = ""

if ($droppedFiles.Count -gt 0) {
    # Filter to valid MVIMG files only
    $validFiles = @()
    foreach ($f in $droppedFiles) {
        if (Is-MVIMG $f) {
            $validFiles += $f
        } else {
            $totalIgnored++
        }
    }

    if ($totalIgnored -gt 0) {
        $resultsText += "⚠️  已忽略 $totalIgnored 个非 MVIMG 文件`n`n"
    }

    if ($validFiles.Count -eq 0 -and $droppedFolders.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show(
            "选中的文件中没有 MVIMG 动态照片。`n`n提示：文件名需要以 MVIMG 开头且为 .jpg/.jpeg 格式。",
            "MVIMG 提取器",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        )
        exit
    }

    foreach ($file in $validFiles) {
        $r = Extract-MVIMG $file
        switch ($r.Status) {
            "ok" {
                $totalOk++
                $resultsText += "  ✅  $($r.Name) → $($r.OutputName) ($($r.SizeMB) MB)`n"
            }
            "fail" {
                $totalFail++
                $resultsText += "  ❌  $($r.Name) — $($r.Msg)`n"
            }
            "skipped" { $totalSkip++ }
        }
    }
}

# ══════════════════════════════
#  Process folder(s) mode
# ══════════════════════════════

if ($droppedFolders.Count -gt 0) {
    foreach ($folder in $droppedFolders) {
        $files = Get-ChildItem -Path $folder -Filter "MVIMG*.jpg" | Sort-Object Name
        if (-not $files) {
            $files = Get-ChildItem -Path $folder -Filter "MVIMG*.jpeg" | Sort-Object Name
        }

        if (-not $files) {
            $resultsText += "📭 $folder 中没有 MVIMG 文件`n`n"
            continue
        }

        $folderResults = ""
        foreach ($file in $files) {
            $r = Extract-MVIMG $file.FullName
            switch ($r.Status) {
                "ok" {
                    $totalOk++
                    $folderResults += "  ✅  $($r.Name) → $($r.OutputName) ($($r.SizeMB) MB)`n"
                }
                "fail" {
                    $totalFail++
                    $folderResults += "  ❌  $($r.Name) — $($r.Msg)`n"
                }
                "skipped" { $totalSkip++ }
            }
        }

        $resultsText += "📁 $folder`n$folderResults`n"
    }
}

# ══════════════════════════════
#  Show results
# ══════════════════════════════

$summary = "✅ 成功：$totalOk 段视频`n❌ 失败：$totalFail`n⏭ 跳过（已有）：$totalSkip"
if ($totalIgnored -gt 0) {
    $summary += "`n⚠️ 忽略：$totalIgnored 个非 MVIMG 文件"
}
$summary += "`n`n$resultsText"

$btnText = if ($droppedFolders.Count -gt 0) { "是" } else { "确定" }

$resultDlg = [System.Windows.Forms.MessageBox]::Show(
    $summary,
    "MVIMG 提取器 — 完成",
    if ($droppedFolders.Count -gt 0) { [System.Windows.Forms.MessageBoxButtons]::YesNo } else { [System.Windows.Forms.MessageBoxButtons]::OK },
    [System.Windows.Forms.MessageBoxIcon]::Information
)

if ($droppedFolders.Count -gt 0 -and $resultDlg -eq 'Yes') {
    Start-Process explorer.exe -ArgumentList $droppedFolders[0]
}
