import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QMessageBox, QListWidget, 
                             QListWidgetItem, QAbstractItemView)
from PyQt5.QtCore import Qt, QSize, QMimeData
from PyQt5.QtGui import QIcon, QColor, QDragEnterEvent, QDropEvent
from PyPDF2 import PdfMerger


class CombinePdfTab(QWidget):
    def __init__(self):
        super().__init__()
        self.pdf_files = []
        self.init_ui()
        self.setAcceptDrops(True)

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add PDF button
        add_btn = QPushButton("Add PDFs")
        add_btn.setIcon(QIcon.fromTheme("list-add"))
        add_btn.clicked.connect(self.add_pdfs)
        layout.addWidget(add_btn)

        # PDF list with scrollable area
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragEnabled(True)
        layout.addWidget(self.list_widget)

        # Convert button
        self.convert_btn = QPushButton("Combine PDFs")
        self.convert_btn.clicked.connect(self.combine_pdfs)
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)

        layout.addStretch()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        new_files = []
        
        for url in urls:
            if url.isLocalFile():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    if file_path not in self.pdf_files:
                        new_files.append(file_path)
        
        if new_files:
            self.pdf_files.extend(new_files)
            for file in new_files:
                self.add_list_item(file)
            
            self.convert_btn.setEnabled(len(self.pdf_files) > 0)

    def add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF files", "", "PDF Files (*.pdf)"
        )
        
        if files:
            for file in files:
                if file not in self.pdf_files:
                    self.pdf_files.append(file)
                    self.add_list_item(file)
            
            self.convert_btn.setEnabled(len(self.pdf_files) > 0)

    def add_list_item(self, file_path):
        item = QListWidgetItem()
        item.setData(Qt.UserRole, file_path)
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # File name label
        label = QLabel(os.path.basename(file_path))
        label.setStyleSheet("QLabel { margin-right: 10px; }")
        layout.addWidget(label)
        
        # Edit button
        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon.fromTheme("document-edit"))
        edit_btn.setFixedSize(24, 24)
        edit_btn.clicked.connect(lambda: self.edit_item(item))
        layout.addWidget(edit_btn)
        
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

    def edit_item(self, item):
        old_path = item.data(Qt.UserRole)
        new_path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF file", os.path.dirname(old_path), "PDF Files (*.pdf)"
        )
        
        if new_path and new_path != old_path:
            index = self.pdf_files.index(old_path)
            self.pdf_files[index] = new_path
            self.add_list_item(new_path)
            self.list_widget.takeItem(self.list_widget.row(item))

    def remove_item(self, item):
        file_path = item.data(Qt.UserRole)
        self.pdf_files.remove(file_path)
        self.list_widget.takeItem(self.list_widget.row(item))
        self.convert_btn.setEnabled(len(self.pdf_files) > 0)

    def combine_pdfs(self):
        if not self.pdf_files:
            return
            
        try:
            # Get output directory from first file
            output_dir = os.path.dirname(self.pdf_files[0])
            output_path = os.path.join(output_dir, "combined.pdf")
            
            # Check if file exists
            if os.path.exists(output_path):
                reply = QMessageBox.question(
                    self, "File Exists", 
                    "combined.pdf already exists. Overwrite?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Update UI
            self.convert_btn.setEnabled(False)
            self.convert_btn.setText("Processing...")
            QApplication.processEvents()
            
            # Combine PDFs
            merger = PdfMerger()
            
            # Use the order from the list widget
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                file_path = item.data(Qt.UserRole)
                merger.append(file_path)
            
            merger.write(output_path)
            merger.close()
            
            # Update UI
            self.convert_btn.setText("Combination Complete!")
            self.convert_btn.setStyleSheet("background-color: green; color: white;")
            QMessageBox.information(self, "Success", 
                                  f"PDFs combined successfully at:\n{output_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")
        finally:
            self.reset_button_style()

    def reset_button_style(self):
        self.convert_btn.setStyleSheet("")
        self.convert_btn.setText("Combine PDFs")
        self.convert_btn.setEnabled(len(self.pdf_files) > 0)