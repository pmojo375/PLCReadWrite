PLC TAG UTILITY

PLC Tag Utility is designed to read, write, trend and monitor tags in Allen Bradley PLCs. It has a intuitive GUI and can interface with PLCs with very little latancy. It also has the ability to store the data read into a YAML file (basically a fancy CSV file that shows nested structures better than a CSV can) and can take tag/value pairs from a YAML file and write them too. The trend feature will read tags and display and, if enabled, store the data to a YAML file, at a given rate. The monitor feature reads the PLC and when a tag equals an inputted value, it logs the time and can read or write other tags using that event as a trigger. This too can be stored to a YAML file.

INTERFACE

The GUI uses a tabbed layout for the 4 features (read, write, trend and monitor) and has a common area to input the IP address and tag that will be read, written, trended or monitored. The right side of the window is where the results will be displayed. Before closing the window, hit the same button which should now say disconnect to close up the connection. If you forget to, nothing bad will happen and it will eventually timeout on its own but if you do this too much you may have to wait to connect next time you use the utility.

TAG FORMATTING

When entering a tag into the tag input box, it is important to format the tag in the proper way.

For tags that are arrays you can specify the number of members in the array to be read and what member to start at. The number of members to read should be enclosed in curly brackets at the end of the tag (My_Array{x}), the member to start at is enclosed in square brackets (My_Array[x]) and combined they will indicate which member to start at and how many to read. If either are omitted for a tag that is an array, they defualt to start at the first member and read only 1 member so My_Array would default to My_Array[0]{1}.

If the tag is not an array there is nothing needed and you may simply input the tag name.

You also have the ability to enter more than one tag if you wish but you must seperate them by commas. A better way to do this is to add the tag to the tag list in the read tab which allows you to have a set of tags read when you press the read list button.

If you want to read a UDT or AOI you do not have to format the tag in any special way but threre cannot be anything that doesn't have extrnal access enabled. If you only want to read one of the child tags in a UDT or AOI you can enter that just like you would use it in your logic and use dot notation (My_UDT.ChildTag).

VALUE FORMATTING WHEN WRITING

When writting tags, you will enter the tag you wish to write to and then in the write tab, you have to press the generate structure button. This performs a read on the tag to both ensure that it exists and to get the structure in the tree to edit with your new values. Without this, the formatting to write to any non-atomic tag would be difficult and very error prone.

YAML

To store results to a YAML file or read a YAML file to write values, you need to check the box on the interface. Entering a file name is optional when storing results as it will default to tag_values.yaml but if you have values you have already read, it will overwrite them so use caution when omitting the file name.

When writing values from a YAML file, you can also leave the file name blank but it will default to writing from the tag_values.yaml file name. If that file doesnt exist it will fail.

When trending a tag with the YAML option enabled, the timestamp will be written along with the value read at the rate you set when starting the trend and when monitoring a tag with the option enabled, the duration since the monitoring was started or the last time the tag monitored was equal to the value you inputed will be written. If you have the option to read tags when the a monitor event occurs, the values of those tags will be stored to the file as well.

SPECIAL THANKS

This script relies heavily on the work of ottowayi's pycomm3 library to do all the communcations to and from the PLC.

This is only a GUI that wraps the functions in that library to my own functions so without it, this project would not be possible.

Take a look at their work here: https://github.com/ottowayi/pycomm3