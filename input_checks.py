import re


def check_if_tag_is_list(tag, tag_types):
    """
    Check if a given tag is a list based on its dimensions.

    Args:
        tag (str): The tag to check.
        tag_types (dict): A dictionary containing tag types and their dimensions.

    Returns:
        bool: True if the tag is a list, False otherwise.
    """
    if tag_types is not None:

        # strip out the brackets
        formatted_tag = re.sub(r"(\[\d+\])|(\{\d+\})", "", tag)

        if formatted_tag in tag_types:
            dimensions = tag_types[formatted_tag]['dimensions']
            if dimensions == [0, 0, 0]:
                return False
            elif dimensions[0] > 0 or dimensions[1] > 0 or dimensions[2] > 0:
                return True
            else:
                return False
        else:
            return False
    else:
        return False

# TODO: Check if the non-list tag has no [] or {} and if it does, return false


def check_tag_range(tag, tag_types):
    """
    Check if the given tag is within the range of a tag.

    Args:
        tag (str): The tag to be checked.
        tag_types (dict): A dictionary containing information about tag types.

    Returns:
        bool: True if the tag is within the range of a tag, False otherwise.
    """
    if tag_types is not None:
        # strip out the brackets
        formatted_tag = re.sub(r"(\[\d+\])|(\{\d+\})", "", tag)

        if formatted_tag in tag_types:
            dimensions = tag_types[formatted_tag]['dimensions']

            # if tag is a list
            if dimensions[0] > 0:

                # get the size of the tag inputted if it has {}
                if '{' in tag and '}' in tag:
                    list_size = int(tag[tag.find('{')+1:tag.find('}')])

                    # get the start position of the tag inputted if it has []
                    if '[' in tag and ']' in tag:
                        start_pos = int(tag[tag.find('[')+1:tag.find(']')])
                    else:
                        start_pos = 0
                else:
                    list_size = 1

                    # get the start position of the tag inputted if it has []
                    if '[' in tag and ']' in tag:
                        start_pos = int(tag[tag.find('[')+1:tag.find(']')])
                    else:
                        start_pos = 0

                if start_pos + list_size <= dimensions[0]:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False
    else:
        return False


def get_tag_length(tag):
    """
    Get the length of a tag.

    Args:
        tag (str): The tag to get the length of.

    Returns:
        int: The length of the tag. If the tag is enclosed in curly braces,
             the length is extracted from the tag. Otherwise, the length is 1.
    """
    if '{' in tag and '}' in tag:
        return int(tag[tag.find('{')+1:tag.find('}')])
    else:
        return 1


def get_tag_start_pos(tag):
    """
    Get the start position of the tag inputted if it has [].

    Parameters:
    tag (str): The tag input.

    Returns:
    int: The start position of the tag if it has [], otherwise 0.
    """
    if '[' in tag and ']' in tag:
        return int(tag[tag.find('[')+1:tag.find(']')])
    else:
        return 0


def get_tag_type(tag, tag_types):
    """
    Get the data type of a tag.

    Parameters:
    tag (str): The tag name.
    tag_types (dict): A dictionary containing tag names as keys and their corresponding data types as values.

    Returns:
    str or None: The data type of the tag if it exists in the tag_types dictionary, None otherwise.
    """
    formatted_tag = re.sub(r"(\[\d+\])|(\{\d+\})", "", tag)

    if tag_types is not None:
        if formatted_tag in tag_types:
            return tag_types[formatted_tag]['data_type']
        else:
            return None
    else:
        return None

# TODO: for lists, check the values in the list not the etire list


def check_value_type(tag, value, tag_types):
    """
    Check the type of a value based on the tag and tag types.

    Args:
        tag (str): The tag to check the value against.
        value (str): The value to be checked.
        tag_types (dict): A dictionary containing the data types and dimensions of tags.

    Returns:
        bool: True if the value matches the expected type, False otherwise.
    """
    formatted_tag = re.sub(r"(\[\d+\])|(\{\d+\})", "", tag)

    if tag_types is not None:
        if formatted_tag in tag_types:
            type = tag_types[formatted_tag]['data_type']
            dimensions = tag_types[formatted_tag]['dimensions']

        if dimensions[0] == 0:
            if type == 'BOOL':
                if value.lower() in ['true', 'false'] or value in ['1', '0']:
                    return True
                else:
                    return False
            elif type == 'STRING':
                return True
            elif type == 'DINT' or type == 'INT' or type == 'SINT':
                if value.isdigit():
                    return True
                else:
                    return False
            elif type == 'REAL':
                if value.isdigit() or value.count('.') == 1:
                    return True
                else:
                    return False
            else:
                try:
                    eval(value)
                    return True
                except:
                    return False
        else:
            try:
                eval(value)
                return True
            except:
                return False


def check_value_length(tag, value, tag_types):
    """
    Checks if the length of the value matches the expected length based on the tag type.

    Args:
        tag (str): The tag name.
        value (str): The value to be checked.
        tag_types (list): List of tag types.

    Returns:
        bool: True if the length matches, False otherwise.
    """
    formatted_tag = re.sub(r"(\[\d+\])|(\{\d+\})", "", tag)

    if tag_types is not None:
        if formatted_tag in tag_types:
            num_to_write = get_tag_length(tag)
            start_pos = get_tag_start_pos(tag)

            length = num_to_write - start_pos

            try:
                if length > 1:
                    eval_obj = eval(value)
                    if isinstance(eval_obj, list):
                        if len(eval_obj) == length:
                            return True
                        else:
                            return False
                    else:
                        return False
                else:
                    return True
            except:
                return False
