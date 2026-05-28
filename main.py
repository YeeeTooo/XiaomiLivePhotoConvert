#!/usr/bin/env python3
"""
MVIMG 动态照片提取器 — 通用 Python 版 (跨平台)
=================================================
适用：Windows / macOS / Linux，需要 Python 3.6+

使用方法：
    python3 main.py <照片文件夹路径>
    或直接双击运行，把文件夹拖到脚本上

输出：在原文件夹中为每张 MVIMG 动态照片生成同名的 .mp4 视频文件
原图不动，可反复运行（已有 mp4 的自动跳过）。
"""

import sys, os, struct

VERSION = "1.3.0"
MP4_MAGIC = b'ftyp'


def find_mp4_offset(filepath, chunk_size=65536):
    """在 MVIMG 文件中搜索嵌入 MP4 的起始字节偏移"""
    with open(filepath, 'rb') as f:
        offset = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            pos = data.find(MP4_MAGIC)
            while pos != -1:
                if pos >= 4:
                    size_bytes = data[pos - 4:pos]
                    size = struct.unpack('>I', size_bytes)[0]
                    if 8 <= size <= 1000000:
                        return offset + pos - 4
                pos = data.find(MP4_MAGIC, pos + 1)
            offset += len(data)
    return None


def extract_video(input_path, output_path):
    """提取嵌入的 MP4 视频"""
    offset = find_mp4_offset(input_path)
    if offset is None:
        return False, 0

    file_size = os.path.getsize(input_path)
    video_size = file_size - offset

    with open(input_path, 'rb') as fin:
        fin.seek(offset)
        with open(output_path, 'wb') as fout:
            copied = 0
            while copied < video_size:
                chunk = fin.read(min(65536, video_size - copied))
                if not chunk:
                    break
                fout.write(chunk)
                copied += len(chunk)

    return True, copied


def find_mvimg_files(folder):
    return sorted(
        f for f in os.listdir(folder)
        if f.upper().startswith('MVIMG') and f.lower().endswith(('.jpg', '.jpeg'))
    )


def show_help():
    print(f"""MVIMG 动态照片提取器 v{VERSION}
═══════════════════════════════
用法:
  python3 main.py <文件夹路径>     处理文件夹中所有 MVIMG
  python3 main.py <文件路径>...     处理指定的 MVIMG 文件
  python3 main.py .                 处理当前目录
  python3 main.py --help           帮助

适用: Windows / macOS / Linux，Python 3.6+
支持拖拽文件夹或文件到脚本/应用图标上
""")


def is_mvimg_file(filepath):
    """检查文件是否是 MVIMG 动态照片"""
    name = os.path.basename(filepath)
    return name.upper().startswith('MVIMG') and name.lower().endswith(('.jpg', '.jpeg'))


def process_files(file_list):
    """处理指定的 MVIMG 文件列表（支持拖拽文件模式）"""
    # 过滤出有效的 MVIMG 文件
    valid = [f for f in file_list if os.path.isfile(f) and is_mvimg_file(f)]
    invalid = [f for f in file_list if not (os.path.isfile(f) and is_mvimg_file(f))]

    if invalid:
        print(f"⚠️  已忽略 {len(invalid)} 个非 MVIMG 文件")

    if not valid:
        print("📭 没有可处理的 MVIMG 文件")
        return

    # 按输出目录分组（同一目录的文件归到一起）
    from collections import defaultdict
    groups = defaultdict(list)
    for f in valid:
        groups[os.path.dirname(os.path.abspath(f))].append(f)

    total_ok, total_fail, total_skip = 0, 0, 0
    for folder, files in sorted(groups.items()):
        # 跳过已有 mp4 的
        todo, skipped = [], []
        for f in files:
            base = os.path.splitext(os.path.basename(f))[0]
            mp4_path = os.path.join(folder, f"{base}.mp4")
            if os.path.exists(mp4_path):
                skipped.append(f)
            else:
                todo.append((f, mp4_path))

        if skipped:
            print(f"⏭️  跳过 {len(skipped)} 张（已有 mp4）")

        if todo:
            print(f"📸 处理 {len(todo)} 张...\n")
            for src, dst in todo:
                success, size = extract_video(src, dst)
                if success:
                    print(f"  ✅ {os.path.basename(src)} → {os.path.basename(dst)} ({size/1024/1024:.1f} MB)")
                    total_ok += 1
                else:
                    print(f"  ❌ {os.path.basename(src)} → 未找到嵌入视频")
                    total_fail += 1

        total_skip += len(skipped)

    print(f"\n🎉 完成：成功 {total_ok}，失败 {total_fail}，跳过 {total_skip}")


def process_folder(folder):
    files = find_mvimg_files(folder)
    if not files:
        print(f"📭 {folder} 中没有 MVIMG 动态照片")
        return

    # 跳过已有 mp4 的
    todo, skipped = [], []
    for f in files:
        base = os.path.splitext(f)[0]
        if os.path.exists(os.path.join(folder, f"{base}.mp4")):
            skipped.append(f)
        else:
            todo.append(f)

    if skipped:
        print(f"⏭️  跳过 {len(skipped)} 张（已有 mp4）")

    if not todo:
        print("✅ 全部已处理")
        return

    print(f"📸 处理 {len(todo)} 张...\n")

    ok, fail = 0, 0
    for filename in todo:
        src = os.path.join(folder, filename)
        dst = os.path.join(folder, f"{os.path.splitext(filename)[0]}.mp4")
        success, size = extract_video(src, dst)
        if success:
            print(f"  ✅ {filename} → {os.path.basename(dst)} ({size/1024/1024:.1f} MB)")
            ok += 1
        else:
            print(f"  ❌ {filename} → 未找到嵌入视频")
            fail += 1

    print(f"\n🎉 完成：成功 {ok}，失败 {fail}，跳过 {len(skipped)}")
    print(f"   视频在: {folder}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        show_help()
        sys.exit(0)

    args = [os.path.abspath(os.path.expanduser(a)) for a in sys.argv[1:]]

    # 检测参数类型：文件夹 vs 文件
    folders = [a for a in args if os.path.isdir(a)]
    files = [a for a in args if os.path.isfile(a)]

    if files and not folders:
        # 纯文件模式（拖拽了文件）
        process_files(files)
    elif folders:
        # 文件夹模式（可能有混合输入，文件部分也处理）
        if files:
            print(f"📁 检测到 {len(folders)} 个文件夹 + {len(files)} 个文件，分别处理\n")
            process_files(files)
            print()
        for folder in folders:
            process_folder(folder)
    else:
        print(f"❌ 路径无效: {args}")
        sys.exit(1)


if __name__ == '__main__':
    main()
