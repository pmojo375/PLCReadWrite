import yaml
import csv

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
                (row['tag'], row['value']))
    return processed_data


def crawl_and_format(obj, name, data, start_index=0):
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
            data = crawl_and_format(value, f'{name}[{i + start_index}]', data)
    # obj is an elementary object
    else:
        data[f'{name}'] = f'{obj}'

    return data


def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(
                        item, f"{new_key}[{i}]", sep=sep).items())
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

