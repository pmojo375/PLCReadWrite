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

# gets the result type of the tag read
def determine_type_read(result):
    if result:
        value = result.value

        return type(value)
    else:
        print('Tag read error!')

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


# This function checks the CSV and if it is the format that is generated by an array or not.
def check_csv(csv_file):
    df = pd.read_csv(csv_file)

    if 'index' not in df.columns:
        return False
    for col in df.columns:
        if '.' in col and col != 'index':
            return True
        
    return False


# This function converts the csv into the format that the write tag from csv function can handle.
def convert_csv(csv_file):
    df = pd.read_csv(csv_file, dtype=str).fillna('')

    new_rows = []

    for index, row in df.iterrows():
        idx = row['index']

        for col in df.columns:
            if col != 'index':
                parent, child = col.split('.', 1)

                tag_name = f'{parent}[{idx}].{child}'



                new_rows.append({'tag': tag_name, 'value': set_data_type(str(row[col]))})

    new_df = pd.DataFrame(new_rows)

    new_df.to_csv(csv_file, index=False)


# Converts the csv file tag value to the proper format
# Any value written in single or double quotes will be treated as a STRING
# Any value written as true or false in any case will be a BOOL
# Any value with a . will be treated as a REAL
# Any other numeric value be treated as an DINT/INT/SINT
def set_data_type(value):

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


# UNUSED
# This function will check if a tag type is already in the type list and if not it will add it
def check_type(ip, tag):
    try:
        data_type = type_list[tag]

        return data_type
    except:
        with LogixDriver(ip) as plc:
            result = plc.read(tag)

            data_type = result.type

            if data_type != None:

                type_list[tag] = data_type

                return data_type
            else:
                print(f'Tag: {tag} does not exist')


# UNUSED
# This function will convert the value to the correct type from the string
def convert_type(value, type):
    if type == 'DINT':
        return int(value)
    elif type == 'INT':
        return int(value)
    elif type == 'SINT':
        return int(value)
    elif type == 'BOOL':
        if value == '1' or value == 'True' or value == 'true':
            return True
        else:
            return False
    elif type == 'REAL':
        return float(value)
    else:
        return value


def trend_tag(ip, tag, **kwargs):
    store_to_csv = kwargs.get('store_to_csv', False)
    data = []
    last = 0
    last_read = time.time()
    with LogixDriver(ip) as plc:
        print('Ctrl + C Stops Trend')
        time.sleep(3)
        try:
            while True:
                if time.time() - last_read >= .047:
                    x = read_tag(ip, tag, csv_name = 'trend.csv', store_to_csv = False, plc = plc)
                    end_time = time.time()
                    print(int(x['Time2'])- last)
                    last = int(x['Time2'])
                    data.append([time.time() - last_read, int(x['Time2'])])
                    last_read = time.time()
                else:
                    pass

        except KeyboardInterrupt:
            print('Stopping Trend')
            with open('trend.csv', 'w', newline='') as f:
                
                # using csv.writer method from CSV package
                write = csv.writer(f)
                
                write.writerow(['time', 'tag'])
                write.writerows(data)


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
        return plc.write(tag, set_data_type(value))


# Writes tag value pairs read from a CSV file
# CSV file must have header of tag, value
# Bools are to be written as 1 (True) or 0 (False)
# UDTs must be written out in their full expanded names. For example: UDT.NestedUDT.TagName
def write_tags_from_csv(ip, csv_name):
    with LogixDriver(ip) as plc:

        data = []

        # opening the CSV file
        with open(csv_name, mode ='r') as file:
        
            # reading the CSV file
            csvFile = csv.reader(file)

            line_count = 0
            tags = []
            
            # displaying the contents of the CSV file
            for line in csvFile:
                # if not on header line
                if line_count != 0:
                    data.append((line[0], line[1]))

                line_count = line_count + 1

            for tag in data:
                value = set_data_type(tag[1])
                tags.append((tag[0], value))

            return plc.write(*tags)


# UNUSED
# This function will read tags from a CSV file and store them in a CSV file if desired
def read_tag_from_csv(ip, csv_name, **kwargs):
    store_to_csv = kwargs.get('store_to_csv', False)

    data = []

    # opening the CSV file
    with open(csv_name, mode ='r') as file:   
        
        # reading the CSV file
        csvFile = csv.reader(file)

        line = 0
        
        # displaying the contents of the CSV file
        for lines in csvFile:
            if line != 0:
                data.append(lines[0])

            line = line + 1

    for tag in data:
        read_tag(ip, tag, store_to_csv = store_to_csv)


# UNUSED
# Meant to seperate the processing from hte read_tag function and allow for a persistant connection to the PLC
def process_results(tag, results, **kwargs):

    store_to_csv = kwargs.get('store_to_csv', False)

    return_data = []
    tmp = []

    csv_name = kwargs.get('csv_name', 'tag_values.csv')

    # tag is an array and we are wanting more than one result in the array
    if '[' in tag and '{' in tag or '[' not in tag and '{' in tag:
        if '{' in tag and '[' not in tag:
            start = 0
            parent = re.search(".*(?=\{)", tag)[0]
        else:
            start = int(re.search("(?<=\[)(.*?)(?=\])", tag)[0])
            parent = re.search(".*(?=\[)", tag)[0]

        i = start
        num_tags = len(results.value)

        for t in results.value:

            tag_name = f'{parent}[{i}]'

            if store_to_csv:
                tmp = crawl_and_format(t, parent, {})
            else:
                tmp = crawl_and_format(t, tag_name, {})
                print(data)

            data = {'index': i}

            data.update(tmp)

            return_data.append(data)

            i = i + 1

        if store_to_csv:
            write_csv(csv_name, return_data)

        return return_data

    # tag is an array with one member
    elif '[' in tag:
        start = int(re.search("(?<=\[)(.*?)(?=\])", tag)[0])
        parent = re.search(".*(?=\[)", tag)[0]

        tag_name = f'{parent}[{start}]'

        data = crawl_and_format(results.value, tag_name, {})

        if store_to_csv:
            write_csv(csv_name, data)

        return data

    # tag is not an array
    else:
        data = crawl_and_format(results.value, results.tag, {})

        if store_to_csv:
            write_csv(csv_name, data)


# This function will read a tag value pair from the PLC
def read_tag(ip, tag, **kwargs):

    store_to_csv = kwargs.get('store_to_csv', False)

    return_data = []
    tmp = []

    csv_name = kwargs.get('csv_name', 'tag_values.csv')

    with LogixDriver(ip) as plc:

        ret = plc.read(tag)

        # tag is an array and we are wanting more than one result in the array
        if '[' in tag and '{' in tag or '[' not in tag and '{' in tag:
            if '{' in tag and '[' not in tag:
                start = 0
                parent = re.search(".*(?=\{)", tag)[0]
            else:
                start = int(re.search("(?<=\[)(.*?)(?=\])", tag)[0])
                parent = re.search(".*(?=\[)", tag)[0]

            i = start
            num_tags = len(ret.value)

            for t in ret.value:

                tag_name = f'{parent}[{i}]'

                if store_to_csv:
                    tmp = crawl_and_format(t, parent, {})
                else:
                    tmp = crawl_and_format(t, tag_name, {})

                data = {'index': i}

                data.update(tmp)

                return_data.append(data)

                i = i + 1

            if store_to_csv:
                write_csv(csv_name, return_data)

            return return_data

        # tag is an array with one member
        elif '[' in tag:
            start = int(re.search("(?<=\[)(.*?)(?=\])", tag)[0])
            parent = re.search(".*(?=\[)", tag)[0]

            tag_name = f'{parent}[{start}]'

            data = crawl_and_format(ret.value, tag_name, {})

            if store_to_csv:
                write_csv(csv_name, data)

            return data

        # tag is not an array
        else:
            data = crawl_and_format(ret.value, ret.tag, {})

            if store_to_csv:
                write_csv(csv_name, data)

            return data


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

    def read_tag(self, window):
        start_time = datetime.datetime.now()

        while not self.stop_event.is_set():
            result = self.plc.read(self.tag)
            
            window.write_event_value('-THREAD-', f'Timestamp: {datetime.datetime.now().strftime("%I:%M:%S:%f %p")}')
            window.write_event_value('-THREAD-', result.value)
            self.results.append(result.value)
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

csv_read_tooltip = ' When checked, the read tag results will be stored to a CSV file. A file \n name can be inputted or one will be auto generated if left empty. '
csv_write_tooltip = ' When checked, a CSV file containing tag/value pairs will be written to the PLC. \n The header must be "tag,value". A CSV filename must be specified to read from. '
value_tooltip = ' When writing a tag, the value must be in the correct format. \n For example, a BOOL must be written as 1 (True) or 0 (False). \n UDTs must be written out in their full expanded names. \n For example: UDT.NestedUDT.TagName                     '
csv_plot_tooltip = ' When checked, a plot of the tag values will \n be displayed after the trend is stopped. '

header = [[sg.Text('IP Address'), sg.InputText(key='-IP-', size=15)],
          [sg.Frame('Tag', [[sg.InputText(key='-TAG-', size=40)]])]]

read_tab = [[sg.Frame('CSV', [[sg.CB('Write Results To CSV', tooltip=csv_read_tooltip, key='-CSV_READ-', enable_events=True)],
            [sg.FileBrowse('Browse', file_types=(('CSV Files', '*.csv'),), key='-CSV_READ_FILE_BROWSE-', disabled=True), sg.InputText(key='-CSV_READ_FILE-', disabled=True, size=31)]])],
            [sg.Frame('Trend Rate', [[sg.InputText(key='-RATE-', size=40)], [sg.CB('Show Trend Plot', tooltip=csv_plot_tooltip, key='-CSV_PLOT-', enable_events=True)]])],
            [sg.Column([[sg.Button('Read'), sg.Button('Start Monitor'), sg.Button('Cancel')]], justification='r')],
            [sg.Column([[sg.Button('Start Trend'), sg.Button('Show Trend Plot')]], justification='r')]]

write_tab = [[sg.Frame('CSV', [[sg.CB('Write From CSV', tooltip=csv_write_tooltip, key='-CSV_WRITE-', enable_events=True)],
             [sg.FileBrowse('Browse', file_types=(('CSV Files', '*.csv'),), key='-CSV_WRITE_FILE_BROWSE-', disabled=True), sg.InputText(key='-CSV_WRITE_FILE-', disabled=True, size=31)]])],
             [sg.Frame('Value', [[sg.InputText(tooltip=value_tooltip, key='-VALUE-', size=40)]])],
             [sg.Column([[sg.Button('Write'), sg.Button('Cancel')]], justification='r')]]

footer = [[sg.Frame('Results', [[sg.Output(size=(38, 10))]])]]

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
            csv_read_enabled = values['-CSV_READ-']
            csv_write_enabled = values['-CSV_WRITE-']
            csv_read_file = values['-CSV_READ_FILE-']
            csv_write_file = values['-CSV_WRITE_FILE-']

            # create a list of tags if there are multiple tags
            if ',' in tag:
                pattern = ",\s*"
                tag = re.split(pattern, tag)

            if ip != '':
                if validate_ip(ip):
                    if csv_read_enabled:
                        if csv_read_file != '':
                            data = read_tag(str(ip), str(tag), store_to_csv=True, csv_name=str(csv_read_file))
                        else:
                            data = read_tag(str(ip), str(tag), store_to_csv=True)
                    else:
                        data = read_tag(str(ip), str(tag))

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
            csv_read_enabled = values['-CSV_READ-']
            csv_write_enabled = values['-CSV_WRITE-']
            csv_read_file = values['-CSV_READ_FILE-']
            csv_write_file = values['-CSV_WRITE_FILE-']

            if ip != '':
                if validate_ip(ip):
                    if csv_write_enabled:

                        if check_csv(csv_write_file):
                            convert_csv(csv_write_file)
                        
                        results = write_tags_from_csv(str(ip), str(csv_write_file))
                    else:
                        results = write_tag(str(ip), str(tag), str(value))

                    if results:
                        print(f'{value} written to {tag} successfully')

                        save_history(ip, tag)
                else:
                    print('Please enter a valid IP address')
            else:
                print('Please enter an IP address')
        elif event == '-CSV_READ-':
            window['-CSV_READ_FILE-'].update(disabled=not values['-CSV_READ-'])
            window['-CSV_READ_FILE_BROWSE-'].update(disabled=not values['-CSV_READ-'])
        elif event == '-CSV_WRITE-':
            window['-CSV_WRITE_FILE-'].update(disabled=not values['-CSV_WRITE-'])
            window['-CSV_WRITE_FILE_BROWSE-'].update(disabled=not values['-CSV_WRITE-'])
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

                if values['-CSV_PLOT-']:
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

                if values['-CSV_READ-']:

                    if values['-CSV_READ_FILE-'] != '':
                        csvfile = values['-CSV_READ_FILE-']
                    else:
                        csvfile = f'{values["-TAG-"]}_trend_results.csv'

                    if type(trender.results[0]) == dict:
                        # get keys from first dict in list
                        keys = ['Trend Duration']
                        keys = keys + [key for key in trender.results[0].keys()]
                    else:
                        keys = ['Trend Duration', 'Value']

                    with open(csvfile, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(keys)
                        for i, val in enumerate(trender.results):
                            if type(val) == dict:
                                row = [trender.timestamps[i], ]
                                for key in keys[1:]:
                                    row.append(val[key])
                                writer.writerow(row)
                            else:
                                writer.writerow([trender.timestamps[i], val])

                trender = None
        elif event == '-THREAD-':
            print(values['-THREAD-'])

window.close()