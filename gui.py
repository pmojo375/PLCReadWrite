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
    QMenuBar,
    QLabel,
    QAction,
    QToolBar,
    QAction,
    QStatusBar,
    QMessageBox,
    QComboBox,
)
from PySide2 import QtGui
import yaml
import pickle
import re
import datetime
import matplotlib.pyplot as plt
import csv

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
        main_window.disable_buttons()
    else:
        plc_instance = LogixDriver(ip)
        plc_instance.open()

        if plc_instance.connected:
            tag_types = get_tags_from_yaml(ip, plc=plc_instance)

            connect_button.setText("Disconnect")

        plc = plc_instance

        main_window.start_plc_connection_check()
        main_window.enable_buttons()
        main_window.showConnectedDialog()


def check_plc_connection(plc, main_window):
    """
    Check if the PLC is connected and return True if it is, False otherwise.

    Args:
        plc (PLC): The PLC object to check connection for.
        main_window (MainWindow): The main window object.

    Returns:
        bool: True if the PLC is connected, False otherwise.
    """
    if plc != None:
        if plc.connected:
            try:
                plc.get_plc_name()
                return True
            except:
                main_window.stop_plc_connection_check()
                return False
        else:
            main_window.stop_plc_connection_check()
            return False
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

        data = data_to_dict(data)

        yaml.safe_dump(data, f, default_flow_style=False)

def data_to_dict(data):

    processed_data = []

    if isinstance(data, list):
        for tag in data:
            if isinstance(tag.value, list):
                for i, value in enumerate(tag.value):
                    processed_data.append({f'{tag.tag}[{str(i)}]': value})
            else:
                processed_data.append({tag.tag: tag.value})
    else:
        processed_data.append({tag.tag: tag.value})    

    return processed_data

def deserialize_from_yaml(yaml_name):
    """
    Deserialize data from a YAML file and return a list of dictionaries containing tag-value pairs.
    
    Args:
    - yaml_name (str): The name of the YAML file to deserialize.
    
    Returns:
    - tag_values (list of dict): A list of dictionaries containing tag-value pairs.
    """
    with open(yaml_name, 'r') as f:
        yaml_data = yaml.safe_load(f)
        tag_values = []
        for item in yaml_data:
            for key, value in item.items():
                tag_values.append({'tag': key, 'value': value})
    
    return tag_values


def iterate_value(name, value, ret):
    """
    Recursively iterates through a nested dictionary or list and returns a list of tuples containing the name and value of each leaf node.

    Args:
        name (str): The name of the current node.
        value (dict or list): The value of the current node.
        ret (list): The list to append the name-value tuples to.

    Returns:
        list: A list of tuples containing the name and value of each leaf node.
    """
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
    """
    Processes YAML data and returns a list of processed data.

    Args:
        data (list): A list of YAML tags, where each tag is a dictionary with 'tag' and 'value' keys.

    Returns:
        list: A list of processed data.
    """

    processed_data = []

    for tag in data:
        tag_name = tag['tag']
        tag_value  = tag['value']

        processed_data = iterate_value(tag_name, tag_value, processed_data)

    return processed_data


def process_csv_read(csv_file):
    """
    Processes CSV data and returns a list of processed data.

    Args:
        csv_file (str): The name of the CSV file to process.

    Returns:
        list: A list of processed data.
    """
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        processed_data = []
        for row in reader:
            processed_data.append((row['tag'], set_data_type(row['value'], row['tag'])))
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


def read_tag(ip, tags, result_window, plc, **kwargs):
    """
    Reads the values of the given tags from the PLC with the given IP address and displays the results in the given result window.

    Args:
        ip (str): The IP address of the PLC to read from.
        tags (list): A list of tag names to read from the PLC.
        result_window (QPlainTextEdit): The window to display the results in.
        plc (LogixDriver): An optional pre-initialized LogixDriver instance to use for reading the tags.
        **kwargs: Additional keyword arguments.
            store_to_yaml (bool): Whether to store the results in a YAML file. Default is False.
            yaml_file (str): The name of the YAML file to store the results in. Default is 'tag_values.yaml'.

    Returns:
        list: A list of dictionaries containing the tag names and their corresponding values.
    """

    save_history(ip, tags)

    tags = [t.strip() for t in tags.split(',')]
        
    store_to_file = kwargs.get('store_to_file', False)
    file_selection = kwargs.get('file_selection', 0)

    if file_selection == 0:
        file_name = kwargs.get('file_name', 'tag_values.yaml')
    elif file_selection == 1:
        file_name = kwargs.get('file_name', 'tag_values.csv')

    return_data = []

    try:
        ret = plc.read(*tags)

        if store_to_file:
            if not isinstance(ret, list):
                ret = [ret]
            
            if file_selection == 0:
                serialize_to_yaml(ret, yaml_file=file_name)
            elif file_selection == 1:
                data = data_to_dict(ret)
                data = [flatten_dict(item) for item in data]
                write_to_csv(data, file_name)

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


def write_tag(ip, tags, values, results, plc, **kwargs):
    """
    Writes a value to a tag in a PLC.

    Args:
        ip (str): The IP address of the PLC.
        tag (str): The tag to write to.
        value (any): The value to write to the tag.
        plc (LogixDriver): An existing LogixDriver instance to use instead of creating a new one.

    Returns:
        bool: True if the write was successful, False otherwise.
    """

    save_history(ip, tags)

    file_enabled = kwargs.get('file_enabled', False)
    file_selection = kwargs.get('file_selection', 0)
    if file_selection == 0:
        file_name = kwargs.get('file_name', 'tag_values.yaml')
    elif file_selection == 1:
        file_name = kwargs.get('file_name', 'tag_values.csv')

    tags = [t.strip() for t in tags.split(',')]

    if not file_enabled:
        values = [t.strip() for t in values.split(',')]

        write_data = []

        for i, tag in enumerate(tags):
            write_data.append((tag, set_data_type(values[i], tag)))

        try:
            if plc.write(*write_data):
                results.appendPlainText(f"Successfully wrote to tags to PLC")
        except Exception as e:
            print(f"Error in write_tag: {e}")
            return None
    else:
        if file_selection == 0:
            tags = process_yaml_read(deserialize_from_yaml(file_name))
        elif file_selection == 1:
            tags = process_csv_read(file_name)

        try:
            if plc.write(*tags):
                results.appendPlainText(f"Successfully wrote to tags to PLC")
        except Exception as e:
            print(f"Error in write_tag: {e}")
            return None


def save_history(ip, tag):
    """
    Saves the IP address and tag to a file named 'plc_readwrite.pckl' using pickle.

    Args:
        ip (str): The IP address to be saved.
        tag (str): The tag to be saved.

    Returns:
        None
    """
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
    """
    Process trend data and write it to a YAML file if enabled.

    Args:
        tag (str): The tag name.
        results (list): The list of trend results.
        timestamps (list): The list of timestamps.
        single_tag (bool): Whether the tag is a single tag or a list of tags.
        yaml_enabled (bool): Whether to write the trend data to a YAML file.
        yaml_file (str): The YAML file to write the trend data to.

    Returns:
        None
    """
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


def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))
    return dict(items)


def yaml_to_csv(yaml_file, csv_file):
    with open(yaml_file, 'r') as jf:
        data = yaml.safe_load(jf)

    flattened_data = [flatten_dict(item) for item in data]

    write_to_csv(flattened_data, csv_file)


def write_to_csv(data, csv_file):
    with open(csv_file, 'w', newline='') as cf:
        writer = csv.DictWriter(cf, fieldnames=['tag', 'value'])
        writer.writeheader()
        for item in data:
            for tag, value in item.items():
                writer.writerow({'tag': tag, 'value': value})

class Trender(QObject):
    """
    A class to read and update PLC tags and emit signals for GUI updates.

    Attributes:
    -----------
    update : Signal
        A signal to update the GUI with a message.
    update_trend_data : Signal
        A signal to update the GUI with the trend data.
    finished : Signal
        A signal to indicate that the thread has finished.

    Methods:
    --------
    run()
        A method to start the thread and read PLC tags.
    stop()
        A method to stop the thread.
    """

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
        """
        A method to start the thread and read PLC tags.
        """
        start_time = datetime.datetime.now()

        self.results = []
        self.timestamps = []

        # Convert tag input to a list
        formatted_tags = [t.strip() for t in self.tags.split(',')]

        try:
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
        """
        A method to stop the thread.
        """
        self.running = False
        self.finished.emit()

class Monitorer(QObject):
    """
    A class for monitoring PLC tags and writing to them.

    Attributes:
    - update (Signal): a signal for updating the GUI with messages
    - update_trend_data (Signal): a signal for updating the GUI with trend data
    - finished (Signal): a signal for indicating that the monitoring has finished
    - tags_to_read_write (str): a comma-separated string of tags to read or write to
    - values_to_write (str): a comma-separated string of values to write to the tags
    - read_selected (bool): a flag indicating whether read is selected
    - write_selected (bool): a flag indicating whether write is selected
    - hold (bool): a flag indicating whether the tag value is being held
    - first_event (bool): a flag indicating whether this is the first event
    - previous_timestamp (datetime): the timestamp of the previous event
    - yaml_data (list): a list of YAML data
    - running (bool): a flag indicating whether the monitoring is running
    - ip (str): the IP address of the PLC
    - value (str): the value of the tag being monitored
    - tag (str): the name of the tag being monitored
    - interval (int): the interval between reads in milliseconds
    - first_pass (bool): a flag indicating whether this is the first pass
    - single_tag (bool): a flag indicating whether only one tag is being monitored
    - plc (LogixDriver): a driver for communicating with the PLC
    - read_write_tag_list (list): a list of tags to read or write to
    """

    update = Signal(str)
    update_trend_data = Signal(list, list)
    finished = Signal()

    def __init__(self):
        """
        Initializes a new Monitorer object.
        """
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
        self.first_pass = True
        self.single_tag = True
        self.plc = None
        self.read_write_tag_list = None

    def run(self):
        """
        Runs the monitoring process.
        """

        self.first_event = True
        self.hold == False
        self.yaml_data = []

        if self.tags_to_read_write != None:
            self.read_write_tag_list = [t.strip() for t in self.tags_to_read_write.split(',')]

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
                            
                        self.plc.write(*tag_write_data)
                        self.update.emit(f'Successfully wrote to tags: {self.tags_to_read_write}')
                        
                    self.yaml_data.append(yaml_temp)
                
                if result.value != self.value:
                    self.hold = False
                    
            except Exception as e:
                print(f"Error in monitorer: {e}")
            
            QThread.msleep(self.interval)
    
    def stop(self):
        """
        Stops the monitoring process.
        """
        self.running = False
        self.finished.emit()



class AboutWindow(QWidget):
    """
    This "window" is a QWidget. If it has no parent, it
    will appear as a free-floating window as we want.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        layout = QVBoxLayout()
        self.name_label = QLabel("PLC Tag Utility")
        self.version_label = QLabel("Version 1.0")
        self.author_label = QLabel("Created by: Parker Mojsiejenko")
        self.description_label = QLabel("This project is a utility for reading and writing tags from Allen-Bradley PLCs. It can read and write from YAML files as well a convert the read file to CSV if desired. In addition to that it can trend tags and monitor tags for changes and write to them when they change.")
        self.description_label.setWordWrap(True)
        self.about_label = QLabel("This project relies on the pycomm3 library made by ottowayi for communicating with Allen-Bradley PLCs.")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.version_label.setAlignment(Qt.AlignCenter)
        self.author_label.setAlignment(Qt.AlignCenter)
        self.about_label.setAlignment(Qt.AlignCenter)
        self.description_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QtGui.QFont("Arial", 20))
        layout.addWidget(self.name_label)
        layout.addWidget(self.version_label)
        layout.addWidget(self.author_label)
        layout.addWidget(self.about_label)
        layout.addWidget(self.description_label)
        self.setLayout(layout)


class MainWindow(QMainWindow):
    def show_about_window(self):
        if self.w is None:
            self.w = AboutWindow()
        self.w.show()

    def showConnectedDialog(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("PLC Connected succesfully!")
        msgBox.setWindowTitle("PLC Connected")
        msgBox.setStandardButtons(QMessageBox.Ok)

        returnValue = msgBox.exec()

    def __init__(self):
        super(MainWindow, self).__init__()

        self.w = None
        self.setWindowTitle("PLC Read/Write")

        menubar = self.menuBar()
        menubar.addAction("About")
        menubar.show()

        # open AboutWindow when About is clicked
        menubar.triggered.connect(self.show_about_window)

        # Create timer for checking PLC connection
        self.plc_connection_check_timer = QTimer()
        self.plc_connection_check_timer.timeout.connect(lambda: check_plc_connection(plc, self))

        # Trender thread and signals
        self.trender = Trender()
        self.trend_thread = QThread()
        self.trender.moveToThread(self.trend_thread)
        self.trend_thread.started.connect(self.trender.run)
        self.trender.update.connect(self.print_resuts)
        self.trender.finished.connect(self.trend_thread.quit)
        self.trender.update_trend_data.connect(self.update_trend_data)
        self.trender_results = []
        self.trender_timestamps = []

        # Monitorer thread and signals
        self.monitorer = Monitorer()
        self.monitor_thread = QThread()
        self.monitorer.moveToThread(self.monitor_thread)
        self.monitor_thread.started.connect(self.monitorer.run)
        self.monitorer.finished.connect(self.monitor_thread.quit)
        self.monitorer.update.connect(self.print_resuts)

        # Create layouts
        main_layout = QHBoxLayout()
        entry_layout = QVBoxLayout()
        results_layout = QVBoxLayout()
        ip_layout = QHBoxLayout()
        read_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        write_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        trend_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        monitor_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        self.monitor_radio_layout = QHBoxLayout()
        file_layout = QHBoxLayout()
        selection_layout = QHBoxLayout()

        # Create tab widget
        tabs = QTabWidget()
        self.read_tab = QWidget()
        write_tab = QWidget()
        trend_tab = QWidget()
        monitor_tab = QWidget()
        tabs.setTabPosition(QTabWidget.North)

        # --------------------------------------------#
        #                   READ TAB                  #
        # --------------------------------------------#

        # Create widgets
        self.read_button = QPushButton("Read")

        # Set parameters
        self.read_button.setDisabled(True)

        # Add to layouts
        read_tab_layout.addWidget(self.read_button)

        
        # --------------------------------------------#
        #                  WRITE TAB                  #
        # --------------------------------------------#

        # Create widgets
        self.write_button = QPushButton("Write")
        self.write_value = QLineEdit()

        # Set parameters
        self.write_value.setPlaceholderText("Value")
        self.write_button.setDisabled(True)

        # Add to layouts
        write_tab_layout.addWidget(self.write_value)
        write_tab_layout.addWidget(self.write_button)


        # --------------------------------------------#
        #                  TREND TAB                  #
        # --------------------------------------------#

        # Create widgets
        self.trend_button = QPushButton("Start Trend")
        self.trend_plot_button = QPushButton("Show Trend Plot")
        self.trend_rate = QDoubleSpinBox()

        # Set parameters
        self.trend_rate.setRange(0.1, 60)
        self.trend_rate.setValue(1)
        self.trend_rate.setSuffix(" seconds between reads")
        self.trend_rate.setSingleStep(0.1)
        self.trend_button.setDisabled(True)

        # Add to layouts
        trend_tab_layout.addWidget(self.trend_rate)
        trend_tab_layout.addWidget(self.trend_button)
        trend_tab_layout.addWidget(self.trend_plot_button)

        # Add tabs to tab widget
        tabs.addTab(self.read_tab, "Read")
        tabs.addTab(write_tab, "Write")
        tabs.addTab(trend_tab, "Trend")
        tabs.addTab(monitor_tab, "Monitor")

        # --------------------------------------------#
        #                 MONITOR TAB                 #
        # --------------------------------------------#

        # Create widgets
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

        # Set parameters
        self.monitor_rate.setRange(0.1, 60)
        self.monitor_rate.setValue(1)
        self.monitor_rate.setSuffix(" seconds between reads")
        self.monitor_rate.setSingleStep(0.1)
        self.monitor_value.setPlaceholderText("Value to Monitor")
        self.monitor_button.setDisabled(True)

        # Add to layouts
        self.monitor_radio_layout.addWidget(self.read_selected_radio)
        self.monitor_radio_layout.addWidget(self.write_selected_radio)
        monitor_tab_layout.addWidget(self.monitor_value)
        monitor_tab_layout.addWidget(self.monitor_rate)
        monitor_tab_layout.addWidget(self.enable_event)
        monitor_tab_layout.addLayout(self.monitor_radio_layout)
        monitor_tab_layout.addWidget(self.monitor_button)
        monitor_tab_layout.addWidget(self.monitor_read_write_tags)
        monitor_tab_layout.addWidget(self.monitor_read_write_values)

        # Set tab layouts
        self.read_tab.setLayout(read_tab_layout)
        write_tab.setLayout(write_tab_layout)
        trend_tab.setLayout(trend_tab_layout)
        monitor_tab.setLayout(monitor_tab_layout)

        # Create main layout widgets
        self.ip_input = QLineEdit()
        self.tag_input = QLineEdit()
        self.file_enabled = QCheckBox("Read/Write To File")
        self.file_name = QLineEdit()
        self.file_browser = QPushButton("Browse")
        self.connect_button = QPushButton("Connect")
        self.results = QPlainTextEdit()
        self.file_format_selection = QComboBox()
        self.file_format = 0

        # Set parameters
        self.tag_input.setPlaceholderText("Tag")
        self.ip_input.setMaxLength(15)
        self.ip_input.setPlaceholderText("IP Address")
        self.results.setReadOnly(True)
        self.file_format_selection.addItems(["YAML", "CSV"])
        self.file_format_selection.currentIndexChanged.connect(self.file_format_changed)

        # Add to layouts
        ip_layout.addWidget(self.ip_input)
        ip_layout.addWidget(self.connect_button)
        entry_layout.addLayout(ip_layout)
        file_layout.addWidget(self.file_name)
        file_layout.addWidget(self.file_browser)
        selection_layout.addWidget(self.file_enabled)
        selection_layout.addWidget(self.file_format_selection)
        entry_layout.addWidget(self.tag_input)
        entry_layout.addLayout(selection_layout)
        entry_layout.addLayout(file_layout)
        entry_layout.addWidget(tabs)
        results_layout.addWidget(self.results)

        # Add to main layout
        main_layout.addLayout(entry_layout)
        main_layout.addLayout(results_layout)

        # Set central widget
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # --------------------------------------------#
        #               CONNECT EVENTS                #
        # --------------------------------------------#

        # Connect read button to read_tag function
        self.read_button.clicked.connect(self.read_tag_button_clicked)
        
        self.write_button.clicked.connect(self.write_tag_button_clicked)

        self.trend_button.clicked.connect(self.trender_thread)
        self.trend_plot_button.clicked.connect(lambda: plot_trend_data(self.trender.tags, self.trender_results, self.trender_timestamps, self.trender.single_tag))
        self.monitor_button.clicked.connect(self.monitorer_thread)
        self.connect_button.clicked.connect(lambda: connect_to_plc(self.ip_input.text(), self.connect_button, self))
        self.file_browser.clicked.connect(lambda: self.file_name.setText(QFileDialog.getOpenFileName()[0]))

        # Load stored data if available
        try:
            f = open('plc_readwrite.pckl', 'rb')
            data_stored = pickle.load(f)
            f.close()
            self.ip_input.setText(str(data_stored[0]))
            self.tag_input.setText(str(data_stored[1]))
        except FileNotFoundError:
            pass

    def file_format_changed(self, i):
        self.file_format = i
        print(i)

    def showNotConnectedDialog(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Please Connect to PLC.")
        msgBox.setWindowTitle("PLC Not Connected")
        msgBox.setStandardButtons(QMessageBox.Ok)

        returnValue = msgBox.exec()


    def showLostConnectionDialog(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("PLC Lost Connection, please reconnect.")
        msgBox.setWindowTitle("PLC Lost Connection")
        msgBox.setStandardButtons(QMessageBox.Ok)

        returnValue = msgBox.exec()

    
    def enable_buttons(self):
        self.trend_button.setDisabled(False)
        self.read_button.setDisabled(False)
        self.write_button.setDisabled(False)
        self.monitor_button.setDisabled(False)

    
    def disable_buttons(self):
        self.trend_button.setDisabled(True)
        self.read_button.setDisabled(True)
        self.write_button.setDisabled(True)
        self.monitor_button.setDisabled(True)


    def read_tag_button_clicked(self):
        if check_plc_connection(plc, self):
            if self.file_name.text() != '':
                read_tag(self.ip_input.text(), self.tag_input.text(), self.results, plc, store_to_file=self.file_enabled.isChecked(), file_name=self.file_name.text(), file_selection = self.file_format)
            else:
                read_tag(self.ip_input.text(), self.tag_input.text(), self.results, plc, store_to_file=self.file_enabled.isChecked(), file_selection = self.file_format)
        else:
            self.showNotConnectedDialog()


    def write_tag_button_clicked(self):
        if check_plc_connection(plc, self):
            if self.file_name.text() != '':
                write_tag(self.ip_input.text(), self.tag_input.text(), self.write_value.text(), self.results, plc, file_enabled=self.file_enabled.isChecked(), file_name=self.file_file.text(), file_selection = self.file_format)
            else:
                write_tag(self.ip_input.text(), self.tag_input.text(), self.write_value.text(), self.results, plc, file_enabled=self.file_enabled.isChecked(), file_selection = self.file_format)
        else:
            self.showNotConnectedDialog()

    def print_resuts(self, results):
        self.results.appendPlainText(results)

    def update_trend_data(self, results, timestamps):
        self.trender_results = results
        self.trender_timestamps = timestamps

    def trender_thread(self):
        if self.trender.running:
            process_trend_data(self.trender.tags, self.trender.results, self.trender.timestamps, self.trender.single_tag, self.file_enabled.isChecked(), self.file_name.text())
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
        self.connect_button.setText("Connect")


app = QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon('icon.ico'))
qdarktheme.setup_theme()
window = MainWindow()
window.show()

app.exec_()