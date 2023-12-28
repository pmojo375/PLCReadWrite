import json
from offline_read import Tag

# Function to create a default value based on type
def default_value(data_type):
    if data_type in ["DINT", "SINT", "INT"]:
        return 0
    elif data_type == "BOOL":
        return False
    elif data_type == "REAL":
        return 0.0
    else:  # For other types
        return {}

# Recursive function to process struct tags
def process_struct_tags(internal_tags):
    result = {}
    for name, info in internal_tags.items():
        if not name.startswith('ZZZZZZZ'):
            if info['tag_type'] == 'atomic':
                result[name] = default_value(info['data_type'])
            elif info['tag_type'] == 'struct':
                result[name] = process_struct_tags(info['data_type']['internal_tags'])
    return result

# Main function to parse the JSON structure into tag objects
def parse_json_to_tags(json_data):
    tags = {}
    for tag_name, tag_info in json_data.items():
        if 'data_type' in tag_info and isinstance(tag_info['data_type'], dict):
            # It's a struct type
            struct_value = process_struct_tags(tag_info['data_type']['internal_tags'])
            tags[tag_name] = Tag(tag_name, 'struct', struct_value)
        else:
            # Atomic type
            tag_value = default_value(tag_info['data_type'])
            tags[tag_name] = Tag(tag_name, 'atomic', tag_value)
    return tags

    
with open('tag_list.json') as f:
    json_data = json.loads(f.read())

# Parse the JSON data
tag_objects = parse_json_to_tags(json_data)

import pickle
with open('tag_objects.pkl', 'wb') as f:
    pickle.dump(tag_objects, f)