import sys
import os
import traceback
import json
import shlex
import shutil
from subprocess import Popen
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
import importlib.util

from PySide2.QtCore import Qt, QStandardPaths, QDir, QSize
from PySide2.QtGui import QIcon, QFont, QFontMetricsF
from PySide2.QtWidgets import (
    QApplication, QMainWindow, QMenu, QWidget, QLineEdit, QVBoxLayout, QDockWidget, QFormLayout, QGridLayout,
    QFileDialog, QDialog, QCheckBox, QMessageBox, QListWidget, QDialogButtonBox, QFrame, QTextEdit, QComboBox,
    QHBoxLayout, QPushButton, QSpinBox, QDoubleSpinBox, QStyleFactory, QTabWidget, QStyle, QProgressBar, QLabel
)
from PySide2.QtSvg import QSvgWidget
from pyqtgraph import PlotWidget, PlotItem, BarGraphItem

import symba_gui as package
from .cli import parse_args
from .dpi import inches_to_pixels as px
from .widgets import PathEdit
from .simulation import Simulation


class ChartEditor(QDialog):
    def __init__(self, parent=None, title=None, code=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Chart Editor")

        self.wtitle = QLineEdit(title or "Untitled Chart")
        self.wcode = QTextEdit()
        self.wcode.setText(code or "")
        font = QFont("Inconsolata", 12)
        font.setStretch(110)
        metrics = QFontMetricsF(font)
        self.wcode.setFont(font)
        self.wcode.setTabStopDistance(metrics.horizontalAdvance("a")*4)

        lytitle_container = QHBoxLayout()
        lytitle_container.setContentsMargins(0, 0, 0, 0)

        lytitle_container.addWidget(QLabel("Chart title:"))
        lytitle_container.addWidget(self.wtitle)

        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.wbutton_save = button_box.button(QDialogButtonBox.Save)
        self.wbutton_cancel = button_box.button(QDialogButtonBox.Cancel)

        self.wbutton_save.clicked.connect(self.accept)
        self.wbutton_cancel.clicked.connect(self.reject)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        ly = QVBoxLayout()
        self.setLayout(ly)

        ly.addLayout(lytitle_container)
        ly.addWidget(self.wcode)
        ly.addWidget(line)
        ly.addWidget(button_box)
    
    @property
    def title(self):
        return self.wtitle.text()
    
    @title.setter
    def title(self, text):
        self.wtitle.setText(text)
    
    @property
    def code(self):
        return self.wcode.toPlainText()
    
    @code.setter
    def code(self, text):
        self.wcode.setText(text)


class Chart(QWidget):
    """A user-made chart that loads from a python file."""
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.title = path.stem

        ly = QVBoxLayout()
        self.setLayout(ly)
        lyheader = QHBoxLayout()

        self.wedit_button = QPushButton("Edit")
        self.wdelete_button = QPushButton("Delete")

        lyheader.addWidget(QLabel(self.title))
        lyheader.addWidget(self.wedit_button)
        lyheader.addWidget(self.wdelete_button)

        self.wchart = QWidget()  # Initialized later in reload()

        ly.addLayout(lyheader)
        ly.addWidget(self.wchart)

        self.reload()

    def reload(self, path=None):
        self.path = path or self.path

        self.layout().removeWidget(self.wchart)

        # Import the module and call chart() function
        spec = importlib.util.spec_from_file_location(self.title, self.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.wchart = module.chart()

        self.layout().addWidget(self.wchart)

    def editor(self):
        """Create and return an editor that is linked to this chart."""
        with open(self.path, "r", encoding="utf-8") as f:
            code = f.read()
        
        dialog = ChartEditor(self, self.title, code)
        
        def done(result):
            if not result:
                return  # User cancelled

            title = dialog.title
            code = dialog.code

            self.path.unlink()
            self.path = self.path.parent / (title + ".py")

            with open(self.path, "w", encoding="utf-8") as f:
                f.write(code)

            self.reload()
        
        dialog.finished.connect(done)
        return dialog
