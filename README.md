# 小米动态照片导出工具

> 一键把小米/红米手机拍的动态照片（MVIMG）拆成「照片 + 视频」两个文件。

---

## 我不是程序员

我不懂编程。只是自己用小米手机拍了很多动态照片，发现电脑上只能看到 `.jpg`，视频部分没法直接看。试了一圈也没找到好用的工具，就让 [WorkBuddy](https://www.codebuddy.cn) 帮我写了一个。

**这个工具目前是 v1.1.0，支持拖拽文件夹或单个文件。** 如果你遇到问题，欢迎提 [Issue](https://github.com/YeeeTooo/XiaomiLivePhotoConvert/issues)，我会尽量修。

---

## 它做了什么

```
MVIMG_20250101.jpg  ──→  MVIMG_20250101.jpg（原图不动）
                    ──→  MVIMG_20250101.mp4（提取的视频）
```

不转码、不压缩，就是从 JPG 文件尾部把 MP4 数据原样切出来。视频质量和你手机拍出来一模一样。

---

## 下载使用

> **目前只有 macOS 版**，Windows 版还在调试，敬请期待。

👉 [**前往 Releases 下载**](https://github.com/YeeeTooo/XiaomiLivePhotoConvert/releases)

### macOS 使用方法

1. 下载 `XiaomiLivePhotoConvert_macOS.dmg`，双击打开
2. 把 `XiaomiLivePhotoConvert` 拖到 `Applications` 文件夹（和普通 Mac 软件一样）
3. 从启动台打开 App → 选择装了 MVIMG 照片的文件夹 → 完成

> 所有 Mac 自带 Python 3，零依赖，绿色免安装。

---

## 原理说明

小米 MVIMG 文件本质是 JPG 图片后面拼接了一段 MP4 视频数据。工具扫描 MP4 特征标记（`ftyp`），找到视频起始位置，逐字节复制出来。全程没有重新编码，所以无损。

提取的视频参数保留手机原始规格：H.264 编码、1080×1440 分辨率、约 30fps，时长 2~3 秒。

---

## 已知问题

- Windows 版功能不完善，暂未发布
- 仅测试了小米 17 Ultra，其他机型未验证
- 如果 MVIMG 文件被某些软件处理过（压缩/编辑），可能无法识别视频数据

---

## 感谢

- 由 [WorkBuddy](https://www.codebuddy.cn) 辅助编写
- MIT 开源，随便用
