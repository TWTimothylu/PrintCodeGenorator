import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os

class PrintCodeGeneratorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Pybricks 列印碼產生器")
        self.master.geometry("800x600")

        # --- 常數設定 ---
        self.PREVIEW_MAX_SIZE = (350, 350)

        # --- 資料變數 ---
        self.original_image = None
        self.processed_image = None
        self.file_path = None

        # --- Tkinter 控制變數 ---
        self.threshold_var = tk.IntVar(value=128)
        self.width_var = tk.StringVar(value="100")
        self.height_var = tk.StringVar(value="100")
        self.mirror_var = tk.BooleanVar(value=False)

        # --- 建立介面 ---
        self._create_widgets()

    def _create_widgets(self):
        # ... (此處的介面佈局程式碼與之前完全相同，為節省篇幅故省略) ...
        # ... (The UI layout code here is identical to before, omitted for brevity) ...
        # --- 主框架 ---
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. 控制面板 (右側) ---
        control_panel = ttk.Frame(main_frame, padding="10")
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        ttk.Label(control_panel, text="控制面板", font=("Arial", 16, "bold")).pack(pady=(0, 10))

        ttk.Button(control_panel, text="載入圖片", command=self.load_image).pack(fill=tk.X, pady=5)
        
        res_frame = ttk.LabelFrame(control_panel, text="解析度")
        res_frame.pack(fill=tk.X, pady=10)
        ttk.Label(res_frame, text="寬:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(res_frame, textvariable=self.width_var, width=5).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(res_frame, text="高:").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(res_frame, textvariable=self.height_var, width=5).grid(row=0, column=3, padx=5, pady=5)

        thresh_frame = ttk.LabelFrame(control_panel, text="二值化閾值")
        thresh_frame.pack(fill=tk.X, pady=10)
        self.threshold_label = ttk.Label(thresh_frame, text=f"目前: {self.threshold_var.get()}")
        self.threshold_label.pack()
        ttk.Scale(thresh_frame, from_=0, to=255, orient=tk.HORIZONTAL, variable=self.threshold_var, command=self.update_preview).pack(fill=tk.X, padx=5, pady=5)

        ttk.Checkbutton(control_panel, text="水平鏡像", variable=self.mirror_var, command=self.update_preview).pack(pady=10)
        ttk.Button(control_panel, text="更新預覽", command=self.update_preview).pack(fill=tk.X, pady=5)
        self.save_button = ttk.Button(control_panel, text="儲存 Print Code", command=self.save_print_code, state=tk.DISABLED)
        self.save_button.pack(fill=tk.X, pady=20)

        # --- 2. 圖片預覽區 (左側) ---
        preview_panel = ttk.Frame(main_frame)
        preview_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        original_frame = ttk.LabelFrame(preview_panel, text="原始圖片")
        original_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.original_label = ttk.Label(original_frame, text="請載入圖片")
        self.original_label.pack(expand=True)

        binary_frame = ttk.LabelFrame(preview_panel, text="二值化預覽")
        binary_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.binary_label = ttk.Label(binary_frame, text="預覽將顯示於此")
        self.binary_label.pack(expand=True)

        # --- 3. 狀態列 ---
        self.status_var = tk.StringVar(value="準備就緒")
        ttk.Label(self.master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)


    def _calculate_aspect_ratio_size(self, original_width, original_height):
        """計算保持長寬比的顯示尺寸"""
        max_w, max_h = self.PREVIEW_MAX_SIZE
        ratio = min(max_w / original_width, max_h / original_height)
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        return (new_width, new_height)

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="選擇圖片",
            filetypes=[("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.gif"), ("所有檔案", "*.*")]
        )
        if not file_path: return
        self.file_path = file_path
        try:
            self.original_image = Image.open(self.file_path)
            
            # --- 變更點 1 ---
            # 顯示原始圖縮圖，保持長寬比
            display_size = self._calculate_aspect_ratio_size(self.original_image.width, self.original_image.height)
            thumb_orig = self.original_image.copy()
            thumb_orig.thumbnail(display_size, Image.Resampling.LANCZOS) # 使用 thumbnail 更安全
            
            self.photo_orig = ImageTk.PhotoImage(thumb_orig)
            self.original_label.config(image=self.photo_orig, text="")
            
            self.status_var.set(f"已載入: {os.path.basename(self.file_path)}")
            self.save_button.config(state=tk.NORMAL)
            self.update_preview()
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟圖片檔案:\n{e}")
            self.status_var.set("圖片載入失敗")

    def update_preview(self, _=None):
        if not self.original_image: return
        try:
            self.threshold_label.config(text=f"目前: {self.threshold_var.get()}")
            width, height = int(self.width_var.get()), int(self.height_var.get())
            threshold, mirror = self.threshold_var.get(), self.mirror_var.get()

            img = self.original_image.copy()
            if mirror: img = img.transpose(Image.FLIP_LEFT_RIGHT)
            
            self.processed_image = img.convert('L').resize((width, height))
            binary_img = self.processed_image.point(lambda p: 255 if p > threshold else 0, '1')

            # --- 變更點 2 ---
            # 顯示二值化預覽圖，保持設定的長寬比
            display_size = self._calculate_aspect_ratio_size(width, height)
            display_img = binary_img.resize(display_size, Image.Resampling.NEAREST)

            self.photo_binary = ImageTk.PhotoImage(display_img)
            self.binary_label.config(image=self.photo_binary, text="")
            
            self.status_var.set("預覽已更新")
        except ValueError: self.status_var.set("錯誤: 解析度必須是數字")
        except Exception as e:
            messagebox.showerror("處理錯誤", f"更新預覽時發生錯誤:\n{e}")
            self.status_var.set("預覽更新失敗")

    def encode_string_to_list(self, encoded_str: str) -> list[str]:
        if not encoded_str: return []
        result, i = [], 0
        while i < len(encoded_str):
            char, count = encoded_str[i], 1
            j = i + 1
            while j < len(encoded_str) and encoded_str[j] == char:
                count += 1
                j += 1
            result.append(f"{char}{count}")
            i = j
        return result

    def save_print_code(self):
        if not self.original_image:
            messagebox.showwarning("警告", "沒有可儲存的圖片資料。")
            return
        try:
            width, height = int(self.width_var.get()), int(self.height_var.get())
            threshold = self.threshold_var.get()
            
            img = self.original_image.copy()
            if self.mirror_var.get():
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            img_resized = img.convert('L').resize((width, height))
            
            binary_data = []
            for y in range(height):
                row = [1 if img_resized.getpixel((x, y)) <= threshold else 0 for x in range(width)]
                binary_data.append(row)

            print_code_data = []
            for row in binary_data:
                encoded_string = "".join([str(p) for p in row])
                print_code_row = self.encode_string_to_list(encoded_string)
                print_code_data.append(print_code_row)

            save_path = filedialog.asksaveasfilename(
                title="儲存 Print Code", defaultextension=".py",
                filetypes=[("Python 檔案", "*.py")], initialfile="image_print_codes.py"
            )
            if not save_path:
                self.status_var.set("存檔已取消")
                return

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"# Generated by PrintCodeGenerator\n")
                f.write(f"# Image: {os.path.basename(self.file_path)}\n")
                f.write(f"# Resolution: {width}x{height}, Threshold: {threshold}, Mirrored: {self.mirror_var.get()}\n")
                f.write("# NOTE: 1 represents BLACK, 0 represents WHITE\n")
                f.write(f"print_codes = {print_code_data}")

            messagebox.showinfo("成功", f"Print Code 已成功儲存至:\n{save_path}")
            self.status_var.set(f"檔案已儲存: {os.path.basename(save_path)}")
        except Exception as e:
            messagebox.showerror("存檔錯誤", f"儲存檔案時發生錯誤:\n{e}")
            self.status_var.set("存檔失敗")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrintCodeGeneratorApp(root)
    root.mainloop()