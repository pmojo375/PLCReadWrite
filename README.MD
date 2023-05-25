This script pulls PLC tag data from an Allen Bradley PLC into a csv file.
It can also write from a CSV file if needed.

This script relies heavily on the work of ottowayi's pycomm3 library to do all the communcations to and from the PLC.
I only implemented additional features and wrapped the pycomm3 functions in my own.

Take a look at their work here: https://github.com/ottowayi/pycomm3

FUNCTIONS

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