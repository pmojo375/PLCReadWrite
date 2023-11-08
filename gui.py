import sys
from pycomm3 import LogixDriver
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
import yaml
import pickle

tag_types = None
plc = None

def connect_to_plc(ip, connect_button):
    """
    Connects to a PLC using the given IP address and updates the connect_button text accordingly.

    Args:
        ip (str): The IP address of the PLC to connect to.
        connect_button (QPushButton): The button to update the text of.

    Returns:
        None
    """
    global plc

    if plc != None:
        plc.close()
        connect_button.setText("Connect")
        plc = None
    else:
        plc_instance = LogixDriver(ip)
        plc_instance.open()

        if plc_instance.connected:
            get_tags_from_yaml(ip, plc=plc_instance)

            connect_button.setText("Disconnect")

        plc = plc_instance


def serialize_to_yaml(data, **kwargs):
    """
    Serialize data to YAML format and write to a file.

    Args:
        data (list or object): The data to be serialized.
        file_name (str, optional): The name of the file to write to. Defaults to 'tag_values.yaml'.

    Returns:
        None
    """

    file_name = kwargs.get('file_name', 'tag_values.yaml')

    with open(file_name, 'w') as f:

        yaml_data = []

        if isinstance(data, list):
            for tag in data:
                if isinstance(tag.value, list):
                    for i, value in enumerate(tag.value):
                        yaml_data.append({f'{tag.tag}[{str(i)}]': value})
                else:
                    yaml_data.append({tag.tag: tag.value})
        else:
            yaml_data.append({tag.tag: tag.value})

        yaml.safe_dump(yaml_data, f, default_flow_style=False)


def crawl_and_format(obj, name, data):
    """
    Recursively crawls through a dictionary or list and formats the data into a flattened dictionary.

    Args:
        obj (dict or list): The object to crawl through.
        name (str): The name of the object.
        data (dict): The flattened dictionary to store the formatted data.

    Returns:
        dict: The flattened dictionary with the formatted data.
    """
    # obj is a dictionary
    if isinstance(obj, dict):
        for key, value in obj.items():
            data = crawl_and_format(value, f'{name}.{key}', data)
    # obj is a list
    elif isinstance(obj, list):
        # iterate through the list
        for i, value in enumerate(obj):
            data = crawl_and_format(value, f'{name}[{i}]', data)
    # obj is an elementary object
    else:
        data[f'{name}'] = f'{obj}'

    return data


def read_tag(ip, tags, result_window, **kwargs):
    """
    Reads the values of the given tags from the PLC with the given IP address and displays the results in the given result window.

    Args:
        ip (str): The IP address of the PLC to read from.
        tags (list): A list of tag names to read from the PLC.
        result_window (QPlainTextEdit): The window to display the results in.
        **kwargs: Additional keyword arguments.
            store_to_yaml (bool): Whether to store the results in a YAML file. Default is False.
            yaml_name (str): The name of the YAML file to store the results in. Default is 'tag_values.yaml'.
            plc (LogixDriver): An optional pre-initialized LogixDriver instance to use for reading the tags.

    Returns:
        list: A list of dictionaries containing the tag names and their corresponding values.
    """

    save_history(ip, tags)

    store_to_yaml = kwargs.get('store_to_yaml', False)

    return_data = []
    data = {}

    yaml_name = kwargs.get('yaml_name', 'tag_values.yaml')
    plc = kwargs.get('plc', None)

    try:
        if plc == None:
            with LogixDriver(ip) as plc:
                ret = plc.read(*tags)
        else:
            ret = plc.read(*tags)

        if store_to_yaml:
            if isinstance(ret, list):
                serialize_to_yaml(ret, file_name=yaml_name)
            else:
                serialize_to_yaml([ret], file_name=yaml_name)

        # loop through each tag in the list
        if len(tags) == 1:
            entry_tag = tags[0]
            value = ret.value
            return_data.append(crawl_and_format(value, entry_tag, {}))
        else:
            for i, tag in enumerate(tags):
                entry_tag = tags[i]
                value = ret[i].value
                return_data.append(crawl_and_format(value, entry_tag, {}))

        for result in return_data:
            for key, value in result.items():
                result_window.appendPlainText(f"{key} = {value}")
    except Exception as e:
        print(f"Error in read_tag: {e}")


def get_tags_from_yaml(ip, **kwargs):
    """
    Gets the data types from the YAML data.

    Args:
        data (dict): The YAML data.

    Returns:
        list: The list of data types.
    """
    ret = {}

    plc = kwargs.get('plc', None)

    try:
        if plc == None:
            with LogixDriver(ip) as plc:
                data = plc.tags_json
        else:
            data = plc.tags_json

        for tag_name in data.keys():
            tag = data[tag_name]
            if isinstance(tag['data_type'], str):
                ret[tag_name] = tag['data_type']
            elif isinstance(tag['data_type'], dict):
                internal_tags = tag['data_type']['internal_tags']
                ret = process_structure(internal_tags, ret, tag_name)

        return ret
    except Exception as e:
        print(f"Error in get_tags_from_yaml: {e}")
        return None


def process_structure(structure, array, name):
    """
    Recursively processes the structure of the YAML data and appends the data types to the array.

    Args:
        structure (dict): The structure of the YAML data.
        array (list): The list to append the data types to.
        name (str): The name of the current tag.

    Returns:
        list: The updated array with the data types appended.
    """
    for child in structure.keys():
        data_type = structure[child]['data_type']
        if child.startswith('_') or child.startswith('ZZZZZZZZZZ'):
            pass
        else:
            if isinstance(data_type, str):
                array[f'{name}.{child}'] = data_type
            elif isinstance(data_type, dict):
                array = process_structure(data_type['internal_tags'], array, f'{name}.{child}')
    
    return array


def save_history(ip, tag):
    if ip != '' and tag != '':
        f = open('plc_readwrite.pckl', 'wb')
        pickle.dump((ip, tag), f)
        f.close()


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

        self.read_button.clicked.connect(lambda: read_tag(self.ip_input.text(), [t.strip() for t in self.tag_input.text().split(',')], self.results, store_to_yaml=self.yaml_enabled.isChecked(), yaml_name=self.yaml_file.text(), plc=plc))

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

        self.connect_button.clicked.connect(lambda: connect_to_plc(self.ip_input.text(), self.connect_button))

        main_layout.addLayout(entry_layout)
        main_layout.addLayout(results_layout)

        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        try:
            f = open('plc_readwrite.pckl', 'rb')
            data_stored = pickle.load(f)
            f.close()
            self.ip_input.setText(str(data_stored[0]))
            self.tag_input.setText(str(data_stored[1]))
        except FileNotFoundError:
            pass

app = QApplication(sys.argv)
qdarktheme.setup_theme()
window = MainWindow()
window.show()

app.exec_()