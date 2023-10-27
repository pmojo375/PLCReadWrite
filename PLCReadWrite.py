from pycomm3 import LogixDriver
import re
import pickle
import time
import pandas as pd
import csv
from ast import literal_eval
import PySimpleGUI as sg
import threading
import datetime
import matplotlib.pyplot as plt
import numpy as np
import json

tag_list_retrieved = False
tag_list = []

# serializes the returned tag or list of tags to json format and writes to a file
def deserialize_from_json():
    with open('tag_values.json', 'r') as f:
        json_data = json.load(f)
        tag_values = []
        for item in json_data:
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


def process_json_read(data):

    processed_data = []

    for tag in data:
        tag_name = tag['tag']
        tag_value  = tag['value']

        processed_data = iterate_value(tag_name, tag_value, processed_data)

    return processed_data


# serializes the returned tag or list of tags to json format and writes to a file
def serialize_to_json(data):
    with open('tag_values.json', 'w') as f:

        json_data = []

        if isinstance(data, list):
            for tag in data:
                if isinstance(tag.value, list):
                    for i, value in enumerate(tag.value):
                        json_data.append({f'{tag.tag}[{str(i)}]': value})
                else:
                    json_data.append({tag.tag: tag.value})
        else:
            json_data.append({tag.tag: tag.value})

        json.dump(json_data, f, indent=4)


def process_structure(structure, array, name):
    """
    Recursively processes the structure of the JSON data and appends the data types to the array.

    Args:
        structure (dict): The structure of the JSON data.
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


def get_tags_from_json(ip):
    """
    Gets the data types from the JSON data.

    Args:
        data (dict): The JSON data.

    Returns:
        list: The list of data types.
    """
    ret = {}
    
    with LogixDriver(ip) as plc:
        data = plc.tags_json
    
    for tag_name in data.keys():
        tag = data[tag_name]
        if isinstance(tag['data_type'], str):
            ret[tag_name] = tag['data_type']
        elif isinstance(tag['data_type'], dict):
            internal_tags = tag['data_type']['internal_tags']
            ret = process_structure(internal_tags, ret, tag_name)

    return ret


'''
- Get all tag return types for offline testing
- Need each native type
- Need each array type of each native type
- Need native UDT type (timer, counter, etc.)
- Need UDT type with each native type and an array of each native type
- Need UDT with nested UDTs and arrays of them
- Need UDT with native nested UDTs and arrays of them

- BOOL, DINT, INT, REAL, SINT, STRING
- BOOL[2], DINT[2], INT[2], REAL[2], SINT[2], STRING[2]
- Tag(tag='zzzDint', value=0, type='DINT', error=None)
    - single value
- Tag(tag='zzzDintArray', value=[1, 2, 3, 4, 5], type='DINT[5]', error=None)
    - list value
- TIMER, COUNTER, CONTROL
- TIMER[2], COUNTER[2], CONTROL[2]
- UDT, UDT[2]
- Tag(tag='zzzUDT', value={'Status': 0, 'RejectCode': 0, 'Model': {'Name': '', 'ModelNum': '', 'UpperTSNum': '', 'LowerTSNum': '', 'Carton': '', 'ColorCode': 0, 'BaseType': 0, 'SNType': 0, 'CartonHeight': 0, 'UPC': '', 'InstallationKit': '', 'Base': '', 'IsRibbed': False, 'GetsSensomaticTag': False, 'SpoutLabel': False}, 'IntialPalletNum': 0, 'FinalPalletNum': 0, 'TrimshellScrews': [{'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}], 'TrimshellStation': 0, 'LabelerStation': 0, 'UnitData': {'Matrix': '', 'SN': ''}}, type='PalletData', error=None)
    - Dict value for UDT
- Tag(tag='zzzUDTArray', value=[{'Status': 1, 'RejectCode': 0, 'Model': {'Name': 'Test', 'ModelNum': '', 'UpperTSNum': '', 'LowerTSNum': '', 'Carton': '', 'ColorCode': 0, 'BaseType': 0, 'SNType': 0, 'CartonHeight': 0, 'UPC': '', 'InstallationKit': '', 'Base': '', 'IsRibbed': True, 'GetsSensomaticTag': False, 'SpoutLabel': False}, 'IntialPalletNum': 0, 'FinalPalletNum': 0, 'TrimshellScrews': [{'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}], 'TrimshellStation': 0, 'LabelerStation': 0, 'UnitData': {'Matrix': '', 'SN': ''}}, {'Status': 2, 'RejectCode': 0, 'Model': {'Name': 'Test', 'ModelNum': '', 'UpperTSNum': '', 'LowerTSNum': '', 'Carton': '', 'ColorCode': 0, 'BaseType': 0, 'SNType': 0, 'CartonHeight': 0, 'UPC': '', 'InstallationKit': '', 'Base': '', 'IsRibbed': True, 'GetsSensomaticTag': False, 'SpoutLabel': False}, 'IntialPalletNum': 0, 'FinalPalletNum': 0, 'TrimshellScrews': [{'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}], 'TrimshellStation': 0, 'LabelerStation': 0, 'UnitData': {'Matrix': '', 'SN': ''}}, {'Status': 3, 'RejectCode': 0, 'Model': {'Name': 'Test', 'ModelNum': '', 'UpperTSNum': '', 'LowerTSNum': '', 'Carton': '', 'ColorCode': 0, 'BaseType': 0, 'SNType': 0, 'CartonHeight': 0, 'UPC': '', 'InstallationKit': '', 'Base': '', 'IsRibbed': False, 'GetsSensomaticTag': False, 'SpoutLabel': False}, 'IntialPalletNum': 0, 'FinalPalletNum': 0, 'TrimshellScrews': [{'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}], 'TrimshellStation': 0, 'LabelerStation': 0, 'UnitData': {'Matrix': '', 'SN': ''}}, {'Status': 4, 'RejectCode': 0, 'Model': {'Name': '', 'ModelNum': '', 'UpperTSNum': '', 'LowerTSNum': '', 'Carton': '', 'ColorCode': 0, 'BaseType': 0, 'SNType': 0, 'CartonHeight': 0, 'UPC': '', 'InstallationKit': '', 'Base': '', 'IsRibbed': False, 'GetsSensomaticTag': False, 'SpoutLabel': False}, 'IntialPalletNum': 0, 'FinalPalletNum': 0, 'TrimshellScrews': [{'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}], 'TrimshellStation': 0, 'LabelerStation': 0, 'UnitData': {'Matrix': '', 'SN': ''}}, {'Status': 5, 'RejectCode': 0, 'Model': {'Name': '', 'ModelNum': '', 'UpperTSNum': '', 'LowerTSNum': '', 'Carton': '', 'ColorCode': 0, 'BaseType': 0, 'SNType': 0, 'CartonHeight': 0, 'UPC': '', 'InstallationKit': '', 'Base': '', 'IsRibbed': False, 'GetsSensomaticTag': False, 'SpoutLabel': False}, 'IntialPalletNum': 0, 'FinalPalletNum': 0, 'TrimshellScrews': [{'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}, {'Torque': 0.0, 'Angle': 0.0}], 'TrimshellStation': 0, 'LabelerStation': 0, 'UnitData': {'Matrix': '', 'SN': ''}}], type='PalletData[5]', error=None)
    - List of Dict value for UDT list
- UDT.NestedUDT, UDT.NestedUDT[2]
'''
type_list = {}

# This function will crawl through a dictionary and format the data
def crawl_and_format(obj, name, data):

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


# This function sets the data type of the given value based on the tag.
# It takes in a value and a tag, and returns the value with the determined data type.
# If there is an error in setting the data type, it raises an Exception.
# If there is an unexpected quote in the value, it raises a ValueError.
def set_data_type(value, tag):
    """
    This function sets the data type of the given value based on the tag.

    Args:
    - value: The value to be set.
    - tag: The tag to determine the data type.

    Returns:
    - The value with the determined data type.

    Raises:
    - ValueError: If there is an unexpected quote in the value.
    - Exception: If there is an error in setting the data type.

    """
    try:
        # Check if the tag is in the tag_list
        if tag in tag_list:
            # Get the data type from the tag_list
            type = tag_list[tag]

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


# This function will write a CSV file
def write_csv(csv_name, data):
    if type(data) == list:
        with open(csv_name, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[*data[0]])
            writer.writeheader()
            writer.writerows(data)
    else:
        with open(csv_name, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=[*data])
            writer.writeheader()
            writer.writerow(data)


# This function will write a tag value pair to the PLC
def write_tag(ip, tag, value, **kwargs):
    with LogixDriver(ip) as plc:
        return plc.write(tag, set_data_type(value, tag))


# Writes tag value pairs read from a CSV file
def write_tags_from_json(ip, json_name):

    with LogixDriver(ip) as plc:
        tags = process_json_read(deserialize_from_json())

        return plc.write(*tags)


# UNUSED
# This function will read tags from a CSV file and store them in a CSV file if desired
def read_tag_from_json(ip, json_name, **kwargs):
    store_to_json = kwargs.get('store_to_json', False)

    data = []

    # opening the CSV file
    with open(json_name, mode ='r') as file:   
        
        # reading the CSV file
        csvFile = csv.reader(file)

        line = 0
        
        # displaying the contents of the CSV file
        for lines in csvFile:
            if line != 0:
                data.append(lines[0])

            line = line + 1

    for tag in data:
        read_tag(ip, tag, store_to_csv = store_to_json)


# This function will read a tag value pair from the PLC
def read_tag(ip, tags, **kwargs):

    store_to_json = kwargs.get('store_to_json', False)

    return_data = []
    tmp = []
    data = {}

    json_name = kwargs.get('json_name', 'tag_values.csv')

    with LogixDriver(ip) as plc:

        ret = plc.read(*tags)

        if store_to_json:
            if isinstance(ret, list):
                serialize_to_json(ret)
            else:
                serialize_to_json([ret])

        # loop through each tag in the list
        if len(tags) == 1:
            entry_tag = tags[0]
            value = ret.value
            return_data.append(crawl_and_format(value, entry_tag, data))
        else:
            for i, tag in enumerate(tags):
                entry_tag = tags[i]
                value = ret[i].value
                return_data.append(crawl_and_format(value, entry_tag, data))

    return return_data


# Saves the IP address and tag to a pickled file to read when opening later
def save_history(ip, tag):
    if ip != '' and tag != '':
        f = open('plc_readwrite.pckl', 'wb')
        pickle.dump((ip, tag), f)
        f.close()


# Checks that the IP address entered is a valid IP address
def validate_ip(ip):
    pattern = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    if pattern.match(ip):
        return True
    else:
        return False


# This function will read a tag value pair from the PLC at a set interval
class TagMonitor:
    def __init__(self, ip, tag):
        self.ip = ip
        self.tag = tag
        self.interval = .1
        self.plc = LogixDriver(self.ip)
        self.plc.open()
        self.stop_event = threading.Event()
        self.results = []
        self.timestamps = []
        self.hold = False
        self.thread = None

    def read_tag(self, window):

        while not self.stop_event.is_set():
            result = self.plc.read(self.tag)

            if result.value == 1 and self.hold == False:
                print('Tag High')
                self.hold = True
                window.write_event_value('-THREAD-', f'Tag High at Timestamp: {datetime.datetime.now().strftime("%I:%M:%S:%f %p")}')
            
            if result.value == 0:
                self.hold = False

            self.stop_event.wait(self.interval)
    
    def stop(self):
        if self.thread is not None:
            self.stop_event.set()

    def set_tag(self, tag):
        self.tag = tag

    def run(self, window):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.read_tag, args=(window,))
        self.thread.start()


# This function will read a tag value pair from the PLC at a set interval
class TagTrender:
    def __init__(self, ip, tag, interval=1):
        self.ip = ip
        self.tag = tag
        self.interval = interval
        self.plc = LogixDriver(self.ip)
        self.plc.open()
        self.stop_event = threading.Event()
        self.results = []
        self.timestamps = []
        self.thread = None
        self.first_pass = True
        self.single_tag = True

    def read_tag(self, window):
        start_time = datetime.datetime.now()

        while not self.stop_event.is_set():

            # Convert tag input to a list
            formatted_tag = [t.strip() for t in self.tag.split(',')]

            result = self.plc.read(*formatted_tag)

            if isinstance(result, list):
                result = result
            else:
                result = [result]

            if self.first_pass:
                length = len(result)
                if length > 1:
                    self.single_tag = False

                    for i in range(length):
                        self.results.append([])
                
                self.first_pass = False

            window.write_event_value('-THREAD-', f'Timestamp: {datetime.datetime.now().strftime("%I:%M:%S:%f %p")}')
            if self.single_tag:
                window.write_event_value('-THREAD-', f'\n{result[0].value}')
                self.results.append(result[0].value)
            else:
                for i, r in enumerate(result):            
                    window.write_event_value('-THREAD-', f'\n{formatted_tag[i]} = {r.value}')
                    self.results[i].append(r.value)
            
            self.timestamps.append((datetime.datetime.now() - start_time).total_seconds() * 1000)
            self.stop_event.wait(self.interval)
    
    def stop(self):
        if self.thread is not None:
            self.stop_event.set()

    def set_tag(self, tag):
        self.tag = tag

    def run(self, window):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self.read_tag, args=(window,))
        self.thread.start()

sg.theme("DarkBlue")

json_read_tooltip = ' When checked, the read tag results will be stored to a CSV file. A file \n name can be inputted or one will be auto generated if left empty. '
json_write_tooltip = ' When checked, a CSV file containing tag/value pairs will be written to the PLC. \n The header must be "tag,value". A CSV filename must be specified to read from. '
value_tooltip = ' When writing a tag, the value must be in the correct format. \n For example, a BOOL must be written as 1 (True) or 0 (False). \n UDTs must be written out in their full expanded names. \n For example: UDT.NestedUDT.TagName                     '
json_plot_tooltip = ' When checked, a plot of the tag values will \n be displayed after the trend is stopped. '

header = [[sg.Text('IP Address'), sg.InputText(key='-IP-', size=15)],
          [sg.Frame('Tag', [[sg.InputText(key='-TAG-', size=40)]])]]

read_tab = [[sg.Frame('JSON', [[sg.CB('Write Results To JSON', tooltip=json_read_tooltip, key='-JSON_READ-', enable_events=True)],
            [sg.FileBrowse('Browse', file_types=(('JSON Files', '*.json'),), key='-JSON_READ_FILE_BROWSE-', disabled=True), sg.InputText(key='-JSON_READ_FILE-', disabled=True, size=31)]])],
            [sg.Frame('Trend Rate', [[sg.InputText(key='-RATE-', size=40)], [sg.CB('Show Trend Plot', tooltip=json_plot_tooltip, key='-JSON_PLOT-', enable_events=True)]])],
            [sg.Column([[sg.Button('Read'), sg.Button('Start Monitor'), sg.Button('Cancel')]], justification='r')],
            [sg.Column([[sg.Button('Start Trend'), sg.Button('Show Trend Plot')]], justification='r')]]

write_tab = [[sg.Frame('JSON', [[sg.CB('Write From JSON', tooltip=json_write_tooltip, key='-JSON_WRITE-', enable_events=True)],
             [sg.FileBrowse('Browse', file_types=(('JSON Files', '*.json'),), key='-JSON_WRITE_FILE_BROWSE-', disabled=True), sg.InputText(key='-JSON_WRITE_FILE-', disabled=True, size=31)]])],
             [sg.Frame('Value', [[sg.InputText(tooltip=value_tooltip, key='-VALUE-', size=40)]])],
             [sg.Column([[sg.Button('Write'), sg.Button('Cancel')]], justification='r')]]

footer = [[sg.Frame('Results', [[sg.Multiline(size=(38, 10), reroute_stdout=True)]])]]

tabs = [[header, sg.TabGroup([[
    sg.Tab('Read', read_tab), sg.Tab('Write', write_tab)]])], footer]

# Create the Window
window = sg.Window('PLC Tag Read/Write', tabs, size=(300, 500))

trender = None
monitorer = None

from matplotlib.backend_bases import MouseEvent

class SnappingCursor:
    """
    A cross-hair cursor that snaps to the data point of a line, which is
    closest to the *x* position of the cursor.

    For simplicity, this assumes that *x* values of the data are sorted.
    """
    def __init__(self, ax, line):
        self.ax = ax
        self.horizontal_line = ax.axhline(color='w', lw=0.8, ls='--')
        self.vertical_line = ax.axvline(color='w', lw=0.8, ls='--')
        self.x, self.y = line.get_data()
        self._last_index = None
        # text location in axes coords
        self.text = ax.text(0.72, 0.9, '', transform=ax.transAxes, color='w')

    def set_cross_hair_visible(self, visible):
        need_redraw = self.horizontal_line.get_visible() != visible
        self.horizontal_line.set_visible(visible)
        self.vertical_line.set_visible(visible)
        self.text.set_visible(visible)
        return need_redraw

    def on_mouse_move(self, event):
        if not event.inaxes:
            self._last_index = None
            need_redraw = self.set_cross_hair_visible(False)
            if need_redraw:
                self.ax.figure.canvas.draw()
        else:
            self.set_cross_hair_visible(True)
            x, y = event.xdata, event.ydata
            index = min(np.searchsorted(self.x, x), len(self.x) - 1)
            if index == self._last_index:
                return  # still on the same data point. Nothing to do.
            self._last_index = index
            x = self.x[index]
            y = self.y[index]
            # update the line positions
            self.horizontal_line.set_ydata([y])
            self.vertical_line.set_xdata([x])
            self.text.set_text('x=%1.2f, y=%1.2f' % (x, y))
            self.ax.figure.canvas.draw()

if __name__ == "__main__":

    try:
        window.read(timeout=0)
        f = open('plc_readwrite.pckl', 'rb')
        data_stored = pickle.load(f)
        f.close()
        window['-IP-'].update(str(data_stored[0]))
        window['-TAG-'].update(str(data_stored[1]))
    except FileNotFoundError:
        pass

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            if trender is not None:
                trender.stop()
                window['Start Trend'].update('Start Trend')
                trender = None
            break
        elif event == 'Read':
            tag = values['-TAG-']
            ip = values['-IP-']
            json_read_enabled = values['-JSON_READ-']
            json_write_enabled = values['-JSON_WRITE-']
            json_read_file = values['-JSON_READ_FILE-']
            json_write_file = values['-JSON_WRITE_FILE-']

            # Convert tag input to a list
            formatted_tag = [t.strip() for t in tag.split(',')]

            if ip != '':
                if validate_ip(ip):
                    if json_read_enabled:
                        if json_read_file != '':
                            data = read_tag(str(ip), formatted_tag, store_to_json=True, json_name=str(json_read_file))
                        else:
                            data = read_tag(str(ip), formatted_tag, store_to_json=True)
                    else:
                        data = read_tag(str(ip), formatted_tag)

                    print(f'Timestamp: {datetime.datetime.now().strftime("%I:%M:%S %p")}')
                    
                    if type(data) is list:
                        for item in data:
                            for key, value in item.items():
                                print(f'Tag: {key} = {value}')
                    else:
                        for key, value in data.items():
                            print(f'Tag: {key} = {value}')

                    save_history(ip, tag)
                else:
                    print('Please enter a valid IP address')    
            else:
                print('Please enter an IP address')

        elif event == 'Write':
            tag = values['-TAG-']
            ip = values['-IP-']
            value = values['-VALUE-']
            json_read_enabled = values['-JSON_READ-']
            json_write_enabled = values['-JSON_WRITE-']
            json_read_file = values['-JSON_READ_FILE-']
            json_write_file = values['-JSON_WRITE_FILE-']

            if ip != '':
                if validate_ip(ip):

                    # if not gotten, get the list of tags and their types from the PLC
                    if not tag_list_retrieved:
                        tag_list = get_tags_from_json(ip)
                        tag_list_retrieved = True

                    if json_write_enabled:
                        results = write_tags_from_json(str(ip), str(json_write_file))
                    else:
                        results = write_tag(str(ip), str(tag), str(value))

                    if results:
                        if json_write_enabled:
                            print(f'{json_write_file} written to {ip} successfully')
                        else:
                            print(f'{value} written to {tag} successfully')

                        save_history(ip, tag)
                else:
                    print('Please enter a valid IP address')
            else:
                print('Please enter an IP address')
        elif event == '-JSON_READ-':
            window['-JSON_READ_FILE-'].update(disabled=not values['-JSON_READ-'])
            window['-JSON_READ_FILE_BROWSE-'].update(disabled=not values['-JSON_READ-'])
        elif event == '-JSON_WRITE-':
            window['-JSON_WRITE_FILE-'].update(disabled=not values['-JSON_WRITE-'])
            window['-JSON_WRITE_FILE_BROWSE-'].update(disabled=not values['-JSON_WRITE-'])
        elif event == 'Show Trend Plot':
            if trender is None:
                print('No data to display!')
            else:
                # if multiple results they will be dicts, plot each result in a separate subplot
                if type(trender.results[0]) == dict:

                    keys = [key for key in trender.results[0].keys()]

                    results_len = len(keys)

                    # create figure with subplots
                    fig, axs = plt.subplots(results_len, sharex=True, facecolor=(.18, .31, .31))

                    fig.suptitle(f'{values["-TAG-"]} Trend Results', color='w')
                    axis = []

                    for i in range(results_len):

                        dict_values = [value[keys[i]] for value in trender.results]

                        axs[i].plot(trender.timestamps, dict_values, 'wo', markersize=1)

                        axs[i].set_ylabel(keys[i], color='w')
                        axs[i].set_facecolor('k')
                        axs[i].tick_params(labelcolor='w', labelsize='medium', width=3)
                        axs[i].grid()

                    
                    fig.tight_layout()
                    fig.align_ylabels()

                else:
                    fig, ax = plt.subplots(facecolor=(.18, .31, .31))
                    plot, = ax.plot(trender.timestamps, trender.results, 'wo', markersize=2)
                    snap_cursor = SnappingCursor(ax, plot)
                    fig.canvas.mpl_connect('motion_notify_event', snap_cursor.on_mouse_move)
                    ax.set_xlabel('Time (msec)', color='w')
                    ax.set_ylabel('Value', color='w')
                    ax.set_title(f'{values["-TAG-"]} Trend Results', color='w')
                    ax.tick_params(labelcolor='w', labelsize='medium', width=3)
                    ax.set_facecolor('k')
                    ax.grid()

                    min_val = min(trender.results)
                    max_val = max(trender.results)

                    range_val = max_val - min_val

                    spacing_val = range_val/30

                    ax.set_ylim(min_val - spacing_val, max_val + spacing_val)

                plt.show()
        elif event == 'Start Monitor':
            if monitorer is None:
                try:
                    save_history(values['-IP-'], values['-TAG-'])
                    monitorer = TagMonitor(values['-IP-'], values['-TAG-'])
                    monitorer.run(window)
                    print(f'Monitoring tag {values["-TAG-"]}...')
                    window['Start Monitor'].update('Stop Monitor')
                except ValueError:
                    print('Please enter a valid IP address')
            else:
                monitorer.stop()
                window['Start Monitor'].update('Start Monitor')

                monitorer = None
        elif event == 'Start Trend':
            if trender is None:
                try:
                    try:
                        float(values['-RATE-'])
                        ok_rate = True
                    except ValueError:
                        ok_rate = False
                    if ok_rate:
                        save_history(values['-IP-'], values['-TAG-'])
                        interval = float(values['-RATE-'])
                        trender = TagTrender(values['-IP-'], values['-TAG-'], interval)
                        trender.run(window)
                        print('Trending...')
                        window['Start Trend'].update('Stop Trend')
                    else:
                        print('Invalid trend rate, value must be a number')
                except ValueError:
                    print('Please enter a valid IP address')
            else:
                trender.stop()
                window['Start Trend'].update('Start Trend')

                # TODO: Make work for multiple tags
                if values['-JSON_PLOT-']:

                    if trender.single_tag:
                        # if multiple results they will be dicts, plot each result in a separate subplot
                        if type(trender.results[0]) == dict:

                            keys = [key for key in trender.results[0].keys()]

                            results_len = len(keys)

                            # create figure with subplots
                            fig, axs = plt.subplots(results_len, sharex=True, facecolor=(.18, .31, .31))

                            fig.suptitle(f'{values["-TAG-"]} Trend Results', color='w')
                            axis = []

                            for i in range(results_len):

                                dict_values = [value[keys[i]] for value in trender.results]

                                axs[i].plot(trender.timestamps, dict_values, 'wo', markersize=1)

                                axs[i].set_ylabel(keys[i], color='w')
                                axs[i].set_facecolor('k')
                                axs[i].tick_params(labelcolor='w', labelsize='medium', width=3)
                                axs[i].grid()

                            
                            fig.tight_layout()
                            fig.align_ylabels()

                        else:
                            fig, ax = plt.subplots(facecolor=(.18, .31, .31))
                            plot, = ax.plot(trender.timestamps, trender.results, 'wo', markersize=2)
                            snap_cursor = SnappingCursor(ax, plot)
                            fig.canvas.mpl_connect('motion_notify_event', snap_cursor.on_mouse_move)
                            ax.set_xlabel('Time (msec)', color='w')
                            ax.set_ylabel('Value', color='w')
                            ax.set_title(f'{values["-TAG-"]} Trend Results', color='w')
                            ax.tick_params(labelcolor='w', labelsize='medium', width=3)
                            ax.set_facecolor('k')
                            ax.grid()

                            min_val = min(trender.results)
                            max_val = max(trender.results)

                            range_val = max_val - min_val

                            spacing_val = range_val/30

                            ax.set_ylim(min_val - spacing_val, max_val + spacing_val)

                        plt.show()
                    else:
                        print('\n****** Cannot plot multiple tags yet ******\n')

                if values['-JSON_READ-']:
                    if values['-JSON_READ_FILE-'] != '':
                        json_file = values['-JSON_READ_FILE-']
                    else:
                        json_file = f'{values["-TAG-"]}_trend_results.json'

                    if type(trender.results[0]) == dict:
                        # get keys from first dict in list
                        keys = ['Trend Duration']
                        keys = keys + [key for key in trender.results[0].keys()]
                    else:
                        keys = ['Trend Duration', 'Value']

                    if values['-JSON_READ-']:
                        if values['-JSON_READ_FILE-'] != '':
                            json_file = values['-JSON_READ_FILE-']
                        else:
                            json_file = f'{values["-TAG-"]}_trend_results.json'

                        with open(json_file, 'w') as f:

                            json_data = []

                            if trender.single_tag:
                                for i, val in enumerate(trender.results):
                                    data = {}

                                    td = trender.timestamps[i]
                                    data['Trend Duration'] = td
                                    data[values['-TAG-']] = val

                                    json_data.append(data)
                            else:
                                formatted_tag = [t.strip() for t in values['-TAG-'].split(',')]

                                # loop through the length of the trend results
                                for i in range(len(trender.results[0])):
                                    data = {}
                                    td = trender.timestamps[i]
                                    data['Trend Duration'] = td

                                    for y in range(len(trender.results)):
                                         data[formatted_tag[y]] = trender.results[y][i]

                                    json_data.append(data)                             

                            json.dump(json_data, f, indent=4)
                trender = None
        elif event == '-THREAD-':
            print(values['-THREAD-'])

window.close()