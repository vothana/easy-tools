from dialogs.dialogs import PopplerConfigDialog
from PyQt5.QtWidgets import QAction

class CustomMenu:
    @staticmethod
    def create_menu_bar(mainWindow):
        menubar = mainWindow.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        exit_action = QAction('Exit', mainWindow)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(mainWindow.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        poppler_action = QAction('Poppler Configuration...', mainWindow)
        poppler_action.triggered.connect(lambda: CustomMenu.show_poppler_config(mainWindow))
        settings_menu.addAction(poppler_action)

    @staticmethod
    def show_poppler_config(mainWindow):
        dialog = PopplerConfigDialog(mainWindow)
        dialog.exec_()
