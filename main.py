import sys
from tabs.tabs import (ImageResizerTab, PdfToImageTab)
from tabs.img_to_pdf import ImageToPdfTab
from tabs.combine_pdf_tab import CombinePdfTab
from menu.menu import (CustomMenu)
from PyQt5.QtWidgets import (QApplication,QMessageBox, QMainWindow, QTabWidget, QWidget, QVBoxLayout)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF and Image Tools")
        self.setGeometry(100, 100, 600, 500)

        CustomMenu.create_menu_bar(self)
  
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 15, 10, 10)
        main_layout.setSpacing(10)
        
        self.tabs = QTabWidget()
        self.pdf_tab = PdfToImageTab(self)
        self.image_tab = ImageResizerTab()
        self.image_to_pdf_tab = ImageToPdfTab()
        self.combine_pdf_tab = CombinePdfTab()
        
        self.tabs.addTab(self.pdf_tab, "PDF to Images")
        self.tabs.addTab(self.combine_pdf_tab, "Combine PDFs")
        self.tabs.addTab(self.image_tab, "Image Resizer")
        self.tabs.addTab(self.image_to_pdf_tab, "Images to PDF")
   
        main_layout.addWidget(self.tabs)
        main_layout.addStretch()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        from pdf2image import convert_from_path
        from PIL import Image
        from fpdf import FPDF
        from PyPDF2 import PdfMerger
    except ImportError as e:
        QMessageBox.critical(None, "Error", 
                           f"Required packages not found. Please install:\n\n"
                           f"pip install pdf2image pillow pyqt5 fpdf2 pypdf2")
        sys.exit(1)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())