# PDF to JPG Converter

This project provides a simple graphical user interface (GUI) application for converting PDF files to JPG images. The application is built using Python's Tkinter library and utilizes the `Pillow` and `pdf2image` libraries for image processing and PDF conversion.

## Project Structure

```
pdf-to-jpg-exe
├── src
│   └── pdf_to_jpg_converter.py  # Main logic for converting PDF to JPG
├── requirements.txt              # List of dependencies
├── setup.py                      # Packaging configuration
└── README.md                     # Project documentation
```

## Installation

To get started with the project, you need to install the required dependencies. You can do this by running the following command in your terminal:

```
pip install -r requirements.txt
```

## Usage

1. **Run the Application**: You can run the application by executing the following command:

   ```
   python src/pdf_to_jpg_converter.py
   ```

2. **Select a PDF File**: Click on the "Select PDF" button to choose the PDF file you want to convert.

3. **Select Output Folder**: Click on the "Select Output" button to choose the folder where the converted JPG images will be saved.

4. **Preview**: A preview of the first page of the selected PDF will be displayed.

5. **Convert to JPG**: Click on the "Convert to JPG" button to start the conversion process. The application will save each page of the PDF as a separate JPG file in the selected output folder.

## Building the Executable

To create an executable file for the application, you can use the following command:

```
python setup.py build
```

This will generate an executable that you can distribute and run on other machines without requiring a Python installation.

## Author

Developed by Md. Hussainuzzaman Hannan  
Mobile: 01719074004  
Email: hannan01719@gmail.com  
WhatsApp: 01719074004

## License

This project is licensed under the MIT License. See the LICENSE file for more details.