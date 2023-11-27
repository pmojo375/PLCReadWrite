import sys
from pycomm3 import LogixDriver
#from offline_read import LogixDriver
import qdarktheme
from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer, QRegularExpression, QSettings
from PySide6.QtWidgets import (
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
    QTextEdit,
    QLabel,
    QMessageBox,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QListView,
    QButtonGroup,
    QTreeWidget,
    QTreeWidgetItem,
)
from PySide6 import QtGui
from PySide6.QtGui import QRegularExpressionValidator, QTextCursor
import yaml
import re
import datetime
import matplotlib.pyplot as plt
import csv

tag_types = None
tag_dimensions = None
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
        plc = LogixDriver(ip)
        plc.open()

        if plc.connected:
            tag_types = get_tags_from_plc(plc)
            connect_button.setText("Disconnect")

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
        processed_data.append({data.tag: data.value})

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
            iterate_value(f'{name}.{key}', value, ret)
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
        tag_value = tag['value']

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
            processed_data.append(
                (row['tag'], set_data_type(row['value'], row['tag'])))
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


def read_tag(tag_names, plc, result_window, **kwargs):
    """
    Reads the values of the given tags from the PLC with the given IP address and displays the results in the given result window.

    Args:
        ip_address (str): The IP address of the PLC to read from.
        tag_names (list): A list of tag names to read from the PLC.
        plc (LogixDriver): An optional pre-initialized LogixDriver instance to use for reading the tags.
        result_window (QPlainTextEdit): The window to display the results in.
        **kwargs: Additional keyword arguments.
            store_to_yaml (bool): Whether to store the results in a YAML file. Default is False.
            yaml_file (str): The name of the YAML file to store the results in. Default is 'tag_values.yaml'.

    Returns:
        list: A list of dictionaries containing the tag names and their corresponding values.
    """

    # split tag name(s) into a list
    tag_names = [name.strip() for name in tag_names.split(',')]

    store_to_file = kwargs.get('store_to_file', False)
    file_selection = kwargs.get('file_selection', 0)

    if file_selection == 0:
        file_name = kwargs.get('file_name', 'tag_values.yaml')
    elif file_selection == 1:
        file_name = kwargs.get('file_name', 'tag_values.csv')

    tag_data = []

    try:
        if len(tag_names) == 1:
            result_window.print_results(f'Reading Tag: {tag_names[0]}<br>')
        else:
            result_window.print_results(f'Reading Tags: {", " .join(tag_names)}<br>')
        
        # get the tag data from the PLC
        read_result = plc.read(*tag_names)

        # Loop through each tag in the list
        if len(tag_names) == 1:
            if read_result.error is None:
                entry_tag = tag_names[0]
                value = read_result.value
                tag_data.append(crawl_and_format(value, entry_tag, {}))
                if isinstance(value, list):
                    for i, v in enumerate(value):
                        result_window.add_to_tree(
                            {f'{read_result.tag}[{i}]': v}, result_window.tree.invisibleRootItem())
                else:
                    result_window.add_to_tree(
                        {read_result.tag: value}, result_window.tree.invisibleRootItem())
            else:
                result_window.print_results(f"Error: {read_result.error}")

        else:
            for i, tag in enumerate(tag_names):
                if read_result[i].error is None:
                    entry_tag = tag_names[i]
                    value = read_result[i].value
                    tag_data.append(crawl_and_format(value, entry_tag, {}))
                    if isinstance(value, list):
                        for i, v in enumerate(value):
                            result_window.add_to_tree(
                                {f'{tag_names[i]}[{i}]': v}, result_window.tree.invisibleRootItem())
                    else:
                        result_window.add_to_tree(
                            {tag_names[i]: value}, result_window.tree.invisibleRootItem())
                else:
                    result_window.print_results(f"Error: {read_result[i].error}", 'red')
                    
        if store_to_file:
            if file_selection == 0:
                serialize_to_yaml(read_result, yaml_file=file_name)
            elif file_selection == 1:
                data = data_to_dict(read_result)
                data = [flatten_dict(item) for item in data]
                write_to_csv(data, file_name)
                
            result_window.print_results(f'Successfully wrote to file: {file_name}<br>')

        for result in tag_data:
            for tag, value in result.items():

                pattern = r'\{[^}]*\}'

                tag = re.sub(pattern, '', tag)

                result_window.print_results(f"{tag} = {value}", 'yellow')
                result_window.tag_read_history[tag] = value

        result_window.print_results(f'')
        result_window.add_to_table(result_window.tag_read_history)
    except Exception as e:
        print(f"Error in read_tags: {e}")


def get_tags_from_plc(plc):
    tag_list = {}

    try:
        data = plc.tags_json

        for tag_name, tag_info in data.items():
            tag_data_type = tag_info['data_type']
            tag_dimensions = tag_info.get('dimensions', [0])

            if isinstance(tag_data_type, str):
                tag_list[tag_name] = {
                    'data_type': tag_data_type,
                    'dimensions': tag_dimensions
                }
            elif isinstance(tag_data_type, dict):
                # Store the parent structure
                tag_list[tag_name] = {
                    'data_type': tag_data_type['name'],
                    'dimensions': tag_dimensions,
                    'structure': True
                }
                # Recursively store children
                tag_list = extract_child_data_types(
                    tag_data_type['internal_tags'], tag_list, tag_name, tag_dimensions)

        return tag_list
    except Exception as e:
        print(f"Error in get_tags_from_plc function: {e}")
        return None


def extract_child_data_types(structure, array, name, parent_dimensions):
    for child_name, child_info in structure.items():
        child_data_type = child_info['data_type']
        child_array_length = child_info.get('array', 0)

        if child_name.startswith('_') or child_name.startswith('ZZZZZZZZZZ'):
            continue

        full_tag_name = f'{name}.{child_name}'
        if isinstance(child_data_type, str):
            array[full_tag_name] = {
                'data_type': child_data_type,
                'dimensions': [child_array_length] if child_array_length > 0 else [0]
            }
        elif isinstance(child_data_type, dict):
            # Store the structure itself
            array[full_tag_name] = {
                'data_type': child_data_type['name'],
                'dimensions': parent_dimensions,
                'structure': True
            }
            # Recursively store children
            array = extract_child_data_types(
                child_data_type['internal_tags'], array, full_tag_name, parent_dimensions)

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
            type = tag_types[tag]['data_type']

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


def write_tag(tags, values, main_window, plc, **kwargs):
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
                main_window.print_results(f"Successfully wrote to tags to PLC")
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
                main_window.print_results(f"Successfully wrote to tags to PLC")
        except Exception as e:
            print(f"Error in write_tag: {e}")
            return None


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


def process_trend_data(tag, results, timestamps, single_tag, file_enabled, file_name, file_format):
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
    if file_enabled:
        if file_name == '':
            if file_format == 0:
                file_name = f'{tag}_trend_results.yaml'
            else:
                file_name = f'{tag}_trend_results.csv'

        if type(results[0]) == dict:
            # get keys from first dict in list
            keys = ['Trend Duration']
            keys = keys + [key for key in results[0].keys()]
        else:
            keys = ['Trend Duration', 'Value']

        with open(file_name, 'w') as f:

            if file_format == 0:

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
            else:
                writer = csv.DictWriter(
                    f, fieldnames=keys, lineterminator='\n')
                writer.writeheader()

                if single_tag:
                    for i, val in enumerate(results):
                        writer.writerow(
                            {'Trend Duration': timestamps[i], 'Value': val})
                else:
                    formatted_tag = [t.strip() for t in tag.split(',')]

                    # loop through the length of the trend results
                    for i in range(len(results[0])):
                        data = {}
                        td = timestamps[i]
                        data['Trend Duration'] = td

                        for y in range(len(results)):
                            data[formatted_tag[y]] = results[y][i]

                        writer.writerow(data)


def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep=sep).items())
                else:
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

    update = Signal(str, str)
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
        self.tag_data = []

    def run(self):
        """
        A method to start the thread and read PLC tags.
        """
        start_time = datetime.datetime.now()

        self.first_pass = True
        self.results = []
        self.timestamps = []

        # Convert tag input to a list
        formatted_tags = [t.strip() for t in self.tags.split(',')]

        try:
            self.plc = plc
        except Exception as e:
            print(f"Error in Trender: {e}")

        self.update.emit('Starting Trend...<br>', 'white')

        while self.running:

            self.tag_data = []
            
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
                self.update.emit(
                    f'Timestamp: {datetime.datetime.now().strftime("%I:%M:%S:%f %p")}<br>', 'white')

                if self.single_tag:
                    self.tag_data = crawl_and_format(result[0].value, formatted_tags[0], {})
                    for tag, value in self.tag_data.items():
                        self.update.emit(f'{tag} = {value}', 'yellow')
                    self.results.append(result[0].value)
                    self.update.emit('', 'white')
                else:
                    for i, r in enumerate(result):
                        self.tag_data.append(crawl_and_format(r.value, formatted_tags[i], {}))
                        self.results[i].append(r.value)
                        
                    for result in self.tag_data:
                        for tag, value in result.items():
                            self.update.emit(f'{tag} = {value}', 'yellow')
                    
                    
                    self.update.emit('', 'white')

                self.timestamps.append(
                    (datetime.datetime.now() - start_time).total_seconds() * 1000)

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

    update = Signal(str, str)
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
        self.read_once = True
        self.read_time = None
        self.read_loop_enabled = False

    def run(self):
        """
        Runs the monitoring process.
        """

        self.first_event = True
        self.hold == False
        self.yaml_data = []
        self.read_loop_enabled = False

        if self.tags_to_read_write != None:
            self.read_write_tag_list = [
                t.strip() for t in self.tags_to_read_write.split(',')]

        self.update.emit('Starting Monitor...<br>', 'white')

        while self.running:

            if self.read_loop_enabled:
                self.read_time_timestamp = datetime.datetime.now()

                read_total_time = (self.read_time_timestamp -
                                   self.read_time_timestamp_start).total_seconds()

                if read_total_time <= self.read_time:
                    try:
                        read_event_results = plc.read(
                            *self.read_write_tag_list)

                        # if there were muliple tags in the read event
                        if type(read_event_results) is list:
                            for i, tag_result in enumerate(read_event_results):
                                yaml_temp[self.read_write_tag_list[i]
                                          ] = tag_result.value
                                self.update.emit(
                                    f'{self.read_write_tag_list[i]} = {tag_result.value}', 'yellow')
                            
                            self.update.emit('', 'white')
                        else:
                            yaml_temp[self.read_write_tag_list[0]
                                      ] = read_event_results.value
                            self.update.emit(
                                f'{self.read_write_tag_list[0]} = {read_event_results.value}', 'yellow')
                            
                        self.update.emit('', 'white')

                        self.yaml_data.append(yaml_temp)

                    except Exception as e:
                        print(f"Error in monitorer: {e}")
                else:
                    self.read_loop_enabled = False
            else:
                try:
                    result = self.plc.read(self.tag)

                    if result.value == self.value and self.hold == False:

                        yaml_temp = {}
                        self.hold = True
                        timestamp = datetime.datetime.now().strftime("%I:%M:%S:%f %p")
                        now = datetime.datetime.now()

                        self.update.emit(
                            f'Tag = {self.value} at Timestamp: {timestamp}<br>', 'yellow')

                        yaml_temp['Timestamp'] = timestamp

                        if self.first_event:
                            self.previous_timestamp = now
                            self.first_event = False
                            yaml_temp['Time Since Last Event'] = ''
                        else:
                            time_since_last_event = (
                                now - self.previous_timestamp).total_seconds() * 1000
                            self.update.emit(
                                f'Time since last event: {time_since_last_event} ms<br>', 'white')
                            self.previous_timestamp = now

                            yaml_temp['Time Since Last Event'] = time_since_last_event

                        if self.read_write_tag_list != None and self.read_selected:
                            read_event_results = plc.read(
                                *self.read_write_tag_list)

                            # if there were muliple tags in the read event
                            if type(read_event_results) is list:
                                for i, tag_result in enumerate(read_event_results):
                                    yaml_temp[self.read_write_tag_list[i]
                                              ] = tag_result.value
                                    self.update.emit(
                                        f'{self.read_write_tag_list[i]} = {tag_result.value}', 'yellow')
                                    
                                self.update.emit('', 'white')
                            else:
                                yaml_temp[self.read_write_tag_list[0]
                                          ] = read_event_results.value
                                self.update.emit(
                                    f'{self.read_write_tag_list[0]} = {read_event_results.value}', 'yellow')
                                self.update.emit('', 'white')

                            if not self.read_once:
                                self.read_loop_enabled = True
                                self.read_time_timestamp_start = datetime.datetime.now()

                        elif self.read_write_tag_list != None and self.write_selected:

                            tag_write_data = []

                            for i, value in enumerate([t.strip() for t in self.values_to_write.split(',')]):
                                tag_write_data.append(
                                    (self.read_write_tag_list[i], set_data_type(value, self.tags_to_read_write[i])))

                            self.plc.write(*tag_write_data)
                            self.update.emit(
                                f'Successfully wrote to tags: {self.tags_to_read_write}<br>', 'white')

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
        self.description_label = QLabel(
            "This project is a utility for reading and writing tags from Allen-Bradley PLCs. It can read and write from YAML files as well a convert the read file to CSV if desired. In addition to that it can trend tags and monitor tags for changes and write to them when they change.")
        self.description_label.setWordWrap(True)
        self.about_label = QLabel(
            "This project relies on the pycomm3 library made by ottowayi for communicating with Allen-Bradley PLCs.")
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


# Custom table widget for displaying tag-value pairs
class TableView(QTableWidget):
    def __init__(self, *args):
        QTableWidget.__init__(self, *args)
        self.setHorizontalHeaderLabels(['Tag', 'Value'])
        self.resizeRowsToContents()

        # Set columns to automatically resize and fill the widget
        self.header = self.horizontalHeader()
        self.header.setSectionResizeMode(QHeaderView.Stretch)

    def setData(self, data):
        row_count = self.rowCount()
        length = len(data.keys())

        if length > row_count:
            self.setRowCount(length)

        for i, (tag, value) in enumerate(data.items()):
            new_tag = QTableWidgetItem(tag)
            new_value = QTableWidgetItem(value)

            new_tag.setFlags(new_tag.flags() ^ Qt.ItemIsEditable)
            new_value.setFlags(new_value.flags() ^ Qt.ItemIsEditable)
            self.setItem(i, 0, new_tag)
            self.setItem(i, 1, new_value)

        self.header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.header.setSectionResizeMode(1, QHeaderView.ResizeToContents)


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

        self.settings = QSettings("PM Development", "PLC Tag Utility")

        ipRegex = QRegularExpression(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
        tagRegex = QRegularExpression(
            r"^[A-Za-z_][A-Za-z\d_]*(?:\[\d+\])?(?:\.[A-Za-z_][A-Za-z\d_]*(?:\[\d+\])?)*(?:\{\d+\})?(?:,\s*[A-Za-z_][A-Za-z\d_]*(?:\[\d+\])?(?:\.[A-Za-z_][A-Za-z\d_]*(?:\[\d+\])?)*(?:\{\d+\})?)*$")
        fileRegex = r"^[a-zA-Z0-9_-]+(\.(csv|yaml))?$"
        ipValidator = QRegularExpressionValidator(ipRegex)
        tagValidator = QRegularExpressionValidator(tagRegex)
        fileValidator = QRegularExpressionValidator(fileRegex)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['Tag', 'Value'])

        self.w = None
        self.setWindowTitle("PLC Read/Write")

        menubar = self.menuBar()
        menubar.addAction("About")
        menubar.show()

        # open AboutWindow when About is clicked
        menubar.triggered.connect(self.show_about_window)

        # Create timer for checking PLC connection
        self.plc_connection_check_timer = QTimer()
        self.plc_connection_check_timer.timeout.connect(
            lambda: check_plc_connection(plc, self))

        # Trender thread and signals
        self.trender = Trender()
        self.trend_thread = QThread()
        self.trender.moveToThread(self.trend_thread)
        self.trend_thread.started.connect(self.trender.run)
        self.trender.update.connect(self.print_results)
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
        self.monitorer.update.connect(self.print_results)

        container = QWidget(self)
        container.setMinimumWidth(400)

        # Create layouts
        main_layout = QHBoxLayout()
        entry_layout = QVBoxLayout()
        results_layout = QVBoxLayout()
        results_label_layout = QHBoxLayout()
        results_layout.addWidget(container)
        ip_layout = QHBoxLayout()
        read_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        write_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        trend_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        monitor_tab_layout = QVBoxLayout(alignment=Qt.AlignTop)
        self.monitor_radio_layout = QHBoxLayout()
        self.monitor_event_layout = QHBoxLayout()
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
        self.read_List_button = QPushButton("Read Tags In List")
        self.remove_tag_button = QPushButton("Remove Tag")
        self.add_tag_button = QPushButton("Add Tag")
        self.tags_to_read_list = QListView()
        model = QtGui.QStandardItemModel()

        # Set parameters
        self.remove_tag_button.setEnabled(False)
        self.tags_to_read_list.setModel(model)
        self.read_button.setDisabled(True)

        # Add to layouts
        read_tab_layout.addWidget(self.read_button)
        read_tab_layout.addWidget(self.tags_to_read_list)
        read_tab_layout.addWidget(self.add_tag_button)
        read_tab_layout.addWidget(self.remove_tag_button)
        read_tab_layout.addWidget(self.read_List_button)

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
        self.trend_plot_button.setEnabled(False)

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
        self.read_selected_radio = QRadioButton("Read On Event")
        self.write_selected_radio = QRadioButton("Write On Event")
        self.monitor_read_write_tags = QLineEdit()
        self.monitor_read_write_tags.setPlaceholderText(
            "Tags to Read/Write On Event")
        self.monitor_read_write_values = QLineEdit()
        self.monitor_read_write_values.setPlaceholderText(
            "Values to Write On Event")
        self.event_oneshot = QRadioButton("Read Once")
        self.event_timed = QRadioButton("Read For Set Time")
        self.event_time = QDoubleSpinBox()
        self.read_write_radio_group = QButtonGroup()
        self.event_radio_group = QButtonGroup()
        self.read_write_radio_group.addButton(self.read_selected_radio)
        self.read_write_radio_group.addButton(self.write_selected_radio)
        self.event_radio_group.addButton(self.event_oneshot)
        self.event_radio_group.addButton(self.event_timed)

        # Set parameters
        self.monitor_rate.setRange(0.1, 60)
        self.event_oneshot.setChecked(True)
        self.event_oneshot.setDisabled(True)
        self.event_timed.setDisabled(True)
        self.monitor_rate.setValue(1)
        self.monitor_rate.setSuffix(" seconds between reads")
        self.monitor_rate.setSingleStep(0.1)
        self.event_time.setRange(0.1, 60)
        self.event_time.setSuffix(" seconds to read tags")
        self.monitor_value.setPlaceholderText("Value to Monitor")
        self.monitor_button.setDisabled(True)
        self.read_selected_radio.setEnabled(False)
        self.write_selected_radio.setEnabled(False)
        self.event_time.setEnabled(False)

        # Add to layouts
        self.monitor_radio_layout.addWidget(self.read_selected_radio)
        self.monitor_radio_layout.addWidget(self.write_selected_radio)
        monitor_tab_layout.addWidget(self.monitor_value)
        monitor_tab_layout.addWidget(self.monitor_rate)
        monitor_tab_layout.addWidget(self.enable_event)
        monitor_tab_layout.addLayout(self.monitor_radio_layout)
        monitor_tab_layout.addWidget(self.monitor_button)
        self.monitor_event_layout.addWidget(self.event_oneshot)
        self.monitor_event_layout.addWidget(self.event_timed)
        monitor_tab_layout.addLayout(self.monitor_event_layout)
        monitor_tab_layout.addWidget(self.event_time)
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
        self.results_label = QLabel("Results")
        self.results = QTextEdit()
        self.file_format_selection = QComboBox()
        self.file_format = 0
        self.table = TableView(0, 2)
        self.table_label = QLabel("Read History")
        self.clear_results_button = QPushButton("Clear Results")

        # Set parameters
        self.tag_input.setPlaceholderText("Tag1, Tag2...")
        self.file_name.setPlaceholderText("File Name")
        self.ip_input.setMaxLength(15)
        self.ip_input.setPlaceholderText("IP Address")
        self.results.setReadOnly(True)
        self.file_format_selection.addItems(["YAML", "CSV"])
        self.file_name.setValidator(fileValidator)
        self.file_name.textChanged.connect(self.on_file_text_changed)
        self.file_format_selection.currentIndexChanged.connect(
            self.file_format_changed)
        self.ip_input.setValidator(ipValidator)
        self.ip_input.textChanged.connect(self.on_ip_text_changed)
        self.tag_input.setValidator(tagValidator)
        self.tag_input.textChanged.connect(self.on_tag_text_changed)

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
        results_label_layout.addWidget(self.results_label)
        results_label_layout.addWidget(self.clear_results_button)
        results_layout.addLayout(results_label_layout)
        results_layout.addWidget(self.results)
        results_layout.addWidget(self.table_label)
        results_layout.addWidget(self.tree)
        # results_layout.addWidget(self.table)

        self.tag_read_history = {}

        # Add to main layout
        main_layout.addLayout(entry_layout)
        main_layout.addLayout(results_layout)

        # Set central widget
        widget = QWidget()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)

        # --------------------------------------------#
        #              MOUSE HOVER TIPS               #
        # --------------------------------------------#

        self.read_button.setToolTip(
            "Reads the tag specified in the tag input field.")
        self.write_button.setToolTip(
            "Writes the value specified in the value input field to the tag specified in the tag input field.")
        self.trend_button.setToolTip(
            "Starts trending the tag specified in the tag input field.")
        self.monitor_button.setToolTip(
            "Starts monitoring the tag specified in the tag input field.")
        self.ip_input.setToolTip("Enter the IP address of the PLC.")
        self.tag_input.setToolTip("Enter the tag to read or write to.")
        self.file_enabled.setToolTip("Enable reading and writing to a file.")
        self.file_name.setToolTip(
            "Enter the name of the file to read or write to.")
        self.file_browser.setToolTip("Browse for a file to read or write to.")
        self.connect_button.setToolTip("Connect or disconnect PLC connection.")
        self.results.setToolTip(
            "Displays the results of the last read or write operation and any user messages.")
        self.read_List_button.setToolTip("Reads the tags in the list above.")
        self.remove_tag_button.setToolTip(
            "Removes the selected tag from the list.")
        self.add_tag_button.setToolTip(
            "Adds the tag in the tag input field to the list.")
        self.trend_rate.setToolTip(
            "Enter the interval between reads in seconds.")
        self.trend_plot_button.setToolTip("Plots the trend data.")
        self.monitor_value.setToolTip("Enter the value to monitor.")
        self.monitor_rate.setToolTip(
            "Enter the interval between reads in seconds.")
        self.enable_event.setToolTip("Enable reading and writing on event.")
        self.read_selected_radio.setToolTip(
            "Reads the tags specified in the tags to read/write on event input field.")
        self.write_selected_radio.setToolTip(
            "Writes the values specified in the values to read/write on event input field to the tags specified in the tags to read/write on event input field.")
        self.monitor_read_write_tags.setToolTip(
            "Enter the tags to read/write on event.")
        self.monitor_read_write_values.setToolTip(
            "Enter the values to write on event.")
        self.write_value.setToolTip("Enter the value to write to the tag.")

        self.setStyleSheet("""QToolTip { 
                           background-color: black; 
                           color: white; 
                           border: black solid 1px;
                           border-radius:10px;
                           }""")

        # --------------------------------------------#
        #               CONNECT EVENTS                #
        # --------------------------------------------#

        # Connect read button to read_tag function
        self.read_button.clicked.connect(self.read_tag_button_clicked)

        self.write_button.clicked.connect(self.write_tag_button_clicked)

        self.trend_button.clicked.connect(self.trender_thread)
        self.trend_plot_button.clicked.connect(lambda: plot_trend_data(
            self.trender.tags, self.trender_results, self.trender_timestamps, self.trender.single_tag))
        self.monitor_button.clicked.connect(self.monitorer_thread)
        self.connect_button.clicked.connect(self.connect_button_clicked)
        self.file_browser.clicked.connect(
            lambda: self.file_name.setText(QFileDialog.getOpenFileName()[0]))

        self.tags_to_read_list.selectionModel().selectionChanged.connect(
            self.handle_list_selection_changed
        )
        self.remove_tag_button.clicked.connect(self.remove_from_list)
        self.add_tag_button.clicked.connect(self.add_to_list)
        self.read_List_button.clicked.connect(
            self.read_tag_list_button_clicked)
        self.enable_event.stateChanged.connect(self.set_read_write_selection)

        self.write_selected_radio.toggled.connect(self.read_event_deselected)
        self.read_selected_radio.toggled.connect(self.read_event_selected)
        self.event_timed.toggled.connect(self.monitor_read_set_time_selected)
        self.event_oneshot.toggled.connect(self.monitor_read_one_shot_selected)
        self.clear_results_button.clicked.connect(self.clear_results)

        # Load stored data if available
        self.ip_input.setText(self.settings.value('ip', ''))
        self.tag_input.setText(self.settings.value('tag', ''))
        self.populate_list_from_history()

        self.tree_data = {}

    def clear_results(self):
        self.results.clear()

    def add_to_tree(self, data, parent):
        if parent.childCount() > 0:
            existing_keys = {parent.child(i).text(0): parent.child(
                i) for i in range(parent.childCount())}
        else:
            existing_keys = {}

        if isinstance(data, dict):
            for key, value in data.items():
                if key in existing_keys:
                    item = existing_keys[key]
                    if isinstance(value, dict):
                        self.add_to_tree(value, item)
                    else:
                        item.setText(1, str(value))
                else:
                    if isinstance(value, dict):
                        new_item = QTreeWidgetItem(
                            parent, [key, ''])
                        self.add_to_tree(value, new_item)
                    elif isinstance(value, list):
                        for i, v in enumerate(value):
                            if isinstance(v, dict):
                                new_item = QTreeWidgetItem(
                                    parent, [f'{key}[{i}]', ''])
                                self.add_to_tree(v, new_item)
                            else:
                                new_item = QTreeWidgetItem(
                                    parent, [f'{key}[{i}]', str(v)])
                                self.add_to_tree(v, new_item)
                    else:
                        new_item = QTreeWidgetItem(parent, [key, str(value)])
        if isinstance(data, list):
            for i, value in enumerate(data):
                if isinstance(value, dict):
                    new_item = QTreeWidgetItem(parent, [f'{i}', ''])
                    self.add_to_tree(value, new_item)
                elif isinstance(value, list):
                    for j, v in enumerate(value):
                        if isinstance(v, dict):
                            new_item = QTreeWidgetItem(
                                parent, [f'{i}[{j}]', ''])
                            self.add_to_tree(v, new_item)
                        else:
                            new_item = QTreeWidgetItem(
                                parent, [f'{i}[{j}]', str(v)])
                            self.add_to_tree(v, new_item)
                else:
                    new_item = QTreeWidgetItem(parent, [f'{i}', str(value)])

        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)

    def read_event_selected(self):
        self.event_oneshot.setEnabled(True)
        self.event_timed.setEnabled(True)

    def read_event_deselected(self):
        self.event_oneshot.setEnabled(False)
        self.event_timed.setEnabled(False)
        self.event_radio_group.setExclusive(False)
        self.event_oneshot.setChecked(True)
        self.event_timed.setChecked(False)
        self.event_radio_group.setExclusive(True)

    def monitor_read_set_time_selected(self):
        self.event_time.setEnabled(True)

    def monitor_read_one_shot_selected(self):
        self.event_time.setEnabled(False)

    def set_read_write_selection(self):
        if self.enable_event.isChecked():
            self.read_selected_radio.setEnabled(True)
            self.write_selected_radio.setEnabled(True)
        else:
            self.read_selected_radio.setEnabled(False)
            self.write_selected_radio.setEnabled(False)
            self.read_write_radio_group.setExclusive(False)
            self.read_selected_radio.setChecked(False)
            self.write_selected_radio.setChecked(False)
            self.read_write_radio_group.setExclusive(True)
            self.event_timed.setEnabled(False)
            self.event_oneshot.setEnabled(False)
            self.event_radio_group.setExclusive(False)
            self.event_timed.setChecked(False)
            self.event_oneshot.setChecked(True)
            self.event_radio_group.setExclusive(True)

    def handle_list_selection_changed(self):
        self.remove_tag_button.setEnabled(
            bool(self.tags_to_read_list.selectedIndexes()))

    def remove_from_list(self):
        for index in self.tags_to_read_list.selectedIndexes():
            self.tags_to_read_list.model().removeRow(index.row())

            self.settings.setValue('tag_list', self.get_from_list())

            # check if list is empty now
            if self.tags_to_read_list.model().rowCount() == 0:
                self.read_List_button.setEnabled(False)

    def add_to_list(self):
        if check_plc_connection(plc, self):
            tags = [t.strip() for t in self.tag_input.text().split(',')]
            for tag in tags:
                if self.tag_input.hasAcceptableInput():
                    if self.is_valid_tag_input(tag, tag_types):
                        # check if tag already in list
                        if tag not in [self.tags_to_read_list.model().item(i).text() for i in range(self.tags_to_read_list.model().rowCount())]:
                            self.tags_to_read_list.model().appendRow(
                                QtGui.QStandardItem(tag))
                            self.read_List_button.setEnabled(True)
                            self.settings.setValue(
                                'tag_list', self.get_from_list())
                    else:
                        self.print_results(f"{tag} does not exist in PLC.", 'red')
                else:
                    self.print_results("Tag input: '{tag}' is invalid.", 'red')
        else:
            self.showNotConnectedDialog()

    def populate_list_from_history(self):
        tags = self.settings.value('tag_list', '')
        if tags != '':
            for tag in tags.split(','):
                tag = tag.strip()
                self.tags_to_read_list.model().appendRow(QtGui.QStandardItem(tag))

    def get_from_list(self):
        tags = ''
        first_item = True
        for index in range(self.tags_to_read_list.model().rowCount()):
            if not first_item:
                tags += ', '
            else:
                first_item = False

            tags = tags + self.tags_to_read_list.model().item(index).text().strip()

        return tags

    def save_history(self):
        self.settings.setValue('ip', self.ip_input.text())
        self.settings.setValue('tag', self.tag_input.text())
        self.settings.setValue('tag_list', self.get_from_list())

    def add_to_table(self, data):
        self.table.setData(data)

    def on_ip_text_changed(self, text):
        if self.ip_input.hasAcceptableInput():
            self.ip_input.setStyleSheet("color: white;")
        else:
            self.ip_input.setStyleSheet("color: red;")

    def on_file_text_changed(self, text):
        if self.file_name.hasAcceptableInput():
            self.file_name.setStyleSheet("color: white;")
        else:
            self.file_name.setStyleSheet("color: red;")

    def on_tag_text_changed(self, text):
        if self.tag_input.hasAcceptableInput():
            self.tag_input.setStyleSheet("color: white;")
        else:
            self.tag_input.setStyleSheet("color: red;")

    def file_format_changed(self, i):
        self.file_format = i

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

    def connect_button_clicked(self):
        if self.ip_input.hasAcceptableInput():
            connect_to_plc(self.ip_input.text(), self.connect_button, self)
        else:
            self.print_results("IP address is invalid.", 'red')

    def is_valid_tag_input(self, tags, tag_types):
        # Validate format
        pattern = r"^[A-Za-z_][A-Za-z\d_]*(?:\[\d+\])?(?:\.\w+(?:\[\d+\])?)*(?:\{\d+\})?(?:,\s*[A-Za-z_][A-Za-z\d_]*(?:\[\d+\])?(?:\.\w+(?:\[\d+\])?)*(?:\{\d+\})?)*$"
        if not re.match(pattern, tags):
            return False

        # Process input by removing [x] and {x}
        stripped_input = re.sub(r"(\[\d+\])|(\{\d+\})", "", tags)
        input_tags = [tag.strip() for tag in stripped_input.split(',')]

        # Check against dictionary
        for input_tag in input_tags:
            tag_components = input_tag.split('.')
            # if not any(all(tc == kc.split('.')[i] for i, tc in enumerate(input_tag) if i < len(kc.split('.'))) for kc in tag_types):
            if input_tag not in tag_types:
                return False

        return True

    def check_and_convert_file_name(self):
        file_name = self.file_name.text()

        if '.csv' not in file_name and '.yaml' not in file_name:
            if self.file_format == 0:
                file_name = file_name + '.yaml'
            else:
                file_name = file_name + '.csv'

        return file_name

    def read_tag_button_clicked(self):
        if check_plc_connection(plc, self):
            if self.tag_input.hasAcceptableInput():
                if self.is_valid_tag_input(self.tag_input.text(), tag_types):
                    self.save_history()
                    if self.file_name.text() != '':
                        file_name = self.check_and_convert_file_name()
                        read_tag(self.tag_input.text(), plc, self, store_to_file=self.file_enabled.isChecked(
                        ), file_name=file_name, file_selection=self.file_format)
                    else:
                        read_tag(self.tag_input.text(
                        ), plc, self, store_to_file=self.file_enabled.isChecked(), file_selection=self.file_format)
                else:
                    self.print_results("Tag or tags do not exist in PLC.", 'red')
            else:
                self.print_results("Tag input is invalid.", 'red')
        else:
            self.showNotConnectedDialog()

    def read_tag_list_button_clicked(self):
        if check_plc_connection(plc, self):
            if self.is_valid_tag_input(self.get_from_list(), tag_types):
                self.save_history()
                if self.file_name.text() != '':
                    file_name = self.check_and_convert_file_name()
                    read_tag(self.get_from_list(), plc, self, store_to_file=self.file_enabled.isChecked(
                    ), file_name=file_name, file_selection=self.file_format)
                else:
                    read_tag(self.get_from_list(
                    ), plc, self, store_to_file=self.file_enabled.isChecked(), file_selection=self.file_format)
            else:
                self.print_results("Tag or tags do not exist in PLC.", 'red')
        else:
            self.showNotConnectedDialog()

    def write_tag_button_clicked(self):
        if check_plc_connection(plc, self):
            if self.tag_input.hasAcceptableInput():
                if self.is_valid_tag_input(self.tag_input.text(), tag_types):
                    if self.verify_write_values():
                        self.save_history()
                        if self.file_name.text() != '':
                            file_name = self.check_and_convert_file_name()
                            write_tag(self.tag_input.text(), self.write_value.text(
                            ), self, plc, file_enabled=self.file_enabled.isChecked(), file_name=file_name, file_selection=self.file_format)
                        else:
                            write_tag(self.tag_input.text(), self.write_value.text(
                            ), self, plc, file_enabled=self.file_enabled.isChecked(), file_selection=self.file_format)
                else:
                    self.print_results("Tag or tags do not exist in PLC.", 'red')
            else:
                self.print_results("Tag input is invalid.", 'red')
        else:
            self.showNotConnectedDialog()
            
    def verify_write_values(self):
        if not self.write_value.text() == '':
            values = [v.strip() for v in self.write_value.text().split(',')]
            tags = [t.strip() for t in self.tag_input.text().split(',')]
            
            if len(values) != len(tags):
                self.print_results("Number of values does not match number of tags.<br>", 'red')
            
            return True
        else:
            self.print_results("No value entered.<br>", 'red')
            

    def print_results(self, results, color='white'):
        
        cursor = self.results.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        cursor.insertHtml(f"<span style='color: {color};'>{results}</span><br>")
        # set scroll bar to bottom
        self.results.verticalScrollBar().setValue(
            self.results.verticalScrollBar().maximum())

    def update_trend_data(self, results, timestamps):
        self.trender_results = results
        self.trender_timestamps = timestamps

    def trender_thread(self):
        if self.trender.running:
            if self.file_name.text() != '':
                file_name = self.check_and_convert_file_name()
            else:
                file_name = ''
            process_trend_data(self.trender.tags, self.trender.results, self.trender.timestamps, self.trender.single_tag,
                               self.file_enabled.isChecked(), file_name, self.file_format_selection.currentIndex())
            self.trender.stop()
            self.trend_button.setText("Start Trend")
        else:
            if check_plc_connection(plc, self):
                if self.tag_input.hasAcceptableInput():
                    if self.is_valid_tag_input(self.tag_input.text(), tag_types):

                        self.save_history()

                        if not self.trend_thread.isRunning():
                            self.trender.ip = self.ip_input.text()
                            self.trender.tags = self.tag_input.text()
                            self.trender.interval = (
                                self.trend_rate.value() * 1000)
                            self.trender.plc = plc
                            self.trender.running = True
                            self.trend_thread.start()
                            self.trend_plot_button.setEnabled(True)
                            self.trend_button.setText("Stop Trend")
                    else:
                        self.print_results("Tag or tags do not exist in PLC.", 'red')
                else:
                    self.print_results("Tag input is invalid.", 'red')
            else:
                self.showNotConnectedDialog()

    def process_monitor_data(self, yaml_data):
        if self.file_enabled.isChecked():
            if self.file_name.text() != '':
                file_name = self.check_and_convert_file_name()
            else:
                if self.file_format == 0:
                    file_name = 'trend_data.yaml'
                else:
                    file_name = 'trend_data.csv'

            with open(file_name, 'w') as f:

                if self.file_format == 0:
                    yaml.safe_dump(yaml_data, f, default_flow_style=False)
                else:
                    writer = csv.writer(f, lineterminator='\n')
                    yaml_data_keys = yaml_data[0].keys()
                    header = []
                    for key in yaml_data_keys:
                        header.append(key)
                    writer.writerow(header)

                    for data in yaml_data:
                        row = []
                        for value in data.values():
                            row.append(value)

                        writer.writerow(row)

    def monitorer_thread(self):
        if self.monitorer.running:
            self.process_monitor_data(self.monitorer.yaml_data)
            self.monitorer.stop()
            self.monitor_button.setText("Start Monitor")
        else:
            if check_plc_connection(plc, self):
                if self.tag_input.hasAcceptableInput():
                    if self.is_valid_tag_input(self.tag_input.text(), tag_types):

                        self.save_history()

                        if not self.monitor_thread.isRunning():
                            self.monitorer.ip = self.ip_input.text()
                            self.monitorer.tags_to_read_write = self.monitor_read_write_tags.text()
                            self.monitorer.values_to_write = self.monitor_read_write_values.text()
                            self.monitorer.read_selected = self.read_selected_radio.isChecked()
                            self.monitorer.write_selected = self.write_selected_radio.isChecked()
                            self.monitorer.tag = self.tag_input.text()
                            self.monitorer.value = set_data_type(
                                self.monitor_value.text(), self.tag_input.text())
                            self.monitorer.interval = (
                                self.monitor_rate.value() * 1000)
                            self.monitorer.plc = plc

                            self.monitorer.read_once = self.event_oneshot.isChecked()

                            if self.event_timed.isChecked():
                                self.monitorer.read_time = self.event_time.value()

                            self.monitorer.running = True
                            self.monitor_thread.start()
                            self.monitor_button.setText("Stop Monitor")
                    else:
                        self.print_results("Tag or tags do not exist in PLC.", 'red')
                else:
                    self.print_results("Tag input is invalid.", 'red')
            else:
                self.showNotConnectedDialog()

    def start_plc_connection_check(self):
        self.plc_connection_check_timer.start(5000)

    def stop_plc_connection_check(self):
        self.plc_connection_check_timer.stop()
        self.connect_button.setText("Connect")


app = QApplication(sys.argv)
app.setWindowIcon(QtGui.QIcon('icon.ico'))
qdarktheme.setup_theme()
window = MainWindow()
window.resize(1000, 600)
window.show()

app.exec()
