from pycomm3 import LogixDriver
import re
import pickle
import time
import csv
from ast import literal_eval
import PySimpleGUI as sg

layout = [[sg.Text('IP Address'), sg.InputText(key='-IP-')],
         [sg.CB('CSV Mode', key='-CSV_ENABLE-'), sg.Text('CSV Filename'), sg.InputText(key='-CSV_FILENAME-')],
         [sg.Text('Tag'), sg.InputText(key='-TAG-')],
         [sg.Button('Read'), sg.Button('Write'), sg.Button('Cancel')]]

# Create the Window
window = sg.Window('PLC Tag Read/Write', layout)



def simplest_type(s):
    try:
        return literal_eval(s)
    except:
        return s
    
def crawl_and_format(obj, name, data):

    # obj is a dict
    if isinstance(obj, dict):
        # iterate though the dictionary
        for key, value in obj.items():
            # call function again while incrementing layer
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


def find_attributes(ip):
    with LogixDriver(ip) as plc:
        pass
    for typ in plc.data_types:
        print(f'{typ} attributes: ', plc.data_types[typ]['attributes'])

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

# determines if the data is a list or dict and writes to a csv file
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

# writes a value to a tag
def write_tag(ip, tag, value, **kwargs):
    with LogixDriver(ip) as plc:
        return plc.write((tag, simplest_type(value)))
    
# Writes tag value pairs read from a CSV file
# CSV file must have header of tag, value
# Since all values are read as strings, this function tries to guess what the type should be
# Any number will be converted into an int or float so strings of numbers will be converted
# Bools are to be written as 1 (True) or 0 (False)
# UDTs must be written out in their full expanded names. For example: UDT.NestedUDT.TagName
# Any situations where an infered type is incorrect, the write will be skipped for that tag
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
                tags.append((tag[0], simplest_type(tag[1])))

            print(tags)
            
            return plc.write(*tags)
        
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

if __name__ == "__main__":
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break

        if event == 'Read':
            tag = values['-TAG-']
            ip = values['-IP-']
            csv_enable = values['-CSV_ENABLE-']
            csv_file = values['-CSV_FILENAME-']

            data = read_tag(str(ip), str(tag), store_to_csv=csv_enable, csv_name=csv_file)
            
            print(f'Reading {tag} from PLC at IP {ip} with CSV mode set to {csv_enable}')

            results_active = True
            layout2 = [[sg.Text('Results')],
                    [sg.Text(data, key='-RESULTS-')]]
        
            results = sg.Window('Results', layout2)

        if results_active:
            ev2, vals2 = results.read(timeout=100)
            if ev2 == sg.WIN_CLOSED:
                results_active = False
                results.close()

window.close()
