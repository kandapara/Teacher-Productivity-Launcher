import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import ImageTk, Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import os
import threading
import queue
import sys
import ctypes

# --- Appearance ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# --- Colors ---
ACCENT_ORANGE = "#FF7F50"
ACCENT_GREEN = "#2E8B57"
ACCENT_CYAN = "#008B8B"

# --- Fonts ---
HEADING_FONT = ("Arial", 20, "bold")

# Hide console window on Windows
if sys.platform == "win32":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)





# --- Sound Engine ---
def play_sound(sound_type="success"):
    if sys.platform == "win32":
        import winsound
        try:
            if sound_type == "success": winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
            else: winsound.PlaySound("SystemHand", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception: pass

# --- App window ---
root = ctk.CTk()
root.title("PDF/JPG Converter")
root.geometry("1200x800")


# --- Global variables ---
mode = tk.StringVar(value="PDF to JPG")

# PDF to JPG variables
pdf_paths, output_folder, pdf_preview_pages = [], "", []
current_preview_doc = None
total_preview_pages, current_preview_page_num, zoom_level = 0, 0, 1.0
jpeg_quality, resolution = tk.IntVar(value=95), tk.IntVar(value=300)
page_range_str = tk.StringVar(value="All")

# JPG to PDF variables
jpg_paths = []
jpg_images_props = []
layout_var = tk.StringVar(value="single")
paper_size_var = tk.StringVar(value="Auto")
zoom_level_jpg = 1.0

# Common variables
watermark_text = tk.StringVar()
watermark_logo_path = tk.StringVar()
watermark_opacity = tk.IntVar(value=30)
watermark_size = tk.DoubleVar(value=1.0)
conversion_queue = queue.Queue()
resizing_watermark = False
initial_mouse_y = 0
initial_watermark_size = 1.0

# --- Watermark Preview Update ---
def update_preview(*args):
    if notebook.get() == "PDF to JPG":
        display_page()
    else:
        preview_jpg_layout()

watermark_text.trace_add("write", update_preview)
watermark_logo_path.trace_add("write", update_preview)
watermark_opacity.trace_add("write", update_preview)
watermark_size.trace_add("write", update_preview)
layout_var.trace_add("write", update_preview)

# --- Core Functions (PDF to JPG) ---
def apply_watermark(image):
    if not watermark_text.get() and not watermark_logo_path.get():
        return image
    try:
        page = image.convert("RGBA")
        watermark_layer = Image.new("RGBA", page.size, (255, 255, 255, 0))
        opacity = int(255 * (watermark_opacity.get() / 100))

        # Logo Watermark
        if watermark_logo_path.get():
            logo = Image.open(watermark_logo_path.get()).convert("RGBA")
            logo_width, logo_height = logo.size
            ratio = (page.width / 4) / logo_width * watermark_size.get()
            new_size = (int(logo_width * ratio), int(logo_height * ratio))
            logo = logo.resize(new_size, Image.Resampling.LANCZOS)
            
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: int(p * (opacity / 255.0)))
            logo.putalpha(alpha)

            pos_x = (page.width - logo.width) // 2
            pos_y = (page.height - logo.height) // 2
            watermark_layer.paste(logo, (pos_x, pos_y), logo)

        # Text Watermark
        if watermark_text.get():
            draw = ImageDraw.Draw(watermark_layer)
            font_size = int(page.height / 20 * watermark_size.get())
            try: font = ImageFont.truetype("arial.ttf", font_size)
            except IOError: font = ImageFont.load_default()
            text = watermark_text.get()
            text_bbox = draw.textbbox((0,0), text, font=font)
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            pos_x = (page.width - text_width) // 2
            pos_y = (page.height - text_height) // 2
            draw.text((pos_x, pos_y), text, font=font, fill=(128, 128, 128, opacity))

        return Image.alpha_composite(page, watermark_layer).convert("RGB")
    except Exception as e:
        raise e

def parse_page_range(range_str, max_pages):
    if range_str.strip().lower() == 'all': return set(range(max_pages))
    pages = set()
    try:
        for part in range_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                if not (1 <= start <= end <= max_pages): raise ValueError(f"Invalid range: {part}")
                pages.update(range(start - 1, end))
            else:
                page_num = int(part)
                if not (1 <= page_num <= max_pages): raise ValueError(f"Invalid page: {page_num}")
                pages.add(page_num - 1)
    except ValueError as e:
        conversion_queue.put(('error', f"Invalid Page Range: {e}. Use format like '1, 3-5, 8'."))
        return None
    return pages

def display_page():
    if not current_preview_doc: return
    try:
        page = current_preview_doc.load_page(current_preview_page_num)
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Apply watermark if any
        img_with_watermark = apply_watermark(img)

        canvas_w = preview_canvas.winfo_width()
        canvas_h = preview_canvas.winfo_height()

        img_w, img_h = img_with_watermark.size
        if img_w == 0 or img_h == 0 or canvas_w < 2 or canvas_h < 2: return

        # Scale image to fit canvas
        w_ratio = canvas_w / img_w
        h_ratio = canvas_h / img_h
        scale_ratio = min(w_ratio, h_ratio)

        new_width, new_height = int(img_w * scale_ratio * zoom_level), int(img_h * scale_ratio * zoom_level)
        
        if new_width == 0 or new_height == 0: return

        resized_image = img_with_watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(resized_image)
        
        preview_canvas.delete("all")
        preview_canvas.create_image(canvas_w/2, canvas_h/2, anchor='center', image=img_tk, tags=("page"))
        preview_canvas.image = img_tk

        preview_canvas.configure(scrollregion=preview_canvas.bbox("all"))
        page_indicator_label.configure(text=f"Page {current_preview_page_num + 1} of {total_preview_pages}")
        update_zoom_label()
        del page
        del pix
    except Exception as e: 
        messagebox.showerror("Error", f"Could not display page: {e}")

def load_pdf_for_preview(event=None):
    global current_preview_doc, total_preview_pages, current_preview_page_num, zoom_level
    selected_indices = pdf_listbox.curselection()
    if not selected_indices: return
    selected_path = pdf_paths[selected_indices[0]]
    try:
        if current_preview_doc:
            current_preview_doc.close()
        current_preview_doc = fitz.open(selected_path)
        total_preview_pages = current_preview_doc.page_count
        current_preview_page_num, zoom_level = 0, 1.0
        display_page()
    except Exception as e: messagebox.showerror("Error", f"Could not load PDF for preview: {e}")

def select_pdfs(event=None):
    new_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
    if not new_paths:
        return
    
    initial_count = len(pdf_paths)
    for path in new_paths:
        if path not in pdf_paths:
            pdf_paths.append(path)
            pdf_listbox.insert(tk.END, os.path.basename(path))
            
    if len(pdf_paths) > initial_count:
        pdf_listbox.selection_clear(0, tk.END)
        new_index = initial_count
        pdf_listbox.selection_set(new_index)
        pdf_listbox.activate(new_index)
        pdf_listbox.see(new_index)
        load_pdf_for_preview()

def remove_selected_pdf():
    global current_preview_doc
    selected_indices = pdf_listbox.curselection()
    if not selected_indices: return
    for index in sorted(selected_indices, reverse=True):
        pdf_listbox.delete(index)
        del pdf_paths[index]
    if current_preview_doc:
        current_preview_doc.close()
        current_preview_doc = None
    preview_canvas.delete("all")

def clear_all_pdfs():
    global current_preview_doc
    pdf_listbox.delete(0, tk.END)
    pdf_paths.clear()
    if current_preview_doc:
        current_preview_doc.close()
        current_preview_doc = None
    preview_canvas.delete("all")

def select_output_folder(event=None):
    global output_folder
    output_folder = filedialog.askdirectory()
    if output_folder: 
        output_label.configure(text=output_folder)
        jpg_output_label.configure(text=output_folder)

def select_logo_file():
    path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
    if path: watermark_logo_path.set(path); logo_path_label.configure(text=os.path.basename(path))

def get_page_count(path):
    try:
        doc = fitz.open(path)
        count = doc.page_count
        doc.close()
        return count
    except Exception as e:
        conversion_queue.put(('error', f"Could not get page count for {os.path.basename(path)}.\nError: {e}"))
        return 0

def conversion_worker():
    quality, dpi = jpeg_quality.get(), resolution.get()
    total_pages_converted = 0
    try:
        for i, path in enumerate(pdf_paths):
            base_filename = os.path.splitext(os.path.basename(path))[0]
            conversion_queue.put(
                ('progress_text', f"Converting: {os.path.basename(path)}..."))

            doc = fitz.open(path)
            max_pages = doc.page_count

            selected_pages = parse_page_range(page_range_str.get(), max_pages)
            if selected_pages is None:
                doc.close()
                continue

            for page_num in range(1, max_pages + 1):
                if (page_num - 1) in selected_pages:
                    try:
                        page = doc.load_page(page_num - 1)
                        mat = fitz.Matrix(dpi / 72, dpi / 72)
                        pix = page.get_pixmap(matrix=mat)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        
                        filename = os.path.join(
                            output_folder, f"{base_filename}_page_{page_num}.jpg")
                        page_with_watermark = apply_watermark(img)
                        page_with_watermark.save(
                            filename, "JPEG", quality=quality)
                        total_pages_converted += 1
                        conversion_queue.put(('page_converted', 1))
                        del page
                        del pix
                        del img
                    except MemoryError:
                        conversion_queue.put(('error', f"MemoryError while converting page {page_num} of {os.path.basename(path)}. Try lowering the DPI/Resolution."))
                    except Exception as e:
                        conversion_queue.put(
                            ('error', f"Error converting page {page_num} of {os.path.basename(path)}: {e}"))
            doc.close()
    except Exception as e:
        conversion_queue.put(
            ('error', f"An unexpected error occurred during conversion: {e}"))
    finally:
        conversion_queue.put(('done', total_pages_converted))

def start_conversion(event=None):
    if not pdf_paths:
        return messagebox.showerror("Error", "No PDF files selected.")
    if not output_folder:
        return messagebox.showerror("Error", "Please select an output folder.")

    progress_label.configure(text="Calculating total pages...")
    progress_frame.pack(fill='x', pady=5)
    convert_btn.configure(state=tk.DISABLED)

    def calculate_total_pages():
        total_pages = 0
        try:
            for path in pdf_paths:
                max_pages = get_page_count(path)
                pages_to_convert = parse_page_range(
                    page_range_str.get(), max_pages)
                if pages_to_convert:
                    total_pages += len(pages_to_convert)
            return total_pages
        except Exception as e:
            conversion_queue.put(
                ('error', f"Failed to calculate total pages. Error: {e}"))
            return -1

    def on_calculation_complete(total_pages):
        if total_pages == -1:
            convert_btn.configure(state=tk.NORMAL)
            progress_frame.pack_forget()
            return

        if total_pages == 0:
            messagebox.showinfo("No Pages", "No pages selected for conversion.")
            convert_btn.configure(state=tk.NORMAL)
            progress_frame.pack_forget()
            return

        progress_bar.set(0)
        progress_bar.configure(determinate_speed=total_pages/100)
        progress_label.configure(text="Starting conversion...")
        threading.Thread(target=conversion_worker, daemon=True).start()
        root.after(100, check_queue)

    # Run page calculation in a separate thread to not freeze the GUI
    def calculation_thread():
        total_pages = calculate_total_pages()
        root.after(0, on_calculation_complete, total_pages)

    threading.Thread(target=calculation_thread, daemon=True).start()

def check_queue():
    try:
        msg_type, data = conversion_queue.get_nowait()
        if msg_type == 'page_converted':
            progress_bar.step()
        elif msg_type == 'progress_text':
            progress_label.configure(text=data)
        elif msg_type == 'done':
            return on_conversion_complete(data)
        elif msg_type == 'error':
            messagebox.showwarning("Conversion Error", data)
        root.after(100, check_queue)
    except queue.Empty:
        root.after(100, check_queue)

def on_conversion_complete(total_converted):
    progress_frame.pack_forget()
    convert_btn.configure(state=tk.NORMAL)
    play_sound("success")
    if total_converted > 0:
        messagebox.showinfo(
            "Success", f"Batch conversion complete!\n{total_converted} total pages converted.")

# --- Core Functions (JPG to PDF) ---
def select_jpgs(event=None):
    new_paths = filedialog.askopenfilenames(filetypes=[("JPG Files", "*.jpg *.jpeg")])
    if not new_paths:
        return
    
    for path in new_paths:
        if path not in jpg_paths:
            jpg_paths.append(path)
            jpg_listbox.insert(tk.END, os.path.basename(path))
            jpg_images_props.append({'path': path, 'scale': 1.0})
    preview_jpg_layout()

def remove_selected_jpg():
    selected_indices = jpg_listbox.curselection()
    if not selected_indices: return
    for index in sorted(selected_indices, reverse=True):
        jpg_listbox.delete(index)
        del jpg_paths[index]
        del jpg_images_props[index]
    preview_jpg_layout()

def clear_all_jpgs():
    jpg_listbox.delete(0, tk.END)
    jpg_paths.clear()
    jpg_images_props.clear()
    preview_jpg_layout()

def convert_to_pdf():
    if not jpg_paths:
        return messagebox.showerror("Error", "No JPG files selected.")
    if not output_folder:
        return messagebox.showerror("Error", "Please select an output folder.")

    try:
        images = [Image.open(p) for p in jpg_paths]
        if not images:
            return

        output_filename = os.path.join(output_folder, "converted.pdf")
        layout = layout_var.get()
        paper_size = paper_size_var.get()

        paper_sizes_dpi_300 = {
            "A4": (2480, 3508),
            "Letter": (2550, 3300),
            "Legal": (2550, 4200),
        }

        if layout == "single":
            processed_images = []
            if paper_size != "Auto":
                page_width, page_height = paper_sizes_dpi_300[paper_size]
                for i, img in enumerate(images):
                    scale = jpg_images_props[i]['scale']
                    img_width, img_height = img.size
                    
                    # Apply scale
                    img_width = int(img_width * scale)
                    img_height = int(img_height * scale)
                    img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)

                    aspect_ratio = img_width / img_height
                    
                    if (img_width / page_width) > (img_height / page_height):
                        new_width = page_width
                        new_height = int(new_width / aspect_ratio)
                    else:
                        new_height = page_height
                        new_width = int(new_height * aspect_ratio)
                        
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    new_page = Image.new('RGB', (page_width, page_height), 'white')
                    paste_x = (page_width - new_width) // 2
                    paste_y = (page_height - new_height) // 2
                    new_page.paste(resized_img, (paste_x, paste_y))
                    processed_images.append(new_page)
            else: # Auto paper size
                processed_images = []
                for i, img in enumerate(images):
                    scale = jpg_images_props[i]['scale']
                    w, h = img.size
                    new_w, new_h = int(w*scale), int(h*scale)
                    resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    processed_images.append(resized_img.convert("RGB"))

            processed_images[0].save(output_filename, save_all=True, append_images=processed_images[1:], resolution=300.0)
        
        else: # Grid layouts
            if paper_size == "Auto":
                messagebox.showerror("Error", "Please select a paper size (A4, Letter, etc.) for grid layouts.")
                return

            page_width, page_height = paper_sizes_dpi_300[paper_size]
            pdf_page = Image.new('RGB', (page_width, page_height), 'white')

            if layout == "2x2":
                cols, rows = 2, 2
                images_to_paste = images[:4]
                props_to_paste = jpg_images_props[:4]
            elif layout == "vertical":
                cols, rows = 1, 2
                images_to_paste = images[:2]
                props_to_paste = jpg_images_props[:2]
            elif layout == "horizontal":
                cols, rows = 2, 1
                images_to_paste = images[:2]
                props_to_paste = jpg_images_props[:2]

            cell_w = page_width // cols
            cell_h = page_height // rows

            for i, (img, props) in enumerate(zip(images_to_paste, props_to_paste)):
                scale = props['scale']
                
                w,h = img.size
                new_w, new_h = int(w*scale), int(h*scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                img.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
                
                col = i % cols
                row = i // cols
                
                paste_x = col * cell_w + (cell_w - img.width) // 2
                paste_y = row * cell_h + (cell_h - img.height) // 2
                pdf_page.paste(img, (paste_x, paste_y))
            
            pdf_page.save(output_filename, resolution=300.0)


        messagebox.showinfo("Success", f"Successfully saved to {output_filename}")

    except Exception as e:
        messagebox.showerror("Error", f"Could not convert to PDF: {e}")

def preview_jpg_layout():
    preview_canvas.delete("all")
    if not jpg_paths: return
    if not hasattr(preview_canvas, 'images'):
        preview_canvas.images = []
    preview_canvas.images.clear()

    try:
        images = [Image.open(p) for p in jpg_paths]
        if not images: return

        layout = layout_var.get()
        
        preview_w = preview_canvas.winfo_width()
        preview_h = preview_canvas.winfo_height()
        if preview_w < 2 : preview_w = 300
        if preview_h < 2 : preview_h = 400

        if layout == "single":
            if not jpg_images_props: return
            img = images[0]
            scale = jpg_images_props[0]['scale']
            
            img_w, img_h = img.size
            w_ratio = preview_w / img_w
            h_ratio = preview_h / img_h
            scale_ratio = min(w_ratio, h_ratio)

            new_w = int(img_w * scale_ratio * scale * zoom_level_jpg)
            new_h = int(img_h * scale_ratio * scale * zoom_level_jpg)

            resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(resized_img)
            
            preview_canvas.create_image(preview_w/2, preview_h/2, anchor='center', image=img_tk, tags=("jpg_0"))
            preview_canvas.images.append(img_tk)

        else: # Grid layouts
            if layout == "2x2":
                cols, rows = 2, 2
                images_to_show = images[:4]
                props_to_show = jpg_images_props[:4]
            elif layout == "vertical":
                cols, rows = 1, 2
                images_to_show = images[:2]
                props_to_show = jpg_images_props[:2]
            elif layout == "horizontal":
                cols, rows = 2, 1
                images_to_show = images[:2]
                props_to_show = jpg_images_props[:2]

            cell_w = (preview_w / cols) * zoom_level_jpg
            cell_h = (preview_h / rows) * zoom_level_jpg

            for i, (img, props) in enumerate(zip(images_to_show, props_to_show)):
                scale = props['scale']
                
                w,h = img.size
                aspect = h/w
                
                new_w = int(cell_w * scale)
                new_h = int(new_w * aspect)

                if new_w > cell_w: new_w = int(cell_w)
                if new_h > cell_h: new_h = int(cell_h)

                resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                col = i % cols
                row = i // cols
                
                paste_x = int(col * cell_w + (cell_w - resized_img.width) / 2)
                paste_y = int(row * cell_h + (cell_h - resized_img.height) / 2)

                img_tk = ImageTk.PhotoImage(resized_img)
                preview_canvas.create_image(paste_x, paste_y, anchor='nw', image=img_tk, tags=(f"jpg_{i}"))
                preview_canvas.images.append(img_tk)
        
        update_zoom_label()
        preview_canvas.config(scrollregion=preview_canvas.bbox("all"))

    except Exception as e: messagebox.showerror("Error", f"Could not preview layout: {e}")

# --- Page Navigation and Zoom ---
def next_page():
    global current_preview_page_num
    if current_preview_page_num < total_preview_pages - 1: current_preview_page_num += 1; display_page()

def prev_page():
    global current_preview_page_num
    if current_preview_page_num > 0: current_preview_page_num -= 1; display_page()

def zoom_in():
    global zoom_level
    zoom_level *= 1.25
    display_page()

def zoom_out():
    global zoom_level
    if zoom_level > 0.2:
        zoom_level /= 1.25
    display_page()

def update_zoom_label():
    if notebook.get() == "PDF to JPG":
        zoom_label.configure(text=f"{int(zoom_level * 100)}%")
    else:
        zoom_label.configure(text=f"{int(zoom_level_jpg * 100)}%")

def zoom_in_jpg():
    global zoom_level_jpg
    zoom_level_jpg *= 1.25
    preview_jpg_layout()
def zoom_out_jpg():
    global zoom_level_jpg
    if zoom_level_jpg > 0.2:
        zoom_level_jpg /= 1.25
    preview_jpg_layout()

# --- Watermark Resizing ---
def start_resize_watermark(event):
    global resizing_watermark, initial_mouse_y, initial_watermark_size
    if (watermark_text.get() or watermark_logo_path.get()) and (notebook.get() == "PDF to JPG"):
        resizing_watermark = True
        initial_mouse_y = event.y
        initial_watermark_size = watermark_size.get()

def resize_watermark(event):
    if resizing_watermark:
        delta_y = initial_mouse_y - event.y
        new_size = initial_watermark_size + delta_y / 100.0
        if 0.1 <= new_size <= 5.0:
            watermark_size.set(new_size)

def stop_resize_watermark(event):
    global resizing_watermark
    resizing_watermark = False

# --- JPG Resizing ---
selected_image_index = None
resizing_jpg = False
initial_image_scale = 1.0

def start_resize_jpg(event):
    global resizing_jpg, selected_image_index, initial_mouse_y, initial_image_scale
    if notebook.get() == "JPG to PDF":
        canvas_item = preview_canvas.find_closest(event.x, event.y)
        if canvas_item:
            tags = preview_canvas.gettags(canvas_item[0])
            if tags and tags[0].startswith("jpg_"):
                selected_image_index = int(tags[0].split("_")[1])
                resizing_jpg = True
                initial_mouse_y = event.y
                initial_image_scale = jpg_images_props[selected_image_index]['scale']

def resize_jpg(event):
    if resizing_jpg and selected_image_index is not None:
        delta_y = initial_mouse_y - event.y
        new_scale = initial_image_scale + delta_y / 100.0
        if 0.1 <= new_scale <= 5.0:
            jpg_images_props[selected_image_index]['scale'] = new_scale
            preview_jpg_layout()

def stop_resize_jpg(event):
    global resizing_jpg, selected_image_index
    resizing_jpg = False
    selected_image_index = None

# --- UI Setup ---
left_frame = ctk.CTkFrame(root, width=400)
left_frame.pack(side=tk.LEFT, fill='y', padx=10, pady=10)

right_frame = ctk.CTkFrame(root)
right_frame.pack(side=tk.LEFT, fill='both', expand=True, pady=10)

notebook = ctk.CTkTabview(left_frame)
notebook.pack(fill="both", expand=True, padx=10, pady=10)

pdf_to_jpg_tab = notebook.add("PDF to JPG")
jpg_to_pdf_tab = notebook.add("JPG to PDF")

pdf_to_jpg_frame = ctk.CTkScrollableFrame(pdf_to_jpg_tab)
pdf_to_jpg_frame.pack(fill='both', expand=True)

jpg_to_pdf_frame = ctk.CTkScrollableFrame(jpg_to_pdf_tab)
jpg_to_pdf_frame.pack(fill='both', expand=True)


# --- PDF to JPG Frame ---
pdf_list_frame = ctk.CTkFrame(pdf_to_jpg_frame, corner_radius=10)
pdf_list_frame.pack(fill='x', padx=5, pady=5)
ctk.CTkLabel(pdf_list_frame, text="PDF Files", font=HEADING_FONT).pack(anchor="w", padx=10, pady=(5,0))
pdf_listbox = tk.Listbox(pdf_list_frame, relief="sunken", borderwidth=1, height=5, bg="#2a2d2e", fg="white", highlightbackground="#565b5e", highlightcolor="#565b5e")
pdf_listbox.bind("<<ListboxSelect>>", load_pdf_for_preview)
pdf_listbox.pack(fill='x', expand=True, pady=5, padx=5)
pdf_btn_frame = ctk.CTkFrame(pdf_list_frame)
pdf_btn_frame.pack(fill='x', pady=(5,5), padx=5)
add_pdf_btn = ctk.CTkButton(pdf_btn_frame, text="Add PDF(s)", command=select_pdfs, fg_color=ACCENT_GREEN, hover_color="#2E8B57", cursor="hand2")
remove_pdf_btn = ctk.CTkButton(pdf_btn_frame, text="Remove", command=remove_selected_pdf, fg_color=ACCENT_ORANGE, hover_color="#FF4500", cursor="hand2")
clear_pdf_btn = ctk.CTkButton(pdf_btn_frame, text="Clear All", command=clear_all_pdfs, fg_color=ACCENT_ORANGE, hover_color="#FF4500", cursor="hand2")
add_pdf_btn.pack(side=tk.LEFT, expand=True, fill='x', padx=(0,5))
remove_pdf_btn.pack(side=tk.LEFT, expand=True, fill='x', padx=5)
clear_pdf_btn.pack(side=tk.LEFT, expand=True, fill='x', padx=(5,0))

out_frame = ctk.CTkFrame(pdf_to_jpg_frame, corner_radius=10)
out_frame.pack(fill='x', padx=5, pady=5)
ctk.CTkLabel(out_frame, text="Output Folder", font=HEADING_FONT).pack(anchor="w", padx=10, pady=(5,0))
out_btn = ctk.CTkButton(out_frame, text="Select Folder", command=select_output_folder, cursor="hand2")
output_label = ctk.CTkLabel(out_frame, text="No folder selected", anchor='w')
out_btn.pack(side=tk.LEFT, padx=10, pady=10)
output_label.pack(side=tk.LEFT, fill='x', expand=True, padx=(0,10))

settings_frame = ctk.CTkFrame(pdf_to_jpg_frame, corner_radius=10)
settings_frame.pack(fill='x', padx=5, pady=5)
ctk.CTkLabel(settings_frame, text="Conversion Settings", font=HEADING_FONT).pack(anchor="w", padx=10, pady=(5,0))
quality_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
quality_frame.pack(fill='x', pady=5, padx=10)
ctk.CTkLabel(quality_frame, text="Quality (1-100):").pack(side=tk.LEFT)
quality_slider = ctk.CTkSlider(quality_frame, from_=1, to=100, variable=jpeg_quality, button_color=ACCENT_CYAN)
quality_slider.pack(side=tk.RIGHT, expand=True, fill='x')
dpi_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
dpi_frame.pack(fill='x', pady=5, padx=10)
ctk.CTkLabel(dpi_frame, text="Resolution (DPI):").pack(side=tk.LEFT)
dpi_menu = ctk.CTkOptionMenu(dpi_frame, variable=resolution, values=["150", "300", "600"], fg_color=ACCENT_CYAN)
dpi_menu.pack(side=tk.RIGHT)
range_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
range_frame.pack(fill='x', pady=5, padx=10)
ctk.CTkLabel(range_frame, text="Page Range:").pack(side=tk.LEFT)
range_entry = ctk.CTkEntry(range_frame, textvariable=page_range_str)
range_entry.pack(side=tk.RIGHT)

watermark_frame = ctk.CTkFrame(pdf_to_jpg_frame, corner_radius=10)
watermark_frame.pack(fill='x', padx=5, pady=5)
ctk.CTkLabel(watermark_frame, text="Watermark Settings", font=HEADING_FONT).pack(anchor="w", padx=10, pady=(5,0))
ctk.CTkLabel(watermark_frame, text="Text:").pack(anchor='w', padx=10)
ctk.CTkEntry(watermark_frame, textvariable=watermark_text).pack(fill='x', pady=(0,5), padx=10)
ctk.CTkLabel(watermark_frame, text="Logo:").pack(anchor='w', padx=10)
logo_frame = ctk.CTkFrame(watermark_frame, fg_color="transparent")
logo_frame.pack(fill='x', padx=10)
ctk.CTkButton(logo_frame, text="Select Logo", command=select_logo_file, cursor="hand2").pack(side=tk.LEFT)
logo_path_label = ctk.CTkLabel(logo_frame, text="No logo selected", anchor='w')
logo_path_label.pack(side=tk.LEFT, fill='x', expand=True, padx=10)
ctk.CTkLabel(watermark_frame, text="Opacity (0-100):").pack(anchor='w', pady=(5,0), padx=10)
ctk.CTkSlider(watermark_frame, from_=0, to=100, variable=watermark_opacity, button_color=ACCENT_CYAN).pack(fill='x', padx=10, pady=(0,10))

convert_btn = ctk.CTkButton(pdf_to_jpg_frame, text="Convert All PDFs", command=start_conversion, height=40, fg_color=ACCENT_CYAN, hover_color="#008B8B", cursor="hand2")
convert_btn.pack(fill='x', ipady=10, pady=10, padx=5)
progress_frame = ctk.CTkFrame(pdf_to_jpg_frame, fg_color="transparent")
progress_label = ctk.CTkLabel(progress_frame, text="")
progress_bar = ctk.CTkProgressBar(progress_frame, orientation='horizontal', mode='determinate', progress_color=ACCENT_CYAN)
progress_label.pack(fill='x')
progress_bar.pack(fill='x', pady=5)
progress_frame.pack_forget()

# --- JPG to PDF Frame ---
jpg_list_frame = ctk.CTkFrame(jpg_to_pdf_frame, corner_radius=10)
jpg_list_frame.pack(fill='x', padx=5, pady=5)
ctk.CTkLabel(jpg_list_frame, text="JPG Files", font=HEADING_FONT).pack(anchor="w", padx=10, pady=(5,0))
jpg_listbox = tk.Listbox(jpg_list_frame, relief="sunken", borderwidth=1, height=5, bg="#2a2d2e", fg="white", highlightbackground="#565b5e", highlightcolor="#565b5e")
jpg_listbox.pack(fill='x', expand=True, pady=5, padx=5)
jpg_btn_frame = ctk.CTkFrame(jpg_list_frame)
jpg_btn_frame.pack(fill='x', pady=(5,5), padx=5)
add_jpg_btn = ctk.CTkButton(jpg_btn_frame, text="Add JPG(s)", command=select_jpgs, fg_color=ACCENT_GREEN, hover_color="#2E8B57", cursor="hand2")
remove_jpg_btn = ctk.CTkButton(jpg_btn_frame, text="Remove", command=remove_selected_jpg, fg_color=ACCENT_ORANGE, hover_color="#FF4500", cursor="hand2")
clear_jpg_btn = ctk.CTkButton(jpg_btn_frame, text="Clear All", command=clear_all_jpgs, fg_color=ACCENT_ORANGE, hover_color="#FF4500", cursor="hand2")
add_jpg_btn.pack(side=tk.LEFT, expand=True, fill='x', padx=(0,5))
remove_jpg_btn.pack(side=tk.LEFT, expand=True, fill='x', padx=5)
clear_jpg_btn.pack(side=tk.LEFT, expand=True, fill='x', padx=(5,0))

jpg_out_frame = ctk.CTkFrame(jpg_to_pdf_frame, corner_radius=10)
jpg_out_frame.pack(fill='x', padx=5, pady=5)
ctk.CTkLabel(jpg_out_frame, text="Output Folder", font=HEADING_FONT).pack(anchor="w", padx=10, pady=(5,0))
jpg_out_btn = ctk.CTkButton(jpg_out_frame, text="Select Folder", command=select_output_folder, cursor="hand2")
jpg_output_label = ctk.CTkLabel(jpg_out_frame, text="No folder selected", anchor='w')
jpg_out_btn.pack(side=tk.LEFT, padx=10, pady=10)
jpg_output_label.pack(side=tk.LEFT, fill='x', expand=True, padx=(0,10))

layout_frame = ctk.CTkFrame(jpg_to_pdf_frame, corner_radius=10)
layout_frame.pack(fill='x', padx=5, pady=5)
ctk.CTkLabel(layout_frame, text="Layout Options", font=HEADING_FONT).pack(anchor="w", padx=10, pady=(5,0))
ctk.CTkRadioButton(layout_frame, text="Single image per page", variable=layout_var, value="single", fg_color=ACCENT_CYAN).pack(anchor='w', padx=10, pady=5)
ctk.CTkRadioButton(layout_frame, text="2x2 grid (4 images per page)", variable=layout_var, value="2x2", fg_color=ACCENT_CYAN).pack(anchor='w', padx=10, pady=5)
ctk.CTkRadioButton(layout_frame, text="Vertical (2 images per page)", variable=layout_var, value="vertical", fg_color=ACCENT_CYAN).pack(anchor='w', padx=10, pady=5)
ctk.CTkRadioButton(layout_frame, text="Horizontal (2 images per page)", variable=layout_var, value="horizontal", fg_color=ACCENT_CYAN).pack(anchor='w', padx=10, pady=5)

paper_size_frame = ctk.CTkFrame(layout_frame, fg_color="transparent")
paper_size_frame.pack(fill='x', pady=5, padx=10)
ctk.CTkLabel(paper_size_frame, text="Paper Size:").pack(side=tk.LEFT)
paper_size_menu = ctk.CTkOptionMenu(paper_size_frame, variable=paper_size_var, values=["Auto", "A4", "Letter", "Legal"], fg_color=ACCENT_CYAN)
paper_size_menu.pack(side=tk.RIGHT)

convert_to_pdf_btn = ctk.CTkButton(jpg_to_pdf_frame, text="Convert to PDF", command=convert_to_pdf, height=40, fg_color=ACCENT_CYAN, hover_color="#008B8B", cursor="hand2")
convert_to_pdf_btn.pack(fill='x', ipady=10, pady=10, padx=5)

# --- Main Content (Preview) ---
right_frame.grid_rowconfigure(1, weight=1)
right_frame.grid_columnconfigure(0, weight=1)

preview_controls = ctk.CTkFrame(right_frame)
preview_controls.grid(row=0, column=0, sticky="ew", padx=10, pady=5)


prev_btn = ctk.CTkButton(preview_controls, text="< Prev", command=prev_page, width=80, cursor="hand2")
page_indicator_label = ctk.CTkLabel(preview_controls, text="Page 0 of 0")
next_btn = ctk.CTkButton(preview_controls, text="Next >", command=next_page, width=80, cursor="hand2")
zoom_out_btn = ctk.CTkButton(preview_controls, text="-", command=lambda: zoom_out() if notebook.get() == "PDF to JPG" else zoom_out_jpg(), width=40, cursor="hand2")
zoom_label = ctk.CTkLabel(preview_controls, text="100%", width=60)
zoom_in_btn = ctk.CTkButton(preview_controls, text="+ ", command=lambda: zoom_in() if notebook.get() == "PDF to JPG" else zoom_in_jpg(), width=40, cursor="hand2")
prev_btn.pack(side=tk.LEFT, padx=(10, 5))
page_indicator_label.pack(side=tk.LEFT, padx=5)
next_btn.pack(side=tk.LEFT, padx=5)

# Create a flexible space to push zoom controls to the right
spacer = tk.Frame(preview_controls, bg=preview_controls.cget("fg_color")[1])
spacer.pack(side=tk.LEFT, expand=True, fill='x')

zoom_out_btn.pack(side=tk.LEFT, padx=5)
zoom_label.pack(side=tk.LEFT, padx=5)
zoom_in_btn.pack(side=tk.LEFT, padx=(5, 10))

def toggle_theme():
    if ctk.get_appearance_mode() == "Dark":
        ctk.set_appearance_mode("light")
    else:
        ctk.set_appearance_mode("dark")

theme_toggle_btn = ctk.CTkSwitch(preview_controls, text="Light Mode", command=toggle_theme, progress_color=ACCENT_ORANGE)
theme_toggle_btn.pack(side=tk.RIGHT, padx=10)


canvas_frame = ctk.CTkFrame(right_frame, corner_radius=10)
canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
canvas_frame.grid_rowconfigure(0, weight=1)
canvas_frame.grid_columnconfigure(0, weight=1)

preview_canvas = tk.Canvas(canvas_frame, highlightthickness=0, bg="#242424")
preview_canvas.grid(row=0, column=0, sticky="nsew")

v_scroll = ctk.CTkScrollbar(canvas_frame, command=preview_canvas.yview)
v_scroll.grid(row=0, column=1, sticky="ns")
h_scroll = ctk.CTkScrollbar(canvas_frame, orientation='horizontal', command=preview_canvas.xview)
h_scroll.grid(row=1, column=0, sticky="ew")

preview_canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)


def _on_preview_mousewheel(event):
    if notebook.get() == "PDF to JPG":
        if event.delta > 0:
            prev_page()
        else:
            next_page()
    else:
        if event.delta > 0:
            zoom_in_jpg()
        else:
            zoom_out_jpg()

preview_canvas.bind("<MouseWheel>", _on_preview_mousewheel)
preview_canvas.bind("<Button-1>", start_resize_watermark)
preview_canvas.bind("<B1-Motion>", resize_watermark)
preview_canvas.bind("<ButtonRelease-1>", stop_resize_watermark)
preview_canvas.bind("<Button-1>", start_resize_jpg, add='+'
)
preview_canvas.bind("<B1-Motion>", resize_jpg, add='+'
)
preview_canvas.bind("<ButtonRelease-1>", stop_resize_jpg, add='+'
)



developer_info_label = ctk.CTkLabel(right_frame, text="Developed by: Md. Hussainuzzaman Hannan | Mobile: 01719074004 | Email: hannan01719@gmail.com | WhatsApp: 01719074004", font=("Arial", 10))
developer_info_label.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

root.mainloop()
