from setuptools import setup, find_packages

setup(
    name="pdf-to-jpg-converter",
    version="1.0",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        "Pillow",
        "pdf2image",
        "tkinter"
    ],
    entry_points={
        'console_scripts': [
            'pdf-to-jpg-converter=pdf_to_jpg_converter:main',
        ],
    },
    python_requires='>=3.6',
)