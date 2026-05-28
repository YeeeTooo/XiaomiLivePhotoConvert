#!/usr/bin/env python3
"""
MiExt GUI v8 — 现代风格 MVIMG 动态照片提取器
Tk 9.0.3 完整版，匹配参考设计稿
"""

import os
import sys
import struct
import tkinter as tk
from tkinter import filedialog, messagebox

VERSION = "1.3.0"
MP4_MAGIC = b'ftyp'

# ─── Colors ───
BG          = '#F5F5F7'
WHITE       = '#FFFFFF'
BORDER      = '#E5E5EA'
TEXT_DARK   = '#1D1D1F'
TEXT_GRAY   = '#86868B'
TEXT_SUB    = '#6E6E73'
BLUE        = '#007AFF'
GREEN       = '#34C759'
ORANGE      = '#FF9500'
BLUE_BTN    = '#007AFF'
BLUE_HOV    = '#0051D5'
GRAY_BTN    = '#F2F2F7'
GRAY_HOV    = '#E5E5EA'
DISABLED    = '#C7C7CC'

# ─── Fonts ───
F_TITLE = ('Helvetica', 15, 'bold')
F_BODY  = ('Helvetica', 13)
F_SMALL = ('Helvetica', 11)
F_TINY  = ('Helvetica', 10)
F_NUM   = ('Helvetica', 36, 'bold')
F_BTN   = ('Helvetica', 12)


def find_mp4_offset(filepath):
    with open(filepath, 'rb') as f:
        offset = 0
        while True:
            data = f.read(65536)
            if not data:
                break
            pos = data.find(MP4_MAGIC)
            while pos != -1:
                if pos >= 4:
                    size = struct.unpack('>I', data[pos-4:pos])[0]
                    if 8 <= size <= 1000000:
                        return offset + pos - 4
                pos = data.find(MP4_MAGIC, pos + 1)
            offset += len(data)
    return None


def extract_video(input_path, output_path):
    offset = find_mp4_offset(input_path)
    if offset is None:
        return False, 0
    video_size = os.path.getsize(input_path) - offset
    with open(input_path, 'rb') as fin:
        fin.seek(offset)
        video_data = fin.read(video_size)
    with open(output_path, 'wb') as fout:
        fout.write(video_data)
    return True, video_size


def find_mvimg_files(folder):
    skip = {'.ds_store', 'thumbs.db', 'desktop.ini'}
    return sorted(
        f for f in os.listdir(folder)
        if not f.startswith('.')
        and f.lower() not in skip
        and f.upper().startswith('MVIMG')
        and f.lower().endswith(('.jpg', '.jpeg'))
    )


def is_mvimg(filepath):
    fname = os.path.basename(filepath)
    if not (fname.upper().startswith('MVIMG') and fname.lower().endswith(('.jpg', '.jpeg'))):
        return False
    return find_mp4_offset(filepath) is not None


# ─── GUI ───

class MiExtGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MiExt")
        self.root.geometry("720x420")
        self.root.configure(bg=BG)
        self.root.minsize(620, 360)
        self.root.resizable(True, True)

        self.folder_path = tk.StringVar()
        self.single_file = None
        self.scan_data = None
        self.is_single_mode = False

        self._build_ui()

    def _build_ui(self):
        # ════════════ 主内容卡片（白色背景） ════════════
        card = tk.Frame(self.root, bg=WHITE, bd=1, relief='solid')
        card.pack(fill='both', expand=True, padx=24, pady=(20, 0))

        inner = tk.Frame(card, bg=WHITE)
        inner.pack(fill='both', expand=True, padx=20, pady=18)

        # ── 文件夹选择行 ──
        sel = tk.Frame(inner, bg=WHITE)
        sel.pack(fill='x')

        # 文件夹图标（Canvas 绘制）
        icon_frame = tk.Frame(sel, bg=WHITE, width=44, height=44)
        icon_frame.pack(side='left', padx=(0, 12))
        icon_frame.pack_propagate(False)
        self.folder_cv = tk.Canvas(icon_frame, width=40, height=36,
                                   bg=WHITE, highlightthickness=0)
        self.folder_cv.pack(expand=True)
        self._draw_folder_icon(BLUE)

        # 文字信息
        info = tk.Frame(sel, bg=WHITE)
        info.pack(side='left', fill='x', expand=True)

        self.sel_title = tk.Label(info, text="未选择文件夹",
                                  font=F_BODY, bg=WHITE, fg=TEXT_DARK,
                                  anchor='w')
        self.sel_title.pack(fill='x')

        self.sel_path = tk.Label(info,
            text="点击底部按钮选择包含 MVIMG 照片的文件夹",
            font=F_SMALL, bg=WHITE, fg=TEXT_GRAY, anchor='w')
        self.sel_path.pack(fill='x', pady=(2, 0))

        # ── 统计文字 ──
        self.stats_lbl = tk.Label(inner, text=" ", font=F_SMALL,
                                  bg=WHITE, fg=TEXT_SUB, anchor='w')
        self.stats_lbl.pack(fill='x', pady=(14, 10))

        # ── 双统计卡片 ──
        cards = tk.Frame(inner, bg=WHITE)
        cards.pack(fill='x')
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        # 左：可转换
        ok_card = tk.Frame(cards, bg=WHITE, bd=1, relief='solid')
        ok_card.grid(row=0, column=0, sticky='new', padx=(0, 8))

        ok_top = tk.Frame(ok_card, bg=WHITE)
        ok_top.pack(fill='x', padx=16, pady=(14, 0))
        tk.Label(ok_top, text="OK", font=('Helvetica', 12, 'bold'),
                bg=WHITE, fg=GREEN).pack(side='left')
        tk.Label(ok_top, text="  可转换", font=F_SMALL,
                bg=WHITE, fg=TEXT_DARK).pack(side='left')

        self.ok_num = tk.Label(ok_card, text="0", font=F_NUM,
                              bg=WHITE, fg=GREEN)
        self.ok_num.pack(anchor='w', padx=16, pady=(6, 0))
        self.ok_sub = tk.Label(ok_card, text="将被转换", font=F_TINY,
                              bg=WHITE, fg=TEXT_GRAY)
        self.ok_sub.pack(anchor='w', padx=16, pady=(0, 14))

        # 右：不可转换
        ng_card = tk.Frame(cards, bg=WHITE, bd=1, relief='solid')
        ng_card.grid(row=0, column=1, sticky='new')

        ng_top = tk.Frame(ng_card, bg=WHITE)
        ng_top.pack(fill='x', padx=16, pady=(14, 0))
        tk.Label(ng_top, text="!", font=('Helvetica', 13, 'bold'),
                bg=WHITE, fg=ORANGE).pack(side='left')
        tk.Label(ng_top, text="  不可转换", font=F_SMALL,
                bg=WHITE, fg=TEXT_DARK).pack(side='left')

        self.ng_num = tk.Label(ng_card, text="0", font=F_NUM,
                              bg=WHITE, fg=ORANGE)
        self.ng_num.pack(anchor='w', padx=16, pady=(6, 0))
        self.ng_sub = tk.Label(ng_card, text="其他文件或已转换", font=F_TINY,
                              bg=WHITE, fg=TEXT_GRAY)
        self.ng_sub.pack(anchor='w', padx=16, pady=(0, 14))

        # ════════════ 底部按钮 ════════════
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill='x', padx=24, pady=(16, 16))
        bar.columnconfigure(0, weight=1)
        bar.columnconfigure(1, weight=1)
        bar.columnconfigure(2, weight=1)

        # 打开文件
        self.btn_file = tk.Button(bar, text="打开文件\n选择单个文件",
            font=F_BTN, bg=GRAY_BTN, fg=TEXT_DARK,
            bd=1, relief='solid',
            activebackground=GRAY_HOV,
            command=self.select_single_file)
        self.btn_file.grid(row=0, column=0, sticky='ew', padx=(0, 8))

        # 打开文件夹
        self.btn_folder = tk.Button(bar, text="打开文件夹\n批量转换文件",
            font=F_BTN, bg=GRAY_BTN, fg=TEXT_DARK,
            bd=1, relief='solid',
            activebackground=GRAY_HOV,
            command=self.select_folder)
        self.btn_folder.grid(row=0, column=1, sticky='ew', padx=(0, 8))

        # 开始转换（蓝色主按钮）
        self.btn_convert = tk.Button(bar, text="开始转换",
            font=('Helvetica', 13, 'bold'),
            bg='#F2F2F7', fg='#C7C7CC',
            disabledforeground='#C7C7CC',
            bd=1, relief='solid',
            state='disabled',
            command=self.convert)
        self.btn_convert.grid(row=0, column=2, sticky='ew')

        self._reset_ui()

    def _draw_folder_icon(self, color):
        c = self.folder_cv
        c.delete('all')
        # 文件夹主体
        c.create_rectangle(2, 12, 34, 32, fill=color, outline='')
        # 文件夹标签页
        c.create_polygon(2, 12, 12, 12, 18, 5, 30, 5, 30, 12,
                        fill=color, outline='')

    def _reset_ui(self):
        self.folder_path.set("")
        self.single_file = None
        self.scan_data = None
        self.is_single_mode = False
        self.sel_title.config(text="未选择文件夹")
        self.sel_path.config(text="点击底部按钮选择包含 MVIMG 照片的文件夹")
        self.stats_lbl.config(text=" ")
        self.ok_num.config(text="0")
        self.ng_num.config(text="0")
        self.ok_sub.config(text="将被转换")
        self.ng_sub.config(text="其他文件或已转换")
        self._set_convert_enabled(False)

    def _set_convert_enabled(self, enabled):
        self._cvt_enabled = enabled
        if enabled:
            self.btn_convert.config(
                bg='#007AFF', fg='white',
                font=('Helvetica', 15, 'bold'),
                bd=0, relief='flat',
                state='normal', text="▶  开始转换")
        else:
            self.btn_convert.config(
                bg='#F2F2F7', fg='#C7C7CC',
                font=('Helvetica', 13, 'bold'),
                bd=1, relief='solid',
                state='disabled', text="开始转换")

    # ──────────────────── 选择与扫描 ────────────────────

    def select_folder(self):
        folder = filedialog.askdirectory(title="选择包含 MVIMG 动态照片的文件夹")
        if folder:
            self.is_single_mode = False
            self.single_file = None
            self.folder_path.set(folder)
            self.sel_title.config(text="已选择文件夹")
            display = folder if len(folder) <= 55 else "..." + folder[-52:]
            self.sel_path.config(text=display)
            self._scan_folder()

    def select_single_file(self):
        fpath = filedialog.askopenfilename(
            title="选择单个 MVIMG 动态照片",
            filetypes=[("JPEG 图片", "*.jpg *.jpeg"), ("所有文件", "*.*")]
        )
        if fpath:
            self.is_single_mode = True
            self.single_file = fpath
            self.folder_path.set(os.path.dirname(fpath))
            self.sel_title.config(text="已选择文件")
            display = fpath if len(fpath) <= 55 else "..." + fpath[-52:]
            self.sel_path.config(text=display)
            self._scan_single_file(fpath)

    def _scan_folder(self):
        folder = self.folder_path.get()
        if not folder or not os.path.isdir(folder):
            return
        self.log("")
        self.log(f"正在扫描：{folder}")

        # 1. 过滤系统文件和隐藏文件
        skip = {'.ds_store', 'thumbs.db', 'desktop.ini'}
        visible = [f for f in os.listdir(folder)
                   if not f.startswith('.') and f.lower() not in skip]

        # 2. 只统计图片文件（mp4 等输出文件不计入）
        image_exts = ('.jpg', '.jpeg', '.png', '.heic', '.webp')
        all_images = [f for f in visible if f.lower().endswith(image_exts)]

        # 3. MVIMG 文件
        mvimg_files = [f for f in all_images if f.upper().startswith('MVIMG')]

        # 4. 非 MVIMG 图片
        non_mvimg = [f for f in all_images if not f.upper().startswith('MVIMG')]

        # 5. 分析 MVIMG：可转换 vs 已转换
        convertible = 0
        already = 0
        for f in mvimg_files:
            base = os.path.splitext(f)[0]
            if os.path.exists(os.path.join(folder, f"{base}.mp4")):
                already += 1
            else:
                convertible += 1

        # 6. 不可转换 = 非MVIMG图片 + 已转换的MVIMG
        not_convertible = len(non_mvimg) + already

        # 7. 智能描述文字
        if already > 0 and len(non_mvimg) > 0:
            ng_desc = f"已转换 {already} 个，其他 {len(non_mvimg)} 个"
        elif already > 0:
            ng_desc = f"已转换 {already} 个"
        elif len(non_mvimg) > 0:
            ng_desc = f"其他文件 {len(non_mvimg)} 个"
        else:
            ng_desc = "其他文件或已转换"

        self.stats_lbl.config(text=f"共 {len(all_images)} 个文件，分析完成")
        self.ok_num.config(text=str(convertible))
        self.ng_num.config(text=str(not_convertible))
        self.ok_sub.config(text="将被转换")
        self.ng_sub.config(text=ng_desc)

        self.scan_data = {
            'folder': folder,
            'mvimg_files': mvimg_files,
            'convertible': convertible,
            'mode': 'folder',
        }

        total_mvimg = len(mvimg_files)
        if convertible > 0:
            self._set_convert_enabled(True)
            self.log(f"[OK] 发现 {convertible} 张可转换的动态照片")
        else:
            self._set_convert_enabled(False)
            if total_mvimg > 0:
                self.log("[INFO] 所有动态照片已转换完成")
            else:
                self.log("[WARN] 未找到 MVIMG 动态照片")

    def _scan_single_file(self, fpath):
        self.log("")
        self.log(f"正在检查：{os.path.basename(fpath)}")

        folder = os.path.dirname(fpath)
        fname = os.path.basename(fpath)

        convertible_flag = is_mvimg(fpath)
        base = os.path.splitext(fname)[0]
        has_mp4 = os.path.exists(os.path.join(folder, f"{base}.mp4"))

        if convertible_flag and not has_mp4:
            convertible, not_convertible = 1, 0
            self.log("[OK] 该文件包含可提取的视频")
        else:
            convertible, not_convertible = 0, 1
            if has_mp4:
                self.log("[INFO] 该文件已转换过")
            else:
                self.log("[WARN] 该文件不包含可提取的视频")

        self.stats_lbl.config(text="共 1 个文件，分析完成")
        self.ok_num.config(text=str(convertible))
        self.ng_num.config(text=str(not_convertible))
        self.ok_sub.config(text="将被转换" if convertible else "")
        self.ng_sub.config(text="已转换或非MVIMG" if not_convertible else "")

        self.scan_data = {
            'folder': folder,
            'file': fpath,
            'convertible': convertible,
            'mode': 'single',
        }

        if convertible > 0:
            self._set_convert_enabled(True)
        else:
            self._set_convert_enabled(False)

    # ──────────────────── 日志 ────────────────────

    def log(self, message):
        print(f"[MiExt] {message}")

    # ──────────────────── 转换 ────────────────────

    def convert(self):
        if not self.scan_data:
            return
        if self.scan_data.get('mode') == 'single':
            self._convert_single()
        else:
            self._convert_folder()

    def _convert_single(self):
        fpath = self.scan_data['file']
        folder = self.scan_data['folder']
        fname = os.path.basename(fpath)
        base = os.path.splitext(fname)[0]
        mp4_path = os.path.join(folder, f"{base}.mp4")

        if not messagebox.askyesno("确认转换",
            f"即将转换：{fname}\n\n输出位置：\n{folder}\n\n是否继续？"):
            return

        self._set_convert_enabled(False)
        self.log("")
        self.log("=" * 40)
        self.log("开始转换...")
        self.log(f"处理：{fname}")

        success, size = extract_video(fpath, mp4_path)
        if success:
            size_mb = size / 1024 / 1024
            self.log(f"  [OK] {base}.mp4 ({size_mb:.1f} MB)")
            messagebox.showinfo("转换完成",
                f"转换成功！\n\n{base}.mp4\n({size_mb:.1f} MB)\n\n已保存在：\n{folder}")
        else:
            self.log(f"  [FAIL] 未找到嵌入视频")
            messagebox.showerror("转换失败",
                f"未能在 {fname} 中找到嵌入的视频数据。")

        self._scan_single_file(fpath)

    def _convert_folder(self):
        folder = self.scan_data['folder']
        mvimg_files = self.scan_data['mvimg_files']
        convertible = self.scan_data['convertible']

        if not messagebox.askyesno("确认转换",
            f"即将转换 {convertible} 张动态照片\n\n"
            f"输出位置：\n{folder}\n\n是否继续？"):
            return

        self._set_convert_enabled(False)
        self.log("")
        self.log("=" * 40)
        self.log("开始转换...")

        ok, fail = 0, 0
        for filename in mvimg_files:
            base = os.path.splitext(filename)[0]
            mp4_path = os.path.join(folder, f"{base}.mp4")
            if os.path.exists(mp4_path):
                continue
            src = os.path.join(folder, filename)
            self.log(f"处理：{filename}")
            success, size = extract_video(src, mp4_path)
            if success:
                size_mb = size / 1024 / 1024
                self.log(f"  [OK] {os.path.basename(mp4_path)} ({size_mb:.1f} MB)")
                ok += 1
            else:
                self.log(f"  [FAIL] 未找到嵌入视频")
                fail += 1

        self.log("")
        self.log("=" * 40)
        self.log("转换完成！")
        self.log(f"  成功：{ok} 张")
        self.log(f"  失败：{fail} 张")
        self.log(f"  视频保存在：{folder}")

        messagebox.showinfo("转换完成",
            f"转换完成！\n\n成功：{ok} 张\n失败：{fail} 张\n\n"
            f"视频已保存在：\n{folder}")

        self._scan_folder()


def main():
    root = tk.Tk()
    MiExtGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
