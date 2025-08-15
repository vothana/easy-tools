import os
from PyQt5.QtWidgets import ( QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox,
                              QGroupBox, QCheckBox,
                             QDialog, QDialogButtonBox)
from pdf2image import convert_from_path

class PopplerConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Poppler Configuration")
        self.setModal(True)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Status Group
        status_group = QGroupBox("Current Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel()
        self.update_status_label()
        
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Configuration Group
        config_group = QGroupBox("Configuration Options")
        config_layout = QVBoxLayout()
        
        # Path selection
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to Poppler bin directory")
        if self.parent.pdf_tab.poppler_path:
            self.path_edit.setText(self.parent.pdf_tab.poppler_path)
            
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_poppler_path)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)
        config_layout.addLayout(path_layout)
        
        # Auto-detect
        self.auto_detect_check = QCheckBox("Enable auto-detection")
        self.auto_detect_check.setChecked(True)
        config_layout.addWidget(self.auto_detect_check)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Test Button
        test_btn = QPushButton("Test Configuration")
        test_btn.clicked.connect(self.test_poppler)
        layout.addWidget(test_btn)

        # Dialog Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept_config)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def update_status_label(self):
        if not self.parent.pdf_tab.poppler_path:
            self.status_label.setText("Status: ❌ Poppler not configured\nUsing system PATH if available")
        else:
            self.status_label.setText(f"Status: ✔️ Poppler configured\nPath: {self.parent.pdf_tab.poppler_path}")

    def browse_poppler_path(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Poppler Bin Directory")
        if dir_path:
            self.path_edit.setText(dir_path)
            self.auto_detect_check.setChecked(False)

    def test_poppler(self):
        test_file = os.path.join(os.path.dirname(__file__), "test\\poppler_test.pdf")
        
        # Create test PDF if it doesn't exist
        if not os.path.exists(test_file):
            try:
                from reportlab.pdfgen import canvas
                c = canvas.Canvas(test_file)
                c.drawString(100, 100, "Poppler Test Document")
                c.save()
            except ImportError:
                QMessageBox.warning(self, "Warning", 
                                  "Test PDF generation requires reportlab.\n"
                                  "Using built-in test instead.")
                test_file = None

        try:
            if test_file:
                # Test with actual PDF file
                images = convert_from_path(
                    test_file,
                    poppler_path=self.path_edit.text() or None,
                    first_page=1,
                    last_page=1
                )
            else:
                # Fallback test
                convert_from_path("", poppler_path=self.path_edit.text() or None)
                
            QMessageBox.information(self, "Success", "Poppler configuration is working correctly!")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Poppler test failed:\n{str(e)}\n\n"
                               "Please ensure:\n"
                               "1. Path points to Poppler 'bin' directory\n"
                               "2. Required DLLs are present")

    def accept_config(self):
        if self.auto_detect_check.isChecked():
            self.parent.pdf_tab.auto_detect_poppler()
        else:
            self.parent.pdf_tab.poppler_path = self.path_edit.text() or None
        
        self.update_status_label()
        self.accept()