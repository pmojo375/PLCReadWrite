import sys
from pycomm3 import LogixDriver
import qdarktheme
from PySide2.QtCore import Qt, QThread, Signal, QObject
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
import re
import datetime
import threading

tag_types = None
plc = None
trender = None

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
    global tag_types

    if plc != None:
        plc.close()
        connect_button.setText("Connect")
        plc = None
    else:
        plc_instance = LogixDriver(ip)
        plc_instance.open()

        if plc_instance.connected:
            tag_types = get_tags_from_yaml(ip, plc=plc_instance)

            connect_button.setText("Disconnect")

        plc = plc_instance


def serialize_to_yaml(data, **kwargs):
    """
    Serialize data to YAML format and write to a file.

    Args:
        data (list or object): The data to be serialized.
        yaml_file (str, optional): The name of the file to write to. Defaults to 'tag_values.yaml'.

    Returns:
        None
    """

    yaml_file = kwargs.get('yaml_file', 'tag_values.yaml')

    with open(yaml_file, 'w') as f:

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

# serializes the returned tag or list of tags to yaml format and writes to a file
def deserialize_from_yaml(yaml_name):
    with open(yaml_name, 'r') as f:
        yaml_data = yaml.safe_load(f)
        tag_values = []
        for item in yaml_data:
            for key, value in item.items():
                tag_values.append({'tag': key, 'value': value})
    
    return tag_values


def iterate_value(name, value, ret):
    if type(value) == list:
        for i, value in enumerate(value):
            iterate_value(f'{name}[{i}]', value, ret)
    elif type(value) == dict:
        for key, value in value.items():
            iterate_value(f'{name}.{key}', value,ret)
    else:
        ret.append((name, value))
    
    return ret


def process_yaml_read(data):

    processed_data = []

    for tag in data:
        tag_name = tag['tag']
        tag_value  = tag['value']

        processed_data = iterate_value(tag_name, tag_value, processed_data)

    return processed_data


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
            yaml_file (str): The name of the YAML file to store the results in. Default is 'tag_values.yaml'.
            plc (LogixDriver): An optional pre-initialized LogixDriver instance to use for reading the tags.

    Returns:
        list: A list of dictionaries containing the tag names and their corresponding values.
    """

    save_history(ip, tags)

    tags = [t.strip() for t in tags.split(',')]
        
    store_to_yaml = kwargs.get('store_to_yaml', False)
    yaml_file = kwargs.get('yaml_file', 'tag_values.yaml')
    plc = kwargs.get('plc', None)

    return_data = []

    try:
        if plc == None:
            with LogixDriver(ip) as plc:
                ret = plc.read(*tags)
        else:
            ret = plc.read(*tags)

        if store_to_yaml:
            if isinstance(ret, list):
                serialize_to_yaml(ret, yaml_file=yaml_file)
            else:
                serialize_to_yaml([ret], yaml_file=yaml_file)

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


def set_data_type(value, tag):
    """
    Converts the given value to the data type specified by the tag.

    Args:
        value (str): The value to be converted.
        tag (str): The tag specifying the data type.

    Returns:
        The converted value.

    Raises:
        ValueError: If the value cannot be converted to the specified data type.
    """
    try:
        # Check if the tag is in the tag_list
        if tag in tag_types:
            # Get the data type from the tag_list
            type = tag_types[tag]

            # Set the data type based on the type from the tag_list
            if type == 'STRING':
                return str(value)
            elif type == 'DINT':
                return int(value)
            elif type == 'INT':
                return int(value)
            elif type == 'SINT':
                return int(value)
            elif type == 'REAL':
                return float(value)
            elif type == 'BOOL':
                if value == '1' or value == 'True' or value == 'true':
                    return True
                else:
                    return False
        else:
            # If the tag is not in the tag_list, determine the data type based on the value
            if not value:
                return ''

            if value == '':
                return ''

            value = value.strip()

            if value.lower() in ['true', 'false']:
                return value.lower() == 'true'

            if (value.startswith('"') and value.endswith('"') or value.startswith("'") and value.endswith("'")):
                inner_value = value[1:-1]

                if '"' in inner_value or "'" in inner_value:
                    raise ValueError(f"Unexpected quote in value: {value}")

                return inner_value
            if value.startswith('-'):
                if value[1:].isdigit():
                    return int(value)

            if value.count('.') == 1:
                return float(value)

            if value.isdigit():
                return int(value)

            return value

    except Exception as e:
        # If there is an error, print the error message and return None
        print(f"Error in set_data_type: {e}")
        return None


def write_tag(ip, tags, values, results, **kwargs):
    """
    Writes a value to a tag in a PLC.

    Args:
        ip (str): The IP address of the PLC.
        tag (str): The tag to write to.
        value (any): The value to write to the tag.
        plc (LogixDriver, optional): An existing LogixDriver instance to use instead of creating a new one.

    Returns:
        bool: True if the write was successful, False otherwise.
    """
    print(tags)
    save_history(ip, tags)

    plc = kwargs.get('plc', None)
    yaml_enabed = kwargs.get('yaml_enabled', False)
    yaml_file = kwargs.get('yaml_file', 'tag_values.yaml')

    tags = [t.strip() for t in tags.split(',')]

    if not yaml_enabed:
        values = [t.strip() for t in values.split(',')]

        write_data = []

        for i, tag in enumerate(tags):
            write_data.append((tag, set_data_type(values[i], tag)))

        try:
            if plc == None:
                with LogixDriver(ip) as plc:
                    if plc.write(*write_data):
                        results.appendPlainText(f"Successfully wrote to tags to PLC")
            else:


                if plc.write(*write_data):
                    results.appendPlainText(f"Successfully wrote to tags to PLC")
        except Exception as e:
            print(f"Error in write_tag: {e}")
            return None
    else:

        tags = process_yaml_read(deserialize_from_yaml(yaml_file))

        try:
            if plc == None:
                with LogixDriver(ip) as plc:
                    return plc.write(*tags)
            else:
                if plc.write(*tags):
                    results.appendPlainText(f"Successfully wrote to tags to PLC")
        except Exception as e:
            print(f"Error in write_tags_from_yaml: {e}")
            return None


def save_history(ip, tag):
    if ip != '' and tag != '':
        f = open('plc_readwrite.pckl', 'wb')
        pickle.dump((ip, tag), f)
        f.close()


def validate_ip(ip):
    """
    Validates if the given IP address is in the correct format.

    Args:
        ip (str): The IP address to validate.

    Returns:
        bool: True if the IP address is in the correct format, False otherwise.
    """
    pattern = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    if pattern.match(ip):
        return True
    else:
        return False


class Trender(QObject):
    update = Signal(str)
    finished = Signal()

    def __init__(self):
        super(Trender, self).__init__()
        self.running = False
        self.ip = None
        self.tags = None
        self.interval = 1
        self.results = []
        self.timestamps = []
        self.first_pass = True
        self.single_tag = True
        self.plc = None

    def run(self):
        start_time = datetime.datetime.now()
        # Convert tag input to a list
        formatted_tags = [t.strip() for t in self.tags.split(',')]

        try:
            if plc == None:
                self.plc = LogixDriver(self.ip)
                self.plc.open()
            else:
                self.plc = plc
        except Exception as e:
            print(f"Error in Trender: {e}")

        while self.running:

            try:
                result = self.plc.read(*formatted_tags)

                if not isinstance(result, list):
                    result = [result]

                if self.first_pass:
                    if len(result) > 1:
                        self.single_tag = False

                        for i in range(len(result)):
                            self.results.append([])
                    
                    self.first_pass = False
                    
                self.update.emit(f'\nTimestamp: {datetime.datetime.now().strftime("%I:%M:%S:%f %p")}')

                if self.single_tag:
                    self.update.emit(f'{formatted_tags[0]} = {result[0].value}')
                    self.results.append(result[0].value)
                else:
                    for i, r in enumerate(result):            
                        self.update.emit(f'{formatted_tags[i]} = {r.value}')
                        self.results[i].append(r.value)
                
                self.timestamps.append((datetime.datetime.now() - start_time).total_seconds() * 1000)
            except Exception as e:
                print(f"Error in Trender: {e}")
            
            QThread.sleep(self.interval)
    
    def stop(self):
        self.running = False
        self.finished.emit()


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

        self.trender = Trender()
        self.thread = QThread()
        self.trender.moveToThread(self.thread)
        self.thread.started.connect(self.trender.run)
        self.trender.update.connect(self.print_resuts)
        #self.trender.finished.connect(self.trender.deleteLater)
        #self.thread.finished.connect(self.thread.deleteLater)
        self.trender.finished.connect(self.thread.quit)

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

        # Add results layout to main layout
        main_layout.addLayout(results_layout)

        # Set central widget
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # Connect read button to read_tag function
        self.read_button.clicked.connect(
            lambda: read_tag(
                self.ip_input.text(),
                self.tag_input.text(),
                self.results,
                store_to_yaml=self.yaml_enabled.isChecked(),
                yaml_file=self.yaml_file.text(),
                plc=plc
            ) if self.yaml_file.text() != '' else read_tag(
                self.ip_input.text(),
                self.tag_input.text(),
                self.results,
                store_to_yaml=self.yaml_enabled.isChecked(),
                plc=plc
            )
        )
        

        # Connect write button to write_tag function
        self.write_button.clicked.connect(
            lambda: write_tag(
                self.ip_input.text(),
                self.tag_input.text(),
                self.write_value.text(),
                self.results,
                yaml_enabled=self.yaml_enabled.isChecked(),
                yaml_file=self.yaml_file.text(),
                plc=plc
            ) if self.yaml_file.text() != '' else write_tag(
                    self.ip_input.text(),
                    self.tag_input.text(),
                    self.write_value.text(),
                    self.results,
                    yaml_enabled=self.yaml_enabled.isChecked(),
                    plc=plc
            )
        )

        self.trend_button.clicked.connect(self.trender_thread)

        # Load stored data if available
        try:
            f = open('plc_readwrite.pckl', 'rb')
            data_stored = pickle.load(f)
            f.close()
            self.ip_input.setText(str(data_stored[0]))
            self.tag_input.setText(str(data_stored[1]))
        except FileNotFoundError:
            pass

    def print_resuts(self, results):
        self.results.appendPlainText(results)

    def trender_thread(self):
        if self.trender.running:
            self.trender.stop()
            self.trend_button.setText("Start Trend")
        else:
            if not self.thread.isRunning():
                self.trender.ip = self.ip_input.text()
                self.trender.tags = self.tag_input.text()
                self.trender.interval = self.trend_rate.value()
                self.trender.plc = plc
                self.trender.running = True
                self.thread.start()
                self.trend_button.setText("Stop Trend")

app = QApplication(sys.argv)
qdarktheme.setup_theme()
window = MainWindow()
window.show()

app.exec_()