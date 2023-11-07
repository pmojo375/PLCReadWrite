import sys
import qdarktheme
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QDoubleSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QRadioButton,
    QWidget,
    QPlainTextEdit,
)

def read_button_clicked(tag_input, ip_input, yaml_enabled, yaml_file, results):
    results.appendPlainText(f"Read button clicked with tag {tag_input.text()} and ip {ip_input.text()}")
    results.appendPlainText(f"Yaml enabled: {yaml_enabled.isChecked()} with file: {yaml_file.text()}")

def write_button_clicked(tag_input, ip_input, write_value, yaml_enabled, yaml_file, results):
    results.appendPlainText(f"Write button clicked with tag {tag_input.text()}, ip {ip_input.text()}, and value {write_value.text()}")
    results.appendPlainText(f"Yaml enabled: {yaml_enabled.isChecked()} with file: {yaml_file.text()}")

def trend_button_clicked(trend_button, tag_input, ip_input, yaml_enabled, yaml_file, trend_rate, results):
    if trend_button.text() == "Start Trend":
        trend_button.setText("Stop Trend")
    else:
        trend_button.setText("Start Trend")

    results.appendPlainText(f"Trend button clicked with tag {tag_input.text()}, ip {ip_input.text()}, and rate {trend_rate.value()}")
    results.appendPlainText(f"Yaml enabled: {yaml_enabled.isChecked()} with file: {yaml_file.text()}")

def show_trend_plot(tag_input, ip_input, yaml_enabled, yaml_file, trend_rate, results):
    results.appendPlainText(f"Show trend plot button clicked with tag {tag_input.text()}, ip {ip_input.text()}, and rate {trend_rate.value()}")
    results.appendPlainText(f"Yaml enabled: {yaml_enabled.isChecked()} with file: {yaml_file.text()}")

def monitor_button_clicked(monitor_button, tag_input, ip_input, yaml_enabled, yaml_file, monitor_rate, monitor_value, enable_event, read_selected_radio, write_selected_radio, results):
    if monitor_button.text() == "Monitor":
        monitor_button.setText("Stop Monitoring")
    else:
        monitor_button.setText("Monitor")

    results.appendPlainText(f"Monitor button clicked with tag {tag_input.text()}, ip {ip_input.text()}, and rate {monitor_rate.value()}")
    results.appendPlainText(f"Yaml enabled: {yaml_enabled.isChecked()} with file: {yaml_file.text()}")
    results.appendPlainText(f"Enable event: {enable_event.isChecked()} with value {monitor_value.text()}")

    if read_selected_radio.isChecked():
        results.appendPlainText("Read selected")
    elif write_selected_radio.isChecked():
        results.appendPlainText("Write selected")


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("PLC Read/Write")

        # Create layouts
        main_layout = QHBoxLayout()
        entry_layout = QVBoxLayout()
        results_layout = QVBoxLayout()
        ip_layout = QHBoxLayout()

        # Create tab widget
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)

        # Create read tab widgets
        self.read_tab = QWidget()
        self.read_button = QPushButton("Read")

        # Read tab layouts
        read_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)

        # Add to layouts
        read_tab_layout.addWidget(self.read_button)

        self.read_tab.setLayout(read_tab_layout)
        
        tabs.addTab(self.read_tab, "Read")

        self.read_button.clicked.connect(lambda: read_button_clicked(self.tag_input, self.ip_input, self.yaml_enabled, self.yaml_file, self.results))

        # Create write tab widgets
        write_tab = QWidget()
        self.write_button = QPushButton("Write")
        self.write_value = QLineEdit()

        self.write_value.setPlaceholderText("Value")

        # Write tab layouts
        write_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)

        # Add to layouts
        write_tab_layout.addWidget(self.write_value)
        write_tab_layout.addWidget(self.write_button)

        self.write_button.clicked.connect(lambda: write_button_clicked(self.tag_input, self.ip_input, self.write_value, self.yaml_enabled, self.yaml_file, self.results))

        write_tab.setLayout(write_tab_layout)

        tabs.addTab(write_tab, "Write")

        # Create trend tab widgets
        trend_tab = QWidget()
        self.trend_button = QPushButton("Start Trend")
        self.trend_plot_button = QPushButton("Show Trend Plot")
        self.trend_rate = QDoubleSpinBox()

        self.trend_rate.setRange(0.1, 60)
        self.trend_rate.setValue(1)
        self.trend_rate.setSuffix(" seconds between reads")
        self.trend_rate.setSingleStep(0.1)

        self.trend_button.clicked.connect(lambda: trend_button_clicked(self.trend_button, self.tag_input, self.ip_input, self.yaml_enabled, self.yaml_file, self.trend_rate, self.results))

        # Trend tab layout
        trend_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)

        # Add to layouts
        trend_tab_layout.addWidget(self.trend_rate)
        trend_tab_layout.addWidget(self.trend_button)
        trend_tab_layout.addWidget(self.trend_plot_button)

        self.trend_plot_button.clicked.connect(lambda: show_trend_plot(self.tag_input, self.ip_input, self.yaml_enabled, self.yaml_file, self.trend_rate, self.results))

        trend_tab.setLayout(trend_tab_layout)

        tabs.addTab(trend_tab, "Trend")

        # Create write tab widgets
        monitor_tab = QWidget()
        self.monitor_button = QPushButton("Monitor")
        self.monitor_value = QLineEdit()
        self.monitor_rate = QDoubleSpinBox()
        self.enable_event = QCheckBox("Enable Read/Write On Event")
        self.read_selected_radio  = QRadioButton("Read On Event")
        self.write_selected_radio  = QRadioButton("Write On Event")

        self.monitor_rate.setRange(0.1, 60)
        self.monitor_rate.setValue(1)
        self.monitor_rate.setSuffix(" seconds between reads")
        self.monitor_rate.setSingleStep(0.1)

        self.monitor_value.setPlaceholderText("Value to Monitor")

        # Monitor tab layouts
        monitor_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        self.monitor_radio_layout = QHBoxLayout()

        self.monitor_radio_layout.addWidget(self.read_selected_radio)
        self.monitor_radio_layout.addWidget(self.write_selected_radio)

        # Add to layouts
        monitor_tab_layout.addWidget(self.monitor_value)
        monitor_tab_layout.addWidget(self.monitor_rate)
        monitor_tab_layout.addWidget(self.enable_event)
        monitor_tab_layout.addLayout(self.monitor_radio_layout)
        monitor_tab_layout.addWidget(self.monitor_button)

        self.monitor_button.clicked.connect(lambda: monitor_button_clicked(self.monitor_button, self.tag_input, self.ip_input, self.yaml_enabled, self.yaml_file, self.monitor_rate, self.monitor_value, self.enable_event, self.read_selected_radio, self.write_selected_radio, self.results))

        monitor_tab.setLayout(monitor_tab_layout)

        tabs.addTab(monitor_tab, "Monitor")

        yaml_file_layout = QHBoxLayout()

        # Create main layout widgets
        self.ip_input = QLineEdit()
        self.tag_input = QLineEdit()
        self.yaml_enabled = QCheckBox("Read/Store to YAML")
        self.yaml_file = QLineEdit()
        self.yaml_file_browser = QPushButton("Browse")

        self.tag_input.setPlaceholderText("Tag")
        self.ip_input.setMaxLength(15)
        self.ip_input.setPlaceholderText("IP Address")

        yaml_file_layout.addWidget(self.yaml_file)
        yaml_file_layout.addWidget(self.yaml_file_browser)

        self.yaml_file_browser.clicked.connect(lambda: self.yaml_file.setText(QFileDialog.getOpenFileName()[0]))

        # Add to main layout
        ip_layout.addWidget(self.ip_input)
        self.connect_button = QPushButton("Connect")
        ip_layout.addWidget(self.connect_button)
        entry_layout.addLayout(ip_layout)
        entry_layout.addWidget(self.tag_input)
        entry_layout.addWidget(self.yaml_enabled)
        entry_layout.addLayout(yaml_file_layout)
        entry_layout.addWidget(tabs)
        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        results_layout.addWidget(self.results)

        main_layout.addLayout(entry_layout)
        main_layout.addLayout(results_layout)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

app = QApplication(sys.argv)
qdarktheme.setup_theme()
window = MainWindow()
window.show()

app.exec_()