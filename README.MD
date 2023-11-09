PLC TAG UTILITY

PLC Tag Utility is designed to read, write, trend and monitor tags in Allen Bradley PLCs. It has a intuitive GUI and can interface with PLCs with very little latancy. It also has the ability to store the data read into a YAML file (basically a fancy CSV file that shows nested structures better than a CSV can) and can take tag/value pairs from a YAML file and write them too. The trend feature will read tags and display and, if enabled, store the data to a YAML file, at a given rate. The monitor feature reads the PLC and when a tag equals an inputted value, it logs the time and can read or write other tags using that event as a trigger. This too can be stored to a YAML file.

INTERFACE

The GUI uses a tabbed layout for the 4 features (read, write, trend and monitor) and has a common area to input the IP address and tag that will be read, written, trended or monitored. The right side of the window is where the results will be displayed. To faciliate faster communication, it is recommened to connect to the PLC with the connect button but it will still work without connecting first as the program will create a new connection for the function and close it afterwards when complete. If you do use the connect button, before closing the window, hit the same button which should now say disconnect to open up the connection. If you forget to, nothing bad will happen and it will eventually timeout on its own but if you do this too much you may have to wait to connect next time you use the utility.

TAG FORMATTING

When entering a tag into the tag input box, it is important to format the tag in the proper way.

For tags that are arrays you can specify the number of members in the array to be read and what member to start at. The number of members to read should be enclosed in curly brackets at the end of the tag (My_Array{x}), the member to start at is enclosed in square brackets (My_Array[x]) and combined they will indicate which member to start at and how many to read. If either are omitted in a tag that is an array, they defualt to start at the first member and read only 1 member so My_Array would default to My_Array[0]{1}.

If the tag is not an array there is nothing needed and you may simply input the tag name.

You also have the ability to enter more than one tag if you wish but you must seperate them by commas.

If you want to read a UDT you do not have to format the tag in any special way but if you only want to read one of the child tags in a UDT you can enter that just like you would use it in your logic and use dot notation (My_UDT.ChildTag).

VALUE FORMATTING WHEN WRITING

When writting tags, you will enter the tag or tags you wish to write to and then in the value input box you enter the values seperating them by commas if there are multiple tags to write to.

You can write to UDTs but must format the value in a specific way. It is recommended to read the UDT and have it save to a YAML file to manipulate and then write from that file as it is much simpler that way but if you insist on not going that direction you will have to format the value as python dictionaries. Python dictionaries are key/value pairs where the value can be another dictionary if there are nested UDTs in your parent UDT.

For example, if you have a UDT with 2 DINTs and a BOOL, your value you would enter would be {'Dint1': x, 'Dint2': x, 'Bool': True} and if that UDT was nested in another UDT with a DINT you would enter {'AntherDint': x, 'NestedUDT': {'Dint1': x, 'Dint2': x, 'Bool': True}}.

YAML

To store results to a YAML file or read a YAML file to write values, you need to check the box on the interface. Entering a file name is optional when storing results as it will default to tag_values.yaml but if you have values you have already read, it will overwrite them so use caution when omitting the file name.

When writing values from a YAML file, you can also leave the file name blank but it will default to writing from the tag_values.yaml file name. If that file doesnt exist it will fail.

When trending a tag with the YAML option enabled, the timestamp will be written along with the value read at the rate you set when starting the trend and when monitoring a tag with the option enabled, the duration since the monitoring was started or the last time the tag monitored was equal to the value you inputed will be written. If you have the option to read tags when the a monitor event occurs, the values of those tags will be stored to the file as well.

SPECIAL THANKS

This script relies heavily on the work of ottowayi's pycomm3 library to do all the communcations to and from the PLC.

This is only a GUI that wraps the functions in that library to my own functions so without it, this project would not be possible.

Take a look at their work here: https://github.com/ottowayi/pycomm3