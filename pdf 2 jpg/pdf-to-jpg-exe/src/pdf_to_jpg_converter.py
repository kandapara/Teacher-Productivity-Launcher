import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageTk, Image
from pdf2image import convert_from_path
import os

# App window
root = tk.Tk()
root.title("📄 Professional PDF to JPG Converter")
root.geometry("700x500")
root.configure(bg="#f5f5f5")

pdf_path = ""
output_folder = ""

def select_pdf():
    global pdf_path
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if pdf_path:
        pdf_label.config(text=pdf_path)
        show_preview(pdf_path)

def select_output_folder():
    global output_folder
    output_folder = filedialog.askdirectory()
    if output_folder:
        output_label.config(text=output_folder)

def show_preview(pdf_file):
    try:
        preview = convert_from_path(pdf_file, 100, first_page=1, last_page=1)[0]
        preview.thumbnail((300, 300))
        img = ImageTk.PhotoImage(preview)
        preview_label.config(image=img)
        preview_label.image = img
    except Exception as e:
        messagebox.showerror("Error", str(e))

def convert_pdf():
    if not pdf_path:
        messagebox.showerror("Error", "Please select a PDF file.")
        return
    if not output_folder:
        messagebox.showerror("Error", "Please select an output folder.")
        return

    try:
        pages = convert_from_path(pdf_path, 300)
        for i, page in enumerate(pages):
            filename = os.path.join(output_folder, f"page_{i+1}.jpg")
            page.save(filename, "JPEG")
        messagebox.showinfo("Success", f"{len(pages)} pages converted successfully!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Layout
tk.Label(root, text="PDF to JPG Converter", font=("Helvetica", 20, "bold"), bg="#f5f5f5").pack(pady=10)

# PDF selection
pdf_frame = tk.Frame(root, bg="#f5f5f5")
pdf_frame.pack(pady=5)
pdf_label = tk.Label(pdf_frame, text="No PDF selected", width=60, anchor='w', bg="white", relief="solid")
pdf_label.pack(side=tk.LEFT, padx=5)
tk.Button(pdf_frame, text="Select PDF", command=select_pdf, bg="#2196f3", fg="white").pack(side=tk.LEFT)

# Output folder selection
out_frame = tk.Frame(root, bg="#f5f5f5")
out_frame.pack(pady=5)
output_label = tk.Label(out_frame, text="Output folder not selected", width=60, anchor='w', bg="white", relief="solid")
output_label.pack(side=tk.LEFT, padx=5)
tk.Button(out_frame, text="Select Output", command=select_output_folder, bg="#4caf50", fg="white").pack(side=tk.LEFT)

# Preview
tk.Label(root, text="Preview", font=("Helvetica", 14, "bold"), bg="#f5f5f5").pack(pady=10)
preview_label = tk.Label(root, text="Preview will appear here", bg="#eeeeee", width=50, height=15, relief="solid")
preview_label.pack()

# Convert Button
tk.Button(root, text="Convert to JPG", command=convert_pdf, bg="#607d8b", fg="white",
          font=("Helvetica", 14, "bold"), width=30).pack(pady=15)

# Footer
footer = tk.Label(root, text=(
    "Developed by:\n"
    "Md. Hussainuzzaman Hannan\n"
    "Mobile: 01719074004\n"
    "Email: hannan01719@gmail.com\n"
    "WhatsApp: 01719074004"
), bg="#263238", fg="white", font=("Arial", 10), justify="center", pady=10)
footer.pack(fill=tk.X, side=tk.BOTTOM)

root.mainloop()