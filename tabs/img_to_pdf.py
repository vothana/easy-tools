import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QMessageBox, QListWidget, 
                             QListWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QColor
from fpdf import FPDF
from PIL import Image


class ImageToPdfTab(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_folder = ""
        self.additional_images = []
        self.MIN_WIDTH = 300  # 300pt = ~106mm
        self.MAX_WIDTH = 584   # 584pt = ~206mm
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Folder selection section
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setWordWrap(True)
        
        select_folder_btn = QPushButton("Select Folder")
        select_folder_btn.setIcon(QIcon.fromTheme("folder"))
        select_folder_btn.clicked.connect(self.select_folder)
        
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(select_folder_btn)
        layout.addLayout(folder_layout)

        # Add individual images button
        add_images_btn = QPushButton("Add Images")
        add_images_btn.setIcon(QIcon.fromTheme("list-add"))
        add_images_btn.clicked.connect(self.add_images)
        layout.addWidget(add_images_btn)

        # Image list with scrollable area
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        layout.addWidget(self.list_widget)

        # Convert button
        self.convert_btn = QPushButton("Convert to PDF")
        self.convert_btn.clicked.connect(self.convert_images_to_pdf)
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)

        layout.addStretch()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Images")
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f"Selected: {folder}")
            self.update_image_list()
            self.check_convert_button()

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Image files", "", 
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        
        if files:
            self.additional_images.extend(files)
            self.update_image_list()
            self.check_convert_button()

    def update_image_list(self):
        self.list_widget.clear()
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

        # Add folder images first (sorted by name)
        if self.selected_folder:
            folder_images = []
            for file in sorted(os.listdir(self.selected_folder)):
                if file.lower().endswith(valid_extensions):
                    full_path = os.path.join(self.selected_folder, file)
                    folder_images.append(full_path)
            
            for img_path in folder_images:
                self.add_list_item(img_path, is_folder_image=True)

        # Add additional images
        for img_path in self.additional_images:
            self.add_list_item(img_path, is_folder_image=False)

    def add_list_item(self, img_path, is_folder_image):
        item = QListWidgetItem()
        item.setData(Qt.UserRole, (img_path, is_folder_image))
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # File name label
        label = QLabel(os.path.basename(img_path))
        label.setStyleSheet("QLabel { margin-right: 10px; }")
        if is_folder_image:
            label.setStyleSheet("QLabel { margin-right: 10px; font-weight: bold; }")
        layout.addWidget(label)
        
        # Only show delete button for additional images
        if not is_folder_image:
            # Delete button
            delete_btn = QPushButton()
            delete_btn.setIcon(QIcon.fromTheme("list-remove"))
            delete_btn.setFixedSize(24, 24)
            delete_btn.clicked.connect(lambda: self.remove_item(item))
            layout.addWidget(delete_btn)
        
        layout.addStretch()
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    def remove_item(self, item):
        img_path, is_folder_image = item.data(Qt.UserRole)
        if not is_folder_image and img_path in self.additional_images:
            self.additional_images.remove(img_path)
            self.list_widget.takeItem(self.list_widget.row(item))
            self.check_convert_button()

    def check_convert_button(self):
        has_images = (self.list_widget.count() > 0)
        self.convert_btn.setEnabled(has_images)
        if not has_images:
            self.reset_button_style()

    def calculate_page_size(self, img_width, img_height):
        """Calculate PDF page size maintaining aspect ratio within constraints"""
        # Convert from points to mm (1pt = 0.352778mm)
        min_width_mm = self.MIN_WIDTH * 0.352778
        max_width_mm = self.MAX_WIDTH * 0.352778
        
        # Original dimensions in mm (assuming 72dpi)
        width_mm = img_width * 0.352778
        height_mm = img_height * 0.352778
        
        # Adjust width if needed
        if width_mm < min_width_mm:
            scale_factor = min_width_mm / width_mm
            width_mm = min_width_mm
            height_mm *= scale_factor
        elif width_mm > max_width_mm:
            scale_factor = max_width_mm / width_mm
            width_mm = max_width_mm
            height_mm *= scale_factor
        
        return width_mm, height_mm

    def convert_images_to_pdf(self):
        if self.list_widget.count() == 0:
            return
            
        try:
            # Determine output directory
            if self.selected_folder:
                output_dir = self.selected_folder
            elif self.additional_images:
                output_dir = os.path.dirname(self.additional_images[0])
            else:
                QMessageBox.warning(self, "Error", "No output directory available")
                return
                
            output_path = os.path.join(output_dir, "output.pdf")
            
            # Check if file exists
            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self, "File Exists", 
                    "output.pdf already exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Update UI for processing
            self.convert_btn.setEnabled(False)
            self.convert_btn.setText("Processing...")
            QApplication.processEvents()
            
            # Create PDF
            pdf = FPDF(unit="pt")
            pdf.set_auto_page_break(False)
            
            # Process all images in list order
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                img_path, _ = item.data(Qt.UserRole)
                
                with Image.open(img_path) as img:
                    img_width, img_height = img.size
                    
                    # Calculate page size within constraints
                    page_width, page_height = self.calculate_page_size(img_width, img_height)
                    
                    # Convert back to points for FPDF
                    page_width_pt = page_width / 0.352778
                    page_height_pt = page_height / 0.352778
                    
                    # Create page with calculated size
                    pdf.add_page(format=(page_width_pt, page_height_pt))
                    
                    # Add image maintaining aspect ratio
                    pdf.image(img_path, 0, 0, page_width_pt, page_height_pt)
            
            # Save PDF
            pdf.output(output_path)
            
            # Update UI
            self.convert_btn.setText("Conversion Complete!")
            self.convert_btn.setStyleSheet("background-color: green; color: white;")
            QMessageBox.information(self, "Success", 
                                  f"PDF created successfully at:\n{output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")
        finally:
            self.reset_button_style()

    def reset_button_style(self):
        self.convert_btn.setStyleSheet("")
        self.convert_btn.setText("Convert to PDF")
        self.check_convert_button()