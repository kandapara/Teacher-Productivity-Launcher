import pytesseract
from PIL import Image
from gtts import gTTS
import os
from tkinter import Tk, filedialog, messagebox

# 🛠️ Tesseract path (ঠিক করে দিন)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def convert_image_to_audio():
    root = Tk()
    root.withdraw()

    image_path = filedialog.askopenfilename(
        title="Select JPG Image",
        filetypes=[("JPG Files", "*.jpg"), ("All files", "*.*")]
    )
    if not image_path:
        return

    # Step 1: OCR - JPG → Text
    text = pytesseract.image_to_string(Image.open(image_path), lang="eng")

    if not text.strip():
        messagebox.showerror("Error", "❌ No text found in image.")
        return

    # Step 2: TTS - Text → MP3
    audio = gTTS(text=text, lang="en")
    output_path = os.path.splitext(image_path)[0] + ".mp3"
    audio.save(output_path)

    messagebox.showinfo("Success", f"✅ Audio saved to:\n{output_path}")

convert_image_to_audio()
