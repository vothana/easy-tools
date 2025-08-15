import os
from PyQt5.QtCore import  QThread, pyqtSignal
from pdf2image import convert_from_path
from PIL import Image

class PdfToImageWorker(QThread):
    progress_updated = pyqtSignal(int)
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, pdf_path, pages, output_dir, poppler_path=None):
        super().__init__()
        self.pdf_path = pdf_path
        self.pages = pages
        self.output_dir = output_dir
        self.poppler_path = poppler_path

    def run(self):
        try:
            # Convert specified pages
            images = convert_from_path(
                self.pdf_path,
                first_page=min(self.pages),
                last_page=max(self.pages),
                dpi=300,
                poppler_path=self.poppler_path
            )
            
            saved_files = []
            total_pages = len(images)
            for i, image in enumerate(images):
                # Only save the pages that were requested
                actual_page_number = i + min(self.pages)
                if actual_page_number in self.pages:
                    output_path = os.path.join(
                        self.output_dir,
                        f"{os.path.splitext(os.path.basename(self.pdf_path))[0]}_page_{actual_page_number}.png"
                    )
                    image.save(output_path, 'PNG')
                    saved_files.append(output_path)
                
                # Update progress
                progress = int((i + 1) / total_pages * 100)
                self.progress_updated.emit(progress)
            
            self.finished.emit(saved_files)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ImageResizerWorker(QThread):
    progress_updated = pyqtSignal(int, str)  # (progress, filename)
    finished = pyqtSignal(str)  # output_path
    error_occurred = pyqtSignal(str, str)  # (error_msg, filename)

    def __init__(self, image_path, output_dir, width, height):
        super().__init__()
        self.image_path = image_path
        self.output_dir = output_dir
        self.width = width
        self.height = height

    def run(self):
        try:
            # Open the image
            img = Image.open(self.image_path)
            
            # Calculate new dimensions
            if self.width == 0 and self.height > 0:
                # Calculate width based on height to maintain aspect ratio
                w_percent = (self.height / float(img.size[1]))
                new_width = int((float(img.size[0]) * float(w_percent)))
                new_size = (new_width, self.height)
            elif self.height == 0 and self.width > 0:
                # Calculate height based on width to maintain aspect ratio
                h_percent = (self.width / float(img.size[0]))
                new_height = int((float(img.size[1]) * float(h_percent)))
                new_size = (self.width, new_height)
            elif self.width > 0 and self.height > 0:
                # Use both dimensions
                new_size = (self.width, self.height)
            else:
                raise ValueError("At least one dimension (width or height) must be greater than 0")
            
            # Resize the image
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Save the resized image
            base_name = os.path.splitext(os.path.basename(self.image_path))[0]
            output_path = os.path.join(self.output_dir, f"{base_name}_resized.png")
            img.save(output_path, 'PNG', quality=95)
            
            self.progress_updated.emit(100, self.image_path)
            self.finished.emit(output_path)
        except Exception as e:
            self.error_occurred.emit(str(e), self.image_path)

