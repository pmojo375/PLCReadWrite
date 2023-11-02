from pycomm3 import LogixDriver
import re
import pickle
import csv
from ast import literal_eval
import PySimpleGUI as sg
from PySimpleGUI import Button, BUTTON_TYPE_READ_FORM, FILE_TYPES_ALL_FILES, theme_background_color, theme_button_color
import threading
import datetime
import matplotlib.pyplot as plt
import numpy as np
import yaml
import io
from base64 import b64encode
from PIL import Image, ImageDraw

tag_list_retrieved = False
tag_list = []
type_list = {}


def RoundedButton(button_text=' ', corner_radius=0, button_type=BUTTON_TYPE_READ_FORM, target=(None, None),
                  tooltip=None, file_types=FILE_TYPES_ALL_FILES, initial_folder=None, default_extension='',
                  disabled=False, change_submits=False, enable_events=False,
                  image_size=(None, None), image_subsample=None, border_width=0, size=(None, None),
                  auto_size_button=None, button_color=(sg.theme_background_color(), sg.theme_background_color()), disabled_button_color=None, highlight_colors=None, 
                  mouseover_colors=(None, None), use_ttk_buttons=None, font=None, bind_return_key=False, focus=False, 
                  pad=None, key=None, right_click_menu=None, expand_x=False, expand_y=False, visible=True, 
                  metadata=None):
    #Creates a PySimpleGUI button with rounded corners.
 
    # Calculate the size of the button if not provided
    if None in size:
        multi = 5
        size = (((len(button_text) if size[0] is None else size[0]) * 5 + 20) * multi,
                20 * multi if size[1] is None else size[1])
    
    # Set the button color if not provided
    if button_color is None:
        button_color = theme_button_color()
    
    # Create the button image
    btn_img = Image.new('RGBA', size, (0, 0, 0, 0))
    corner_radius = int(corner_radius/2*min(size))
    poly_coords = (
        (corner_radius, 0),
        (size[0] - corner_radius, 0),
        (size[0], corner_radius),
        (size[0], size[1] - corner_radius),
        (size[0] - corner_radius, size[1]),
        (corner_radius, size[1]),
        (0, size[1] - corner_radius),
        (0, corner_radius),
    )
    pie_coords = [
        [(size[0] - corner_radius * 2, size[1] - corner_radius * 2, size[0], size[1]),
         [0, 90]],
        [(0, size[1] - corner_radius * 2, corner_radius * 2, size[1]), [90, 180]],
        [(0, 0, corner_radius * 2, corner_radius * 2), [180, 270]],
        [(size[0] - corner_radius * 2, 0, size[0], corner_radius * 2), [270, 360]],
    ]
    brush = ImageDraw.Draw(btn_img)
    brush.polygon(poly_coords, button_color[1])
    for coord in pie_coords:
        brush.pieslice(coord[0], coord[1][0], coord[1][1], button_color[1])
    
    # Convert the button image to base64
    data = io.BytesIO()
    btn_img.thumbnail((size[0] // 3, size[1] // 3), resample=Image.LANCZOS)
    btn_img.save(data, format='png', quality=95)
    btn_img = b64encode(data.getvalue())
    
    # Create and return the button
    return Button(button_text=button_text, button_type=button_type, target=target, tooltip=tooltip,
                  file_types=file_types, initial_folder=initial_folder, default_extension=default_extension,
                  disabled=disabled, change_submits=change_submits, enable_events=enable_events,
                  image_data=btn_img, image_size=image_size,
                  image_subsample=image_subsample, border_width=border_width, size=size,
                  auto_size_button=auto_size_button, button_color=(sg.theme_background_color(), theme_background_color()),
                  disabled_button_color=disabled_button_color, highlight_colors=highlight_colors,
                  mouseover_colors=mouseover_colors, use_ttk_buttons=use_ttk_buttons, font=font,
                  bind_return_key=bind_return_key, focus=focus, pad=pad, key=key, right_click_menu=right_click_menu,
                  expand_x=expand_x, expand_y=expand_y, visible=visible, metadata=metadata)


# serializes the returned tag or list of tags to yaml format and writes to a file
def deserialize_from_yaml():
    with open('tag_values.yaml', 'r') as f:
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


# serializes the returned tag or list of tags to yaml format and writes to a file
def serialize_to_yaml(data):
    with open('tag_values.yaml', 'w') as f:

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


def get_tags_from_yaml(ip):
    """
    Gets the data types from the YAML data.

    Args:
        data (dict): The YAML data.

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


# This function will write a tag value pair to the PLC
def write_tag(ip, tag, value, **kwargs):
    with LogixDriver(ip) as plc:
        return plc.write(tag, set_data_type(value, tag))


# Writes tag value pairs read from a CSV file
def write_tags_from_yaml(ip, yaml_name):

    with LogixDriver(ip) as plc:
        tags = process_yaml_read(deserialize_from_yaml())

        return plc.write(*tags)


# UNUSED
# This function will read tags from a CSV file and store them in a CSV file if desired
def read_tag_from_yaml(ip, yaml_name, **kwargs):
    store_to_yaml = kwargs.get('store_to_yaml', False)

    data = []

    # opening the CSV file
    with open(yaml_name, mode ='r') as file:   
        
        # reading the CSV file
        csvFile = csv.reader(file)

        line = 0
        
        # displaying the contents of the CSV file
        for lines in csvFile:
            if line != 0:
                data.append(lines[0])

            line = line + 1

    for tag in data:
        read_tag(ip, tag, store_to_csv = store_to_yaml)


# This function will read a tag value pair from the PLC
def read_tag(ip, tags, **kwargs):

    store_to_yaml = kwargs.get('store_to_yaml', False)

    return_data = []
    data = {}

    yaml_name = kwargs.get('yaml_name', 'tag_values.csv')

    with LogixDriver(ip) as plc:

        ret = plc.read(*tags)

        if store_to_yaml:
            if isinstance(ret, list):
                serialize_to_yaml(ret)
            else:
                serialize_to_yaml([ret])

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
    def __init__(self, ip, tag, value, **kwargs):

        self.ip = ip
        self.value = value
        self.tag = tag
        self.tags_to_read = kwargs.get('tags_to_read', None)
        self.interval = .1
        self.plc = LogixDriver(self.ip)
        self.plc.open()
        self.stop_event = threading.Event()
        self.results = []
        self.timestamps = []
        self.hold = False
        self.thread = None
        self.first_event = True
        self.previous_timestamp = None

    def read_tag(self, window):

        while not self.stop_event.is_set():
            result = self.plc.read(self.tag)

            if result.value == self.value and self.hold == False:

                self.hold = True

                window.write_event_value('-THREAD-', f'\nTag = {self.value} at Timestamp: {datetime.datetime.now().strftime("%I:%M:%S:%f %p")}')

                if self.first_event:
                    self.previous_timestamp = datetime.datetime.now()
                    self.first_event = False
                    
                else:
                    time_since_last_event = (datetime.datetime.now() - self.previous_timestamp).total_seconds() * 1000
                    window.write_event_value('-THREAD-', f'Time since last event: {time_since_last_event} ms')
                    self.previous_timestamp = datetime.datetime.now()

                if self.tags_to_read is not None:
                    data = read_tag(self.ip, self.tags_to_read)

                    if type(data) is list:
                        for item in data:
                            for key, value in item.items():
                                print(f'Tag: {key} = {value}')
                    else:
                        for key, value in data.items():
                            print(f'Tag: {key} = {value}')
            
            if result.value != self.value:
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

            window.write_event_value('-THREAD-', f'\nTimestamp: {datetime.datetime.now().strftime("%I:%M:%S:%f %p")}')
            if self.single_tag:
                window.write_event_value('-THREAD-', f'{result[0].value}')
                self.results.append(result[0].value)
            else:
                for i, r in enumerate(result):            
                    window.write_event_value('-THREAD-', f'{formatted_tag[i]} = {r.value}')
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

def verify_tag(tag):
    if tag in tag_list:
        return True
    else:
        return False

sg.theme("DarkGray12")

yaml_read_tooltip = ' When checked, the read tag results will be stored to a YAML file. A file \n name can be inputted or one will be auto generated if left empty. '
yaml_write_tooltip = ' When checked, a YAML file will be written to the PLC. \n A YAML filename must be specified to read from. '
value_tooltip = ' When writing a tag, the value must be in the correct format. \n For example, a BOOL must be written as 1 (True) or 0 (False). \n UDTs must be written out in their full expanded names. \n For example: UDT.NestedUDT.TagName                     '
yaml_plot_tooltip = ' When checked, a plot of the tag values will \n be displayed after the trend is stopped. '

header = [[sg.Text('IP Address'), sg.InputText(key='-IP-', size=20)],
          [sg.Frame('Tag', [[sg.InputText(key='-TAG-', size=50)]])]]

read_tab = [[sg.Frame('YAML', [[sg.CB('Write Results To YAML', tooltip=yaml_read_tooltip, key='-YAML_READ-', enable_events=True)],
            [sg.FileBrowse('Browse', file_types=(('YAML Files', '*.yaml'),), key='-YAML_READ_FILE_BROWSE-', disabled=True), sg.InputText(key='-YAML_READ_FILE-', disabled=True, size=40)]])],
            [sg.Column([[RoundedButton('Read', .5, font="Calibri 11"), RoundedButton('Cancel', .5, font="Calibri 11")]], justification='r')]]

trend_tab = [[sg.Frame('YAML', [[sg.CB('Write Trend To YAML', tooltip=yaml_read_tooltip, key='-YAML_TREND-', enable_events=True)],
            [sg.FileBrowse('Browse', file_types=(('YAML Files', '*.yaml'),), key='-YAML_TREND_FILE_BROWSE-', disabled=True), sg.InputText(key='-YAML_TREND_FILE-', disabled=True, size=40)]])],
            [sg.Frame('Trend Rate', [[sg.InputText(key='-RATE-', size=50)], [sg.CB('Show Trend Plot', tooltip=yaml_plot_tooltip, key='-YAML_PLOT-', enable_events=True)]])],
            [sg.Frame('Value To Monitor', [[sg.InputText(key='-MONITOR_VALUE-', size=50)]])],
            [sg.Frame('Tag To Read', [[sg.InputText(key='-MONITOR_TAGS_TO_READ-', size=50)]])],
            [sg.Column([[RoundedButton('Start Monitor', .5, font="Calibri 11"), RoundedButton('Cancel', .5, font="Calibri 11")]], justification='r')],
            [sg.Column([[RoundedButton('Start Trend', .5, font="Calibri 11"), RoundedButton('Show Trend Plot', .5, font="Calibri 11", metadata=False)]], justification='r')]]

write_tab = [[sg.Frame('YAML', [[sg.CB('Write From YAML', tooltip=yaml_write_tooltip, key='-YAML_WRITE-', enable_events=True)],
             [sg.FileBrowse('Browse', file_types=(('YAML Files', '*.yaml'),), key='-YAML_WRITE_FILE_BROWSE-', disabled=True), sg.InputText(key='-YAML_WRITE_FILE-', disabled=True, size=40)]])],
             [sg.Frame('Value', [[sg.InputText(tooltip=value_tooltip, key='-VALUE-', size=50)]])],
             [sg.Column([[RoundedButton('Write', .5, font="Calibri 11"), RoundedButton('Cancel', .5, font="Calibri 11")]], justification='r')]]

footer = [[sg.Frame('Results', [[sg.Multiline(size=(50, 25), reroute_stdout=True)]])]]

tabs = [[header, sg.TabGroup([[
    sg.Tab('Read', read_tab), sg.Tab('Write', write_tab),  sg.Tab('Trend', trend_tab)]])], footer]
 
# Create the Window
window = sg.Window('PLC Tag Read/Write', tabs, size=(400, 700), icon='./icon.ico')

trender = None
monitorer = None

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
            yaml_read_enabled = values['-YAML_READ-']
            yaml_write_enabled = values['-YAML_WRITE-']
            yaml_read_file = values['-YAML_READ_FILE-']
            yaml_write_file = values['-YAML_WRITE_FILE-']

            # Convert tag input to a list
            formatted_tag = [t.strip() for t in tag.split(',')]

            tags_ok = True

            if ip != '':
                if validate_ip(ip):

                    # if not gotten, get the list of tags and their types from the PLC
                    if not tag_list_retrieved:
                        tag_list = get_tags_from_yaml(ip)
                        tag_list_retrieved = True

                    for tag in formatted_tag:
                        if not verify_tag(tag):
                            print(f'{tag} is not a valid tag')
                            tags_ok = False

                    if tags_ok:        

                        if yaml_read_enabled:
                            if yaml_read_file != '':
                                data = read_tag(str(ip), formatted_tag, store_to_yaml=True, yaml_name=str(yaml_read_file))
                            else:
                                data = read_tag(str(ip), formatted_tag, store_to_yaml=True)
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
                        print('One or more tags not in PLC, please fix and try again')
                else:
                    print('Please enter a valid IP address')    
            else:
                print('Please enter an IP address')
        elif event == 'Write':
            tag = values['-TAG-']
            ip = values['-IP-']
            value = values['-VALUE-']
            yaml_read_enabled = values['-YAML_READ-']
            yaml_write_enabled = values['-YAML_WRITE-']
            yaml_read_file = values['-YAML_READ_FILE-']
            yaml_write_file = values['-YAML_WRITE_FILE-']
            tags_ok = True

            if ip != '':
                if validate_ip(ip):

                    # if not gotten, get the list of tags and their types from the PLC
                    if not tag_list_retrieved:
                        tag_list = get_tags_from_yaml(ip)
                        tag_list_retrieved = True

                    if not verify_tag(tag):
                        print(f'{tag} is not a valid tag')
                        tags_ok = False

                    if tags_ok:        

                        if yaml_write_enabled:
                            results = write_tags_from_yaml(str(ip), str(yaml_write_file))
                        else:
                            results = write_tag(str(ip), str(tag), str(value))

                        if results:
                            if yaml_write_enabled:
                                print(f'{yaml_write_file} written to {ip} successfully')
                            else:
                                print(f'{value} written to {tag} successfully')

                            save_history(ip, tag)
                    else:
                        print('Tag not in PLC, please fix and try again')
                else:
                    print('Please enter a valid IP address')
            else:
                print('Please enter an IP address')
        elif event == '-YAML_READ-':
            window['-YAML_READ_FILE-'].update(disabled=not values['-YAML_READ-'])
            window['-YAML_READ_FILE_BROWSE-'].update(disabled=not values['-YAML_READ-'])
        elif event == '-YAML_WRITE-':
            window['-YAML_WRITE_FILE-'].update(disabled=not values['-YAML_WRITE-'])
            window['-YAML_WRITE_FILE_BROWSE-'].update(disabled=not values['-YAML_WRITE-'])
        elif event == 'Show Trend Plot':

            if trender is None or window['Show Trend Plot'].metadata == False:
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

                ip = values['-IP-']
                tag = values['-TAG-']
                tags_ok = True
                
                if ip != '':
                    if validate_ip(ip):
                        
                        # if not gotten, get the list of tags and their types from the PLC
                        if not tag_list_retrieved:
                            tag_list = get_tags_from_yaml(ip)
                            tag_list_retrieved = True
                        
                        if not verify_tag(tag):
                            print(f'{tag} is not a valid tag')
                            tags_ok = False

                        if tags_ok:

                            value_to_monitor = set_data_type(values['-MONITOR_VALUE-'], tag)
                            tags_to_read = values['-MONITOR_TAGS_TO_READ-']
                            
                            # Convert tag input to a list
                            formatted_tags_to_read = [t.strip() for t in tags_to_read.split(',')]

                            save_history(ip, tag)
                            if tags_to_read is not '':
                                monitorer = TagMonitor(ip, tag, value_to_monitor, tags_to_read=formatted_tags_to_read)
                            else:
                                monitorer = TagMonitor(ip, tag, value_to_monitor)
                            monitorer.run(window)
                            print(f'Monitoring tag {tag}...')
                            window['Start Monitor'].update('Stop Monitor')
                        else:
                            print('Tag not in PLC, please fix and try again')
                    else:
                        print('Please enter a valid IP address')    
                else:
                    print('Please enter an IP address')
            else:
                monitorer.stop()
                window['Start Monitor'].update('Start Monitor')

                monitorer = None
        elif event == 'Start Trend':
            if trender is None:

                tags_ok = True

                if ip != '':
                    if validate_ip(ip):

                        # if not gotten, get the list of tags and their types from the PLC
                        if not tag_list_retrieved:
                            tag_list = get_tags_from_yaml(ip)
                            tag_list_retrieved = True

                        if not verify_tag(tag):
                            print(f'{tag} is not a valid tag')
                            tags_ok = False

                        if tags_ok:  

                            window['Show Trend Plot'].metadata=True

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
                        else:
                            print('Tag not in PLC, please fix and try again')
                    else:
                        print('Please enter a valid IP address')    
                else:
                    print('Please enter an IP address')
            else:

                window['Show Trend Plot'].metadata=False

                trender.stop()
                window['Start Trend'].update('Start Trend')

                # TODO: Make work for multiple tags
                if values['-YAML_PLOT-']:

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

                if values['-YAML_TREND-']:
                    if values['-YAML_TREND_FILE-'] != '':
                        yaml_file = values['-YAML_TREND_FILE-']
                    else:
                        yaml_file = f'{values["-TAG-"]}_trend_results.yaml'

                    if type(trender.results[0]) == dict:
                        # get keys from first dict in list
                        keys = ['Trend Duration']
                        keys = keys + [key for key in trender.results[0].keys()]
                    else:
                        keys = ['Trend Duration', 'Value']

                    if values['-YAML_TREND-']:
                        if values['-YAML_TREND_FILE-'] != '':
                            yaml_file = values['-YAML_TREND_FILE-']
                        else:
                            yaml_file = f'{values["-TAG-"]}_trend_results.yaml'

                        with open(yaml_file, 'w') as f:

                            yaml_data = []

                            if trender.single_tag:
                                for i, val in enumerate(trender.results):
                                    data = {}

                                    td = trender.timestamps[i]
                                    data['Trend Duration'] = td
                                    data[values['-TAG-'].strip()] = val

                                    yaml_data.append(data)
                            else:
                                formatted_tag = [t.strip() for t in values['-TAG-'].split(',')]

                                # loop through the length of the trend results
                                for i in range(len(trender.results[0])):
                                    data = {}
                                    td = trender.timestamps[i]
                                    data['Trend Duration'] = td

                                    for y in range(len(trender.results)):
                                         data[formatted_tag[y]] = trender.results[y][i]

                                    yaml_data.append(data)                             

                            yaml.safe_dump(yaml_data, f, default_flow_style=False)
                trender = None
        elif event == '-THREAD-':
            print(values['-THREAD-'])

window.close()