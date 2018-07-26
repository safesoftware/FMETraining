#!/usr/bin/python
# -*- coding: utf-8 -*-
# Edits existing content by inserting or replacing
# an include to edit or add content. Run after downloading markdown files with
# generateChapters.py.

import os
import time
import json

# Function to read edits from JSON and make them to Markdown files
def editBook(edit_file = "edits.json"):
    # Open json
    with open('edits.json', encoding='utf-8') as data_file:
        # Load json into data
        data = json.loads(data_file.read())
    # Iterate over sections to make edits
    for section in data:
        # Save attributes of edit as variable
        attr = data[section]
        # Open chapter to read
        with open(section, "r", encoding="utf8") as infile:
            # Open chapter to write
            with open(section + "_write.md", "w", encoding="utf8") as outfile:
                print("Editing " + section)
                # Iterate over md reading file
                for index, line in enumerate(infile, start=1):
                    # Iterate over edits by section
                    for edit in attr:
                        # Define edit variables
                        line_num = edit["line_num"]
                        type = edit["type"]
                        content = edit["content"]
                        # set deletion lines from content
                        if type == "delete":
                            if "-" in content:
                                del_start = int(content.split("-")[0])
                                del_end = int(content.split("-")[1])
                            else:
                                del_start = int(content)
                                del_end = int(content)
                        # Make edits if on an edited line
                        if (index == line_num or
                          (type == "delete" and
                          index >= del_start and
                          index <= del_end)):
                            # Insert an include
                            if type == "insert":
                                print("Add line " + str(index))
                                line = "\n{% include \"../includes/" + content + ".md\" %} \n\n"
                            # Replace w/ an include
                            elif type == "replace":
                                print("Replace line " + str(index))
                                line = "{% include \"../includes/" + content + ".md\" %} \n\n"
                            # Delete lines
                            elif type == "delete":
                                print("Delete line " + str(index))
                                line = ""
                        # Otherwise, don't edit the line
                        else:
                            print("Don't edit line " + str(index))
                        # Write the line with or w/o edits from above
                    outfile.write(line)
        print("Finished section, clean up temp files.")
        # Close files for reading/writing and delete temp files
        infile.close()
        outfile.close()
        os.remove(section)
        os.rename(section + "_write.md", section)

# editBook()
