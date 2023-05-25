This script pulls PLC tag data from an Allen Bradley PLC into a csv file.
It can also write from a CSV file if needed. A GUI is in the works to make the script more user friendly.

Additional work will be done to add and improve the features as time goes on.

This script relies heavily on the work of ottowayi's pycomm3 library to do all the communcations to and from the PLC.
I only implemented additional features and wrapped the pycomm3 functions in my own.

Take a look at their work here: https://github.com/ottowayi/pycomm3

FUNCTIONS

simplest_type
  - This function takes a string (read from CSVs in this context) and converts it to whatever type it appears to be. For example, it would convert a '1' to an int of 1.
    - Inputs:
      - s: STRING = The string that you want to convert the type of
    - Outputs:
      - ANY = The value in its infered type

find_atributes
  - This function gets a list of all the data types and lists out their attributes and prints them
    - Inputs:
      - ip: STRING = The PLCs IP address
    - Outputs:
      - NONE

trend_tag
  - This function trends a tag at a 50ms rate. The rate will vary but be somewhat close to the 50ms target. It can output to a CSV as well. Use CTRL + C to stop the trend.
    - Inputs:
      - ip: STRING = The PLCs IP address in string format
      - tag STRING = The tag you want to read. For arrays, put {x} at the end to read x elements.
      - store_to_csv: BOOL (optional) = When true the data is saved to a csv file.
    - Outputs:
      - NONE

write_csv
  - This is a helper function to write the results of a dictionary or list of dictionaries to a CSV.
    - Inputs:
      - csv_name: STRING = The name of the csv file that is going to be created.
      - data: DICT or LIST[DICT] = The data you are writing to the CSV.
    - Outputs
      - NONE

write_tag
  - This function writes to a tag. It is used to write to a single tag only. It cannot write to a UDT or complex type at the moment.
    - Inputs:
      - ip: STRING = The PLCs IP address in string format
      - tag STRING = The tag you want to write to. Must be a single tag. Arrays should be written as a single element and UDTs can only be written to at the element level.
      - value: STRING = The value to write. Bools will accept 1 for true and 0 for false and other data types will be converted to the type that makes the most sense. So a '1' will be an int and a '3.4' will be a float.
    - Outputs:
      - TAG = The pycomm3 tag structure result from the write call.

write_tags_from_csv
  - This function does the same as the write_tag function but reads the values and tags from a CSV file. The CSV file must have the header "tag, value". Bools will accept a 1 or 0 for true and false and ints and floats will be converted. This unfortunatly means you cannot write a '1' string to a string as it will be converted. UDTs must be expanded to their lowest elements and not written to as a whole. For example, if your UDT has two child elements, tag1 and tag2, it must be in the CSV as UDT.tag1 and UDT.tag2.
    - Inputs:
      - ip: STRING = The PLCs IP address in string format
      - csv_name: STRING = The name of the CSV file you want to read. Must be present in the folder containing the script.
    - Outputs:
      - LIST[TAG] = A list of the pycomm3 tag structure result from the write calls.

crawl_and_format
  - This function formats the output of a read tag into an easy to read format.
    - Inputs:
      - obj: ANY = This is the variable you want to format.
      - name STRING = The parent name of the tag you are formatting.
      - data: DICT = What the formatted data is appended to.
    - Outputs:
      - DICT = The formatted dictionary

read_tag
  - This function reads a plc tag and can store the results to a csv file.
    - Inputs:
      - ip: STRING = The PLCs IP address in string format
      - tag STRING = The tag you want to read. For arrays, put {x} at the end to read x elements.
      - store_to_csv: BOOL (optional) = When true the data is saved to a csv file.
      - csv_name: STRING (optional) = The name of the csv file you want to create (must add .csv to string). 
                                      Defaults to csv_file.csv.
      - plc: LogixDriver (optional) = The LogixDriver object from the pycomm3 library. Speeds things up if you are
                                      reading in a loop.
    - Outputs:
      - DICT = A dict with the tag values

INSTALLATION

- Install Python
  - Latest version is best
- Navigate to Directory
  - Using any terminal (powershell, cmd, etc.) navigate to the project folder this document is in
  - Can be done by using "CD" (without quotes) followed by the path
  - "./" (without quotes) indicates your current directory
  - Example: "CD ./Desktop/PLC/PLCReadWrite"
- Create Virtual Environment
  - While withing the project folder, create your virtual environment with the following command (without quotes):
    - "python -m venv ./venv"
- Activate Virtual Enviroment
  - If you are in the same folder still fun the following command (without quotes):
    - "./venv/scripts/activate.ps1"
  - If all went well you will see (venv) on the left of your prompt
  - When you are done you can deactivate the virtual enviroment by running the command deactivate
- Install Libraries
  - In the directory, run the following (without quotes):
    - "python -m pip install -r requirements.txt"
  - The libraries may take a minute to install
- Run Script
  - From the project directory, run the following command (without quotes):
    - python -m ./PLCReadWrite.py
  - You will then get a prompt to enter your IP address. After typing it out, press enter.
  - Then you will get a prompt to enter the tag you want to read.
    - Single tags can be entered as you would assume. If you want to read a specific array member add [x] to the end
    - If you want to read a whole array of size x, after the tag name type {x} where x is the number of elements to read
    - Press enter to run the script.
  - Data will be in a CSV file called "part_history.csv"
- Repeat the last step as needed. The installing python step, virtual environment and installing libraries steps only need to be done on the first run
  - You will need to activate the venv though everytime unless it is still activated.

NOTES

If you are running the main function, it will default to save as a csv and the name of the file will be "tags.csv".