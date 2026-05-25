# MVIMG Extractor

一键提取小米/红米手机动态照片（MVIMG）中的视频，**不转码、不压缩、逐字节无损**。

> 小米手机拍摄的动态照片本质是「JPG + MP4」的拼接文件，在电脑上只能看到 `.jpg`。本工具从 JPG 尾部无损切出 MP4 视频，质量与手机内置「保存为视频」完全一致。

## 特性

- **无损提取** — 不重新编码，逐字节复制，MD5 完全一致
- **批处理** — 一次处理整个文件夹，可反复运行（已提取的自动跳过）
- **零依赖** — Windows 版依赖自带 PowerShell，macOS 版依赖自带 Python 3
- **拖拽即用** — 不需要命令行

## 快速开始

### Windows

1. 下载 `Windows/MVIMG_提取器.bat`
2. **双击运行** → 选择照片文件夹 → 等待完成
3. 提取的 `.mp4` 文件在原图旁边

> Windows 10/11 自带 PowerShell，无需安装任何东西。

### macOS

1. 下载 `macOS/MVIMG Extractor.app`
2. **双击运行** → 选择照片文件夹 → 等待完成弹窗
3. 点击「打开文件夹」直接查看视频

> 所有 Mac 自带 Python 3（`/usr/bin/python3`），无需安装任何东西。

### 命令行（跨平台）

```bash
python3 mvimg-extract.py /path/to/photos/
```

- `python3 mvimg-extract.py` — 处理当前目录
- `python3 mvimg-extract.py ~/Desktop/photos` — 处理指定目录
- `python3 mvimg-extract.py --status` — 只看不处理

## 原理

```
MVIMG_20250101_120000.jpg
┌──────────────────────────────┐
│  JPEG 图片数据  │  MP4 视频   │
│  (静态预览)    │  (H.264+AAC)│
└──────────────────────────────┘
                      ↓
               按字节切分，原样复制
                      ↓
              MVIMG_20250101_120000.mp4
```

脚本扫描 MP4 特征标记 `ftyp`，定位视频数据的准确起始偏移，然后逐字节复制出来。

## 视频参数

提取的视频保留手机原始录制参数：

| 属性 | 典型值 |
|------|--------|
| 编码 | H.264 + AAC |
| 分辨率 | 1080×1440（竖屏） |
| 帧率 | ~30fps |
| 时长 | 约 2~3 秒 |

## 文件结构

```
mvimg-extractor/
├── README.md
├── mvimg-extract.py          # 命令行通用版
├── Windows/
│   ├── MVIMG_提取器.bat       # 主力：双击即用
│   └── mvimg-extract.py      # 备用
└── macOS/
    └── MVIMG Extractor.app   # 主力：双击即用
```

## License

MIT
