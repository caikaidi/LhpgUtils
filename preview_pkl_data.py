import sys
import pandas as pd
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QSplitter,
    QFileDialog,
    QListWidget,
    QStackedWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QPalette


class DropArea(QLabel):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("QLabel { border: 2px dashed #aaa; }")
        self.setText("Drag and drop a PKL file here")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            # Only accept the first file
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.main_window.load_pkl_data(file_path)
            event.acceptProposedAction()
        else:
            event.ignore()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Visualization")
        self.setGeometry(100, 100, 1200, 900)

        # Create main layout and sidebar
        main_layout = QHBoxLayout()

        # Create sidebar
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)

        # Sidebar options
        self.sidebar_list = QListWidget()
        self.sidebar_list.addItem("View PKL Data")
        # Future options can be added here
        sidebar_layout.addWidget(self.sidebar_list)
        self.sidebar_list.currentRowChanged.connect(self.display_settings)

        main_layout.addWidget(self.sidebar, 2)

        # Create central area
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)

        # Use QSplitter to separate upper (plot) and lower (settings) parts
        splitter = QSplitter(Qt.Vertical)

        # Upper part for plotting
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True)
        # font
        font = {"color": "k", "font-size": "16pt", "font-family": "Times New Roman"}
        self.plot_widget.setLabel("left", "Y-Axis", **font)
        self.plot_widget.setLabel("bottom", "X-Axis", **font)
        axis_font = pg.QtGui.QFont("Times New Roman", 14)
        self.plot_widget.getAxis("left").setTickFont(axis_font)
        self.plot_widget.getAxis("bottom").setTickFont(axis_font)
        # show top and right borders
        self.plot_widget.showAxis("top")
        self.plot_widget.showAxis("right")
        self.plot_widget.getAxis("top").setTicks([])
        self.plot_widget.getAxis("right").setTicks([])
        self.plot_widget.setDownsampling(mode="peak")
        self.plot_widget.setClipToView(True)
        splitter.addWidget(self.plot_widget)

        # Lower part for settings with QStackedWidget
        self.settings_stack = QStackedWidget()

        # Settings for 'View PKL Data'
        self.view_pkl_settings = QWidget()
        view_pkl_layout = QVBoxLayout(self.view_pkl_settings)

        # Load PKL Data button
        self.load_pkl_button = QPushButton("Load PKL Data")
        self.load_pkl_button.clicked.connect(self.load_pkl_data)
        view_pkl_layout.addWidget(self.load_pkl_button)

        # Drag and drop area
        self.drop_area = DropArea(self)
        view_pkl_layout.addWidget(self.drop_area)

        # X-axis and Y-axis dropdowns
        self.x_axis_label = QLabel("Select X-axis:")
        self.x_axis_combobox = QComboBox()
        self.y_axis_label = QLabel("Select Y-axis:")
        self.y_axis_combobox = QComboBox()
        self.plot_button = QPushButton("Plot Data")
        self.plot_button.clicked.connect(self.plot_data)

        view_pkl_layout.addWidget(self.x_axis_label)
        view_pkl_layout.addWidget(self.x_axis_combobox)
        view_pkl_layout.addWidget(self.y_axis_label)
        view_pkl_layout.addWidget(self.y_axis_combobox)
        view_pkl_layout.addWidget(self.plot_button)

        self.settings_stack.addWidget(self.view_pkl_settings)

        splitter.addWidget(self.settings_stack)

        # Add splitter to central layout
        central_layout.addWidget(splitter)
        main_layout.addWidget(central_widget, 8)

        # Create main window widget
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Initialize data variable
        self.data = None

        # Apply CSS styling
        self.apply_styles()

    def display_settings(self, index):
        self.settings_stack.setCurrentIndex(index)

    def load_pkl_data(self, file_path=None):
        if not file_path:
            # Open file dialog to select .pkl file
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(
                self, "Open PKL File", "", "Pickle Files (*.pkl)"
            )
            if not file_path:
                return

        self.data = pd.read_pickle(file_path)
        self.x_axis_combobox.clear()
        self.y_axis_combobox.clear()
        for key in self.data.columns:
            self.x_axis_combobox.addItem(key)
            self.y_axis_combobox.addItem(key)

    def plot_data(self):
        # Get selected x-axis and y-axis data
        x_axis = self.x_axis_combobox.currentText()
        y_axis = self.y_axis_combobox.currentText()

        x_data = self.data[x_axis].to_numpy()
        y_data = self.data[y_axis].to_numpy()

        # Clear previous plots and plot new data
        self.plot_widget.clear()
        # self.plot_widget.setBackground('w')
        # self.plot_widget.showGrid(x=True, y=True)
        pen = pg.mkPen(color="#1f77b4", width=2)
        self.plot_widget.plot(x_data, y_data, pen=pen)
        self.plot_widget.setLabel("bottom", x_axis)
        self.plot_widget.setLabel("left", y_axis)

    def apply_styles(self):
        style_sheet = """
        QWidget {
            background-color: #F0F0F0;
            font-size: 14px;
        }

        QPushButton {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 24px;
            text-align: center;
            font-size: 14px;
            margin: 4px 2px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #45a049;
        }

        QComboBox {
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }

        QLabel {
            font-weight: bold;
        }

        QListWidget {
            border: none;
        }

        QListWidget::item {
            padding: 10px;
        }

        QListWidget::item:selected {
            background-color: #d3d3d3;
        }

        QSplitter::handle {
            background-color: #ccc;
        }
        """
        self.setStyleSheet(style_sheet)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
