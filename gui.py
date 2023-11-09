import sys
from pycomm3 import LogixDriver
import qdarktheme
from PySide2.QtCore import Qt, QThread, Signal, QObject, QTimer
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
import matplotlib.pyplot as plt

tag_types = None
plc = None

def connect_to_plc(ip, connect_button, main_window):
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
        main_window.stop_plc_connection_check()
    else:
        plc_instance = LogixDriver(ip)
        plc_instance.open()

        if plc_instance.connected:
            tag_types = get_tags_from_yaml(ip, plc=plc_instance)

            connect_button.setText("Disconnect")

        plc = plc_instance

        main_window.start_plc_connection_check()


def check_plc_connection(plc, main_window):
    if plc != None:
        if plc.connected:
            try:
                plc.get_plc_name()
                return True
            except:
                main_window.stop_plc_connection_check()
                return False

    main_window.stop_plc_connection_check()
    return False
                


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


def plot_trend_data(tag, results, timestamps, single_tag):

    if single_tag:
        # ensure tag is an elementary data type
        if type(results[0]) != dict:
            fig, ax = plt.subplots(facecolor=(.18, .31, .31))
            plot, = ax.plot(timestamps, results, 'wo', markersize=2)
            ax.set_xlabel('Time (msec)', color='w')
            ax.set_ylabel('Value', color='w')
            ax.set_title(f'{tag} Trend Results', color='w')
            ax.tick_params(labelcolor='w', labelsize='medium', width=3)
            ax.set_facecolor('k')
            ax.grid()

            min_val = min(results)
            max_val = max(results)

            range_val = max_val - min_val

            spacing_val = range_val/30

            ax.set_ylim(min_val - spacing_val, max_val + spacing_val)

            plt.show()
        else:
            print('\n****** Can only plot elementary data types ******\n')
    else:
        print('\n****** Cannot plot multiple tags yet ******\n')

def process_trend_data(tag, results, timestamps, single_tag, yaml_enabled, yaml_file):
    if yaml_enabled:
        if yaml_file == '':
            yaml_file = f'{tag}_trend_results.yaml'

        if type(results[0]) == dict:
            # get keys from first dict in list
            keys = ['Trend Duration']
            keys = keys + [key for key in results[0].keys()]
        else:
            keys = ['Trend Duration', 'Value']

        with open(yaml_file, 'w') as f:

            yaml_data = []

            if single_tag:
                for i, val in enumerate(results):
                    data = {}

                    td = timestamps[i]
                    data['Trend Duration'] = td
                    data[tag.strip()] = val

                    yaml_data.append(data)
            else:
                formatted_tag = [t.strip() for t in tag.split(',')]

                # loop through the length of the trend results
                for i in range(len(results[0])):
                    data = {}
                    td = timestamps[i]
                    data['Trend Duration'] = td

                    for y in range(len(results)):
                            data[formatted_tag[y]] = results[y][i]

                    yaml_data.append(data)                             

            yaml.safe_dump(yaml_data, f, default_flow_style=False)

class Trender(QObject):
    update = Signal(str)
    update_trend_data = Signal(list, list)
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

        self.results = []
        self.timestamps = []

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

        self.update.emit('Starting Trend...')

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

                self.update_trend_data.emit(self.results, self.timestamps)
            except Exception as e:
                print(f"Error in Trender: {e}")
            
            QThread.msleep(self.interval)
    
    def stop(self):
        self.running = False
        self.finished.emit()

class Monitorer(QObject):
    update = Signal(str)
    update_trend_data = Signal(list, list)
    finished = Signal()

    def __init__(self):
        super(Monitorer, self).__init__()
        self.tags_to_read_write = None
        self.values_to_write = None
        self.read_selected = False
        self.write_selected = False
        self.hold = False
        self.first_event = True
        self.previous_timestamp = None
        self.yaml_data = []
        self.running = False
        self.ip = None
        self.value = None
        self.tag = None
        self.interval = 1
        self.results = []
        self.timestamps = []
        self.first_pass = True
        self.single_tag = True
        self.plc = None
        self.read_write_tag_list = None

    def run(self):
        start_time = datetime.datetime.now()

        self.results = []
        self.timestamps = []

        if self.tags_to_read_write != None:
            self.read_write_tag_list = [t.strip() for t in self.tags_to_read_write.split(',')]
            
        try:
            if plc == None:
                self.plc = LogixDriver(self.ip)
                self.plc.open()
            else:
                self.plc = plc
        except Exception as e:
            print(f"Error in Monitorer: {e}")

        self.update.emit('Starting Monitor...')

        while self.running:

            try:
                result = self.plc.read(self.tag)

                if result.value == self.value and self.hold == False:

                    yaml_temp = {}
                    self.hold = True
                    timestamp = datetime.datetime.now().strftime("%I:%M:%S:%f %p")
                    now = datetime.datetime.now()

                    self.update.emit(f'\nTag = {self.value} at Timestamp: {timestamp}')

                    yaml_temp['Timestamp'] = timestamp

                    if self.first_event:
                        self.previous_timestamp = now
                        self.first_event = False
                    else:
                        time_since_last_event = (now - self.previous_timestamp).total_seconds() * 1000
                        self.update.emit(f'Time since last event: {time_since_last_event} ms')
                        self.previous_timestamp = now

                        yaml_temp['Time Since Last Event'] = time_since_last_event

                    if self.read_write_tag_list != None and self.read_selected:
                        read_event_results = plc.read(*self.read_write_tag_list)

                        # if there were muliple tags in the read event
                        if type(read_event_results) is list:
                            for i, tag_result in enumerate(read_event_results):
                                yaml_temp[self.read_write_tag_list[i]] = tag_result.value
                                self.update.emit(f'{self.read_write_tag_list[i]} = {tag_result.value}')
                        else:
                            yaml_temp[self.read_write_tag_list[0]] = read_event_results.value
                            self.update.emit(f'{self.read_write_tag_list[0]} = {read_event_results.value}')

                    elif self.read_write_tag_list != None and self.write_selected:

                        tag_write_data = []

                        for i, value in enumerate([t.strip() for t in self.values_to_write.split(',')]):
                            tag_write_data.append((self.read_write_tag_list[i], set_data_type(value, self.tags_to_read_write[i])))
                            
                        plc.write(*tag_write_data)
                        self.update.emit(f'Successfully wrote to tags: {self.tags_to_read_write}')
                        
                    self.yaml_data.append(yaml_temp)
                
                if result.value != self.value:
                    self.hold = False
                    
            except Exception as e:
                print(f"Error in monitorer: {e}")
            
            QThread.msleep(self.interval)
    
    def stop(self):
        self.running = False
        self.finished.emit()


class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("PLC Read/Write")

        self.plc_connection_check_timer = QTimer()
        self.plc_connection_check_timer.timeout.connect(lambda: check_plc_connection(plc, self))

        self.trender = Trender()
        self.monitorer = Monitorer()
        self.trend_thread = QThread()
        self.monitor_thread = QThread()
        self.trender.moveToThread(self.trend_thread)
        self.trend_thread.started.connect(self.trender.run)
        self.trender.update.connect(self.print_resuts)
        #self.trender.finished.connect(self.trender.deleteLater)
        #self.thread.finished.connect(self.thread.deleteLater)
        self.trender.finished.connect(self.trend_thread.quit)

        self.monitorer.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitorer.run)
        self.monitorer.finished.connect(self.monitor_thread.quit)
        self.monitorer.update.connect(self.print_resuts)
        self.trender_results = []
        self.trender_timestamps = []

        self.trender.update_trend_data.connect(self.update_trend_data)

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

        trend_tab.setLayout(trend_tab_layout)

        tabs.addTab(trend_tab, "Trend")

        # Create write tab widgets
        monitor_tab = QWidget()
        self.monitor_button = QPushButton("Start Monitor")
        self.monitor_value = QLineEdit()
        self.monitor_rate = QDoubleSpinBox()
        self.enable_event = QCheckBox("Enable Read/Write On Event")
        self.read_selected_radio  = QRadioButton("Read On Event")
        self.write_selected_radio  = QRadioButton("Write On Event")
        self.monitor_read_write_tags = QLineEdit()
        self.monitor_read_write_tags.setPlaceholderText("Tags to Read/Write On Event")
        self.monitor_read_write_values = QLineEdit()
        self.monitor_read_write_values.setPlaceholderText("Values to Write On Event")

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
        monitor_tab_layout.addWidget(self.monitor_read_write_tags)
        monitor_tab_layout.addWidget(self.monitor_read_write_values)

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

        self.connect_button.clicked.connect(lambda: connect_to_plc(self.ip_input.text(), self.connect_button, self))

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
        self.trend_plot_button.clicked.connect(lambda: plot_trend_data(self.trender.tags, self.trender_results, self.trender_timestamps, self.trender.single_tag))

        self.monitor_button.clicked.connect(self.monitorer_thread)
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

    def update_trend_data(self, results, timestamps):
        self.trender_results = results
        self.trender_timestamps = timestamps

    def trender_thread(self):
        if self.trender.running:
            process_trend_data(self.trender.tags, self.trender.results, self.trender.timestamps, self.trender.single_tag, self.yaml_enabled.isChecked(), self.yaml_file.text())
            self.trender.stop()
            self.trend_button.setText("Start Trend")
        else:
            if not self.trend_thread.isRunning():
                self.trender.ip = self.ip_input.text()
                self.trender.tags = self.tag_input.text()
                self.trender.interval = (self.trend_rate.value() * 1000)
                self.trender.plc = plc
                self.trender.running = True
                self.trend_thread.start()
                self.trend_button.setText("Stop Trend")

    def monitorer_thread(self):
        if self.monitorer.running:
            self.monitorer.stop()
            self.monitor_button.setText("Start Monitor")
        else:
            if not self.monitor_thread.isRunning():
                self.monitorer.ip = self.ip_input.text()
                self.monitorer.tags_to_read_write = self.monitor_read_write_tags.text()
                self.monitorer.values_to_write = self.monitor_read_write_values.text()
                self.monitorer.read_selected = self.read_selected_radio.isChecked()
                self.monitorer.write_selected = self.write_selected_radio.isChecked()
                self.monitorer.tag = self.tag_input.text()
                self.monitorer.value = set_data_type(self.monitor_value.text(), self.tag_input.text())
                self.monitorer.interval = (self.monitor_rate.value() * 1000)
                self.monitorer.plc = plc
                self.monitorer.running = True
                self.monitor_thread.start()
                self.monitor_button.setText("Stop Monitor")
    
    def start_plc_connection_check(self):
        self.plc_connection_check_timer.start(5000)

    def stop_plc_connection_check(self):
        self.plc_connection_check_timer.stop()
        self.results.appendPlainText('PLC Connection Lost')
        self.connect_button.setText("Connect")


app = QApplication(sys.argv)
qdarktheme.setup_theme()
window = MainWindow()
window.show()

app.exec_()