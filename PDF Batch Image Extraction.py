import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor, as_completed
import fitz  # PyMuPDF
from pathlib import Path

MAX_THREADS = 8  # 可根据 CPU 核心数调整


def extract_images_from_pdf(pdf_path, output_folder):
    try:
        pdf_name = pdf_path.stem
        relative_path = pdf_path.relative_to(source_folder)
        pdf_output_dir = output_folder / relative_path.parent / pdf_name
        pdf_output_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(pdf_path)
        img_count = 0
        for page_index in range(len(doc)):
            page = doc[page_index]
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                img_count += 1
                img_filename = pdf_output_dir / f"image_{img_count}.{image_ext}"
                with open(img_filename, "wb") as img_file:
                    img_file.write(image_bytes)
        doc.close()
    except Exception as e:
        print(f"处理失败: {pdf_path} 错误: {e}")


def process_pdfs():
    status_label.config(text="正在提取图片，请稍等...")
    extract_button.config(state=tk.DISABLED)

    def worker():
        pdf_paths = list(Path(source_folder).rglob("*.pdf"))
        total = len(pdf_paths)
        completed = 0

        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            future_to_pdf = {executor.submit(extract_images_from_pdf, path, Path(output_folder)): path for path in
                             pdf_paths}
            for future in as_completed(future_to_pdf):
                completed += 1
                status_label.config(text=f"处理中... {completed}/{total}")

        status_label.config(text="提取完成！")
        extract_button.config(state=tk.NORMAL)
        messagebox.showinfo("完成", f"{total} 个 PDF 处理完成！")

    threading.Thread(target=worker).start()


def choose_source_folder():
    global source_folder
    selected = filedialog.askdirectory()
    if selected:
        source_folder = selected
        source_label.config(text=f"源目录: {source_folder}")


def choose_output_folder():
    global output_folder
    selected = filedialog.askdirectory()
    if selected:
        output_folder = selected
        output_label.config(text=f"输出目录: {output_folder}")


# 初始化 UI
root = tk.Tk()
root.title("PDF 图片提取器（多线程）")
root.geometry("500x320")
root.resizable(False, False)

source_folder = ""
output_folder = ""

# UI 布局
tk.Label(root, text="PDF 图片批量提取器（多线程加速）", font=("Helvetica", 15, "bold")).pack(pady=10)

tk.Button(root, text="选择源目录", command=choose_source_folder, width=22).pack(pady=5)
source_label = tk.Label(root, text="源目录: 未选择", wraplength=460, anchor="w", justify="left")
source_label.pack()

tk.Button(root, text="选择输出目录", command=choose_output_folder, width=22).pack(pady=5)
output_label = tk.Label(root, text="输出目录: 未选择", wraplength=460, anchor="w", justify="left")
output_label.pack()

extract_button = tk.Button(root, text="开始提取", command=process_pdfs, width=22, bg="#4CAF50", fg="white")
extract_button.pack(pady=15)

status_label = tk.Label(root, text="")
status_label.pack()

root.mainloop()
