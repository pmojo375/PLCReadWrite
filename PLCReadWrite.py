from pycomm3 import LogixDriver
import re
import pickle
import time
import csv
from ast import literal_eval
import PySimpleGUI as sg
import threading

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


def main():

    try:
        f = open('plc_readwrite.pckl', 'rb')
        data_stored = pickle.load(f)
        f.close()
        file_found = True
    except FileNotFoundError:
        file_found = False

    if file_found:
        ip = input(f'Please Input IP Address (Press Enter For {data_stored[0]}): ')
        tag = input(f'Please Input Tag (Press Enter For {data_stored[1]}): ')
    else:
        ip = input(f'Please Input IP Address: ')
        tag = input(f'Please Input Tag: ')

    if ip == '':
        ip = data_stored[0]

    if tag == '':
        tag = data_stored[1]

    f = open('plc_readwrite.pckl', 'wb')
    pickle.dump((ip, tag), f)
    f.close()
    write_tags_from_csv(str(ip), str(tag))
    #read_tag(str(ip), str(tag), store_to_csv=True, csv_name='tags.csv')


# This function will print all attributes of all data types
def find_attributes(ip):
    with LogixDriver(ip) as plc:
        pass
    for typ in plc.data_types:
        print(f'{typ} attributes: ', plc.data_types[typ]['attributes'])


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
        return plc.write(tag, convert_type(value, check_type(ip, tag)))
    
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

            line = 0
            
            # displaying the contents of the CSV file
            for lines in csvFile:
                if line != 0:
                    data.append((lines[0], lines[1]))

                line = line + 1

            tags = []

            for tag in data:
                value = convert_type(tag[1], check_type(ip, tag[0]))

                tags.append((tag[0], value))

            print(tags)
            
            return plc.write(*tags)


# This function will read a tag value pair from the PLC
def read_tag(ip, tag, **kwargs):

    store_to_csv = kwargs.get('store_to_csv', False)

    return_data = []
    tmp = []

    csv_name = kwargs.get('csv_name', 'tag_values.csv')

    # if plc object is supplied in function call dont open a new connection every time you read
    if 'plc' in kwargs:
        plc = kwargs.get('plc')

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

    # plc object not supplied in function call, open new connection
    else:
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


def save_history(ip, tag):
    if ip != '' and tag != '':
        f = open('plc_readwrite.pckl', 'wb')
        pickle.dump((ip, tag), f)
        f.close()

def validate_ip(ip):
    pattern = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    if pattern.match(ip):
        return True
    else:
        return False

# This function will read a tag value pair from the PLC at a set interval
class TagTrender:
    def __init__(self, ip, tag, interval=1):
        self.ip = ip
        self.tag = tag
        self.interval = interval
        self.plc = LogixDriver(self.ip)
        self.plc.open()
        self.stop_event = threading.Event()
        self.thread = None

    def read_tag(self, window):
        while not self.stop_event.is_set():
            result = self.plc.read(self.tag)
            window.write_event_value('-THREAD-', result.value)
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

'''
trender = TagTrender('192.168.1.229', 'zzzTimer.ACC', 0.5)

try:
    trender.run()
    input('Press Enter to stop')
finally:
    trender.stop()

'''
sg.theme("DarkBlue")

csv_tooltip = ' When enabled, the read button will write the results to a CSV and the \n write button will read tag/value pairs from a CSV to write. When writing \n from a CSV, the header must be "tag, value". A CSV filename must \n be specified when writing but can be auto generated when reading.'
value_tooltip = ' When writing a tag, the value must be in the correct format. \n For example, a BOOL must be written as 1 (True) or 0 (False). \n UDTs must be written out in their full expanded names. \n For example: UDT.NestedUDT.TagName                     '
layout = [[sg.Text('IP Address'), sg.InputText(key='-IP-', size=15)],
         [sg.Frame('CSV File', [[sg.CB('Enable CSV Read/Write', tooltip=csv_tooltip, key='-CSV_ENABLE-', enable_events=True)], [sg.FileBrowse('Browse', file_types=(('CSV Files', '*.csv'),), key='-CSV_FILE_BROWSE-', disabled=True), sg.InputText(key='-CSV_FILE-', disabled=True, size=31)]])],
         [sg.Frame('Tag', [[sg.InputText(key='-TAG-', size=40)]])],
         [sg.Frame('Value', [[sg.InputText(tooltip=value_tooltip, key='-VALUE-', size=40)]])],
         [sg.Frame('Results', [[sg.Output(size=(38, 5))]])],
         [sg.Column([[sg.Button('Read'), sg.Button('Write'), sg.Button('Start Trend'), sg.Button('Cancel')]], justification='r')]]


# Create the Window
window = sg.Window('PLC Tag Read/Write', layout, size=(300, 380))

trender = None

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
            csv_enable = values['-CSV_ENABLE-']
            csv_file = values['-CSV_FILE-']

            if ip != '':
                if validate_ip(ip):
                    if csv_enable:
                        if csv_file != '':
                            data = read_tag(str(ip), str(tag), store_to_csv=True, csv_name=str(csv_file))
                        else:
                            data = read_tag(str(ip), str(tag), store_to_csv=True)
                    else:
                        data = read_tag(str(ip), str(tag))
                    
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
            csv_enable = values['-CSV_ENABLE-']
            csv_file = values['-CSV_FILE-']

            if ip != '':
                if validate_ip(ip):
                    if csv_enable:
                        results = write_tags_from_csv(str(ip), str(csv_file))
                    else:
                        results = write_tag(str(ip), str(tag), str(value))

                    if results:
                        print(f'{value} written to {tag} successfully')

                        save_history(ip, tag)
                else:
                    print('Please enter a valid IP address')
            else:
                print('Please enter an IP address')
        elif event == '-CSV_ENABLE-':
            window['-CSV_FILE-'].update(disabled=not values['-CSV_ENABLE-'])
            window['-CSV_FILE_BROWSE-'].update(disabled=not values['-CSV_ENABLE-'])
        elif event == 'Start Trend':
            if trender is None:
                try:
                    interval = 1
                    trender = TagTrender(values['-IP-'], values['-TAG-'], interval)
                    trender.run(window)
                    print('Trending...')
                    save_history(ip, tag)
                    window['Start Trend'].update('Stop Trend')
                except ValueError:
                    print('Please enter a valid IP address')
            else:
                trender.stop()
                window['Start Trend'].update('Start Trend')
                trender = None
        elif event == '-THREAD-':
            print(values['-THREAD-'])


window.close()