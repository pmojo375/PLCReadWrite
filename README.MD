This program is a GUI that allows you to read and write to an Allen Bradley PLC. It has the ability to read tags and write the results to a JSON file and write tags from data in a JSON file as well.

Additional work will be done to add and improve the features as time goes on.

This script relies heavily on the work of ottowayi's pycomm3 library to do all the communcations to and from the PLC.
I only implemented additional features and wrapped the pycomm3 functions in my own.

Take a look at their work here: https://github.com/ottowayi/pycomm3

When the GUI opens up you will have a few areas to input information:
  - IP Address: Enter the PLC IP address here.
  - Enable JSON Read/Write: Check this box to enable JSON functionality. When reading from the PLC while enabled, your results will output to a JSON file. When writing to the PLC, tags and values will be read from a JSON file and each tag will have its value written to it.
  - Browse: Click this to browse for your JSON file. When one is selected, its path will be written to the text box to the right of this button. You may also type a path driectly to the text box. Paths can be relative. For example, if running the script in a folder that also contains a tags.json file, you may just type "tags.json" in the text box.
  - Tag: When JSON read/write is disabled and you are writing to the PLC, this is the tag that will be written to. When reading, this will be the tag that you read reguardless of whether you have CSV read/write enabled or not.
  - Value: When you have JSON read/write disabled and you are writing to the PLC, this is the value you are writing. When reading this has no use and may be left empty reguardless if JSON read/write is on or not.
  - Results: This is where your results will be printed. It will tell you if there are any issues as well with the read/write or if any information was not entered or entered incorrectly.
  - Read: If everything is inputted correctly, this will read a tag from the PLC.
  - Write: If everthing is inputted correctly, this will write a tag/value pair to the PLC or read tag/value pairs from a CSV to write.
  - Cancel: Closes the window.
  - NEED TO UPDATE TO INCLUDE NEW FEATURES

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
    - "python -m pip install -r requirements.txt" (NEED TO UPDATE THIS FILE)
  - The libraries may take a minute to install
- Run Script
  - From the project directory, run the following command (without quotes):
    - python -m ./PLCReadWrite.py
  - You will then get a prompt to enter your IP address. After typing it out, press enter.
  - Then you will get a prompt to enter the tag you want to read.
    - Single tags can be entered as you would assume. If you want to read a specific array member add [x] to the end
    - If you want to read a whole array of size x, after the tag name type {x} where x is the number of elements to read
    - Press enter to run the script.
  - Data will be in a JSON file called "part_history.json"
- Repeat the last step as needed. The installing python step, virtual environment and installing libraries steps only need to be done on the first run
  - You will need to activate the venv though everytime unless it is still activated.