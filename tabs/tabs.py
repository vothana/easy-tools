
import os
from workers.workers import (PdfToImageWorker, ImageResizerWorker) 
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QProgressBar, QMessageBox,
                             QSpinBox, QGroupBox, QRadioButton, QButtonGroup, QListWidget)
from PyQt5.QtGui import  QIcon
from PIL import Image
from fpdf import FPDF

class PdfToImageTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.poppler_path = None
        self.parent = parent
        self.init_ui()
        self.auto_detect_poppler()

    def init_ui(self):
        layout = QVBoxLayout()

        # PDF File Selection
        file_group = QGroupBox("PDF File")
        file_layout = QVBoxLayout()
        
        self.pdf_path_label = QLabel("No PDF file selected")
        browse_btn = QPushButton("Browse PDF")
        browse_btn.clicked.connect(self.browse_pdf)
        
        file_layout.addWidget(self.pdf_path_label)
        file_layout.addWidget(browse_btn)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Pages Selection
        pages_group = QGroupBox("Pages to Export")
        pages_layout = QVBoxLayout()
        
        self.pages_input = QLineEdit()
        self.pages_input.setPlaceholderText("Enter page numbers separated by commas (e.g., 1,3,5)")
        pages_layout.addWidget(QLabel("Pages to export:"))
        pages_layout.addWidget(self.pages_input)
        pages_group.setLayout(pages_layout)
        layout.addWidget(pages_group)

        # Output Directory
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        self.output_dir_label = QLabel("Default: Same as input file directory")
        output_dir_btn = QPushButton("Change Output Directory")
        output_dir_btn.clicked.connect(self.browse_output_dir)
        self.custom_output_dir = None
        
        output_layout.addWidget(self.output_dir_label)
        output_layout.addWidget(output_dir_btn)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Status label for Poppler
        self.poppler_path_label = QLabel("Poppler: Using system PATH")
        layout.addWidget(self.poppler_path_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Convert Button
        convert_btn = QPushButton("Convert to Images")
        convert_btn.clicked.connect(self.convert_pdf)
        layout.addWidget(convert_btn)

        self.setLayout(layout)

    def auto_detect_poppler(self):
        """Try to find Poppler in common installation locations"""
        common_paths = [
            # Windows common paths
            r"C:\Program Files\poppler-23.08.0\Library\bin",
            r"C:\Program Files\poppler\bin",
            r"C:\poppler\bin",
            # Linux common paths
            "/usr/bin",
            "/usr/local/bin",
            # Mac common paths
            "/opt/homebrew/bin",
            "/usr/local/opt/poppler/bin"
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                # Check for pdftoppm executable
                if any(fname.startswith('pdftoppm') and not fname.endswith('.exe') 
                       for fname in os.listdir(path)):
                    self.poppler_path = path
                    self.poppler_path_label.setText(f"Auto-detected: {path}")
                    return
                # Windows check
                elif any(fname.lower() == 'pdftoppm.exe' for fname in os.listdir(path)):
                    self.poppler_path = path
                    self.poppler_path_label.setText(f"Auto-detected: {path}")
                    return
        
        self.poppler_path_label.setText("Poppler not auto-detected (will try system PATH)")

    def browse_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.pdf_path_label.setText(file_path)
            if not self.custom_output_dir:
                self.output_dir_label.setText(f"Default: {os.path.dirname(file_path)}")

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.custom_output_dir = dir_path
            self.output_dir_label.setText(dir_path)

    def convert_pdf(self):
        pdf_path = self.pdf_path_label.text()
        if not pdf_path or not os.path.exists(pdf_path):
            QMessageBox.warning(self, "Error", "Please select a valid PDF file")
            return

        pages_text = self.pages_input.text().strip()
        if not pages_text:
            QMessageBox.warning(self, "Error", "Please enter at least one page number")
            return

        try:
            pages = [int(p.strip()) for p in pages_text.split(",") if p.strip()]
            if not pages:
                raise ValueError("No valid page numbers")
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Invalid page numbers: {str(e)}")
            return

        output_dir = self.custom_output_dir if self.custom_output_dir else os.path.dirname(pdf_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.progress_bar.setValue(0)

        self.worker = PdfToImageWorker(pdf_path, pages, output_dir, self.poppler_path)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(self.conversion_complete)
        self.worker.error_occurred.connect(self.show_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def conversion_complete(self, saved_files):
        QMessageBox.information(
            self, "Success",
            f"Successfully exported {len(saved_files)} pages to:\n{os.path.dirname(saved_files[0])}"
        )
        self.progress_bar.setValue(0)

    def show_error(self, error_msg):
        if "poppler" in error_msg.lower():
            error_msg += "\n\nPlease ensure Poppler is installed and the correct path is set."
        QMessageBox.critical(self, "Error", error_msg)
        self.progress_bar.setValue(0)


class ImageResizerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.workers = []
        self.running_workers = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Image File Selection
        file_group = QGroupBox("Image Files")
        file_layout = QVBoxLayout()
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.ExtendedSelection)
        
        browse_btn = QPushButton("Browse Images")
        browse_btn.setIcon(QIcon.fromTheme("document-open"))
        browse_btn.clicked.connect(self.browse_images)
        
        clear_btn = QPushButton("Clear List")
        clear_btn.setIcon(QIcon.fromTheme("edit-clear"))
        clear_btn.clicked.connect(self.clear_file_list)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(browse_btn)
        btn_layout.addWidget(clear_btn)
        
        file_layout.addWidget(QLabel("Selected Images:"))
        file_layout.addWidget(self.file_list)
        file_layout.addLayout(btn_layout)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Resize Options (same as before)
        resize_group = QGroupBox("Resize Options")
        resize_layout = QVBoxLayout()
        
        self.method_group = QButtonGroup(self)
        
        pixel_method = QRadioButton("Resize by Pixels")
        pixel_method.setChecked(True)
        percent_method = QRadioButton("Resize by Percentage")
        
        self.method_group.addButton(pixel_method, 0)
        self.method_group.addButton(percent_method, 1)
        
        method_layout = QHBoxLayout()
        method_layout.addWidget(pixel_method)
        method_layout.addWidget(percent_method)
        resize_layout.addLayout(method_layout)
        
        self.pixel_controls = QWidget()
        pixel_layout = QVBoxLayout()
        
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Width:"))
        self.width_input = QSpinBox()
        self.width_input.setRange(0, 9999)
        self.width_input.setValue(0)
        self.width_input.setSpecialValueText("Auto")
        width_layout.addWidget(self.width_input)
        width_layout.addStretch()
        pixel_layout.addLayout(width_layout)
        
        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Height:"))
        self.height_input = QSpinBox()
        self.height_input.setRange(0, 9999)
        self.height_input.setValue(0)
        self.height_input.setSpecialValueText("Auto")
        height_layout.addWidget(self.height_input)
        height_layout.addStretch()
        pixel_layout.addLayout(height_layout)
        
        pixel_layout.addWidget(QLabel("Note: Set one dimension to 0 to maintain aspect ratio"))
        self.pixel_controls.setLayout(pixel_layout)
        resize_layout.addWidget(self.pixel_controls)

        self.percent_controls = QWidget()
        percent_layout = QVBoxLayout()
        
        percent_input_layout = QHBoxLayout()
        percent_input_layout.addWidget(QLabel("Scale Percentage:"))
        self.percent_input = QSpinBox()
        self.percent_input.setRange(1, 500)
        self.percent_input.setValue(100)
        self.percent_input.setSuffix("%")
        percent_input_layout.addWidget(self.percent_input)
        percent_input_layout.addStretch()
        percent_layout.addLayout(percent_input_layout)
        
        self.percent_controls.setLayout(percent_layout)
        resize_layout.addWidget(self.percent_controls)
        self.percent_controls.setVisible(False)
        
        pixel_method.toggled.connect(lambda: self.toggle_resize_method(0))
        percent_method.toggled.connect(lambda: self.toggle_resize_method(1))
        
        resize_group.setLayout(resize_layout)
        layout.addWidget(resize_group)

        # Output Directory
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout()
        
        self.output_dir_label = QLabel("Default: Same as input file directory")
        output_dir_btn = QPushButton("Change Output Directory")
        output_dir_btn.clicked.connect(self.browse_output_dir)
        self.custom_output_dir = None
        
        output_layout.addWidget(self.output_dir_label)
        output_layout.addWidget(output_dir_btn)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status Label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Resize Button
        self.resize_btn = QPushButton("Resize Images")
        self.resize_btn.clicked.connect(self.resize_images)
        layout.addWidget(self.resize_btn)

        self.setLayout(layout)

    def toggle_resize_method(self, method):
        self.pixel_controls.setVisible(method == 0)
        self.percent_controls.setVisible(method == 1)

    def browse_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Image Files", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_paths:
            for file_path in file_paths:
                self.file_list.addItem(file_path)
            
            if not self.custom_output_dir:
                first_file_dir = os.path.dirname(file_paths[0])
                self.output_dir_label.setText(f"Default: {first_file_dir}")

    def clear_file_list(self):
        self.file_list.clear()

    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.custom_output_dir = dir_path
            self.output_dir_label.setText(dir_path)

    def resize_images(self):
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "Error", "Please select at least one image file")
            return

        if self.method_group.checkedId() == 0:  # Pixel method
            width = self.width_input.value()
            height = self.height_input.value()
            
            if width == 0 and height == 0:
                QMessageBox.warning(self, "Error", "At least one dimension (width or height) must be greater than 0")
                return
        else:  # Percentage method
            percent = self.percent_input.value()
            if percent <= 0:
                QMessageBox.warning(self, "Error", "Percentage must be greater than 0")
                return

        output_dir = self.custom_output_dir if self.custom_output_dir else os.path.dirname(self.file_list.item(0).text())
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.progress_bar.setValue(0)
        self.resize_btn.setEnabled(False)
        self.status_label.setText("Processing...")
        self.running_workers = 0

        # Process all selected files
        for i in range(self.file_list.count()):
            image_path = self.file_list.item(i).text()
            
            if self.method_group.checkedId() == 0:  # Pixel method
                width = self.width_input.value()
                height = self.height_input.value()
            else:  # Percentage method
                percent = self.percent_input.value()
                # Get original dimensions for percentage calculation
                with Image.open(image_path) as img:
                    original_width, original_height = img.size
                    width = int(original_width * percent / 100)
                    height = int(original_height * percent / 100)

            worker = ImageResizerWorker(image_path, output_dir, width, height)
            worker.progress_updated.connect(self.update_progress)
            worker.finished.connect(self.resize_complete)
            worker.error_occurred.connect(self.show_error)
            
            self.workers.append(worker)
            self.running_workers += 1
            worker.start()

    def update_progress(self, value, filename):
        # Update progress for individual files
        base_name = os.path.basename(filename)
        self.status_label.setText(f"Processing: {base_name}... ({value}%)")
        self.progress_bar.setValue(value)

    def resize_complete(self, output_path):
        self.running_workers -= 1
        if self.running_workers <= 0:
            self.all_processes_complete()

    def show_error(self, error_msg, filename):
        self.running_workers -= 1
        QMessageBox.critical(self, "Error", f"Failed to process {filename}:\n{error_msg}")
        if self.running_workers <= 0:
            self.all_processes_complete()

    def all_processes_complete(self):
        self.progress_bar.setValue(100)
        self.resize_btn.setEnabled(True)
        self.status_label.setText("All operations completed")
        QMessageBox.information(self, "Complete", "All images have been processed")