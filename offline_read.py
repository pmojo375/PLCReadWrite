import json
import pickle

class Tag:
    def __init__(self, name, type, value, error=None):
        self.tag = name
        self.type = type
        self.value = value
        self.error = error

    def __bool__(self):
        return True


class LogixDriver():

    def __init__(self, ip):
        self.connected = False

        with open('tag_list.json') as f:
            self.tags_json = json.loads(f.read())

        with open('tag_objects.pkl', 'rb') as f:
            self.tag_objects = pickle.load(f)

        print(self.tag_objects['PartDataCarrier'].value)


    def read(self, *tags):

        tag_results = []
        
        for tag in tags:
            # remove [x] and {x} from tag name where x is a number
            if '[' in tag or '{' in tag:
                stripped_tag = tag.split('[')[0].split('{')[0]
            else:
                stripped_tag = tag

            if '{' in tag:
                # get the number between the { and }
                num_to_read = tag.split('{')[1].split('}')[0]
            else:
                num_to_read = 1
            if '[' in tag:
                # get the number between the [ and ]
                start_index = tag.split('[')[1].split(']')[0]
            else:
                start_index = 0
            
            if num_to_read == 1:
                tag_results.append(self.tag_objects[stripped_tag])
            else:
                values = []

                tag_data = self.tag_objects[stripped_tag]

                for i in range(int(num_to_read)):
                    values.append(tag_data.value)
                
                tag_data.value = values
                tag_results.append(tag_data)
                
        if len(tag_results) == 1:
            return tag_results[0]
        
        return tag_results

    def write(self, *tags):
        return True

    def close(self):
        self.connected = False

    def open(self):
        self.connected = True

    def get_plc_name(self):
        return "Logix"
