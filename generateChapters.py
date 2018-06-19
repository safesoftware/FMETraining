#!/usr/bin/python
# -*- coding: utf-8 -*-
# Requires pandoc installed and added to path
# Might not work on Unix systems due to filepaths

# Import required modules
import os # lib for operating system operations
import csv # lib for reading csv
import re # regex
import wget # for downloading files
import bs4 # beautifulsoup4 for scraping KC
import subprocess # for calling pandoc from cmd
import edits # script for making edits to downloaded content

# Method to split camel case string to list
def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

# Method to replace all items in a dic [item, replace] in text
def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

# Define variables
# Update bookpath if repo changes
bookpath = "https://raw.githubusercontent.com/safesoftware/FMETraining/"
branch = "Desktop-Basic-2018/" # update for current branch/version

# Download md files and images from other books based on csv structure
# Open csv
with open('chapters.csv', 'r') as csvfile:
    # Skip header
    next(csvfile, None)
    # Define csv reader
    data = csv.reader(csvfile, delimiter=',')
    # Iterate on urls to generate chapters
    for row in data:
        # For now, skip sections not in KC
        if not (row[0] + row[9]):
            print("not")
            pass
        # Download process for KC articles
        elif row[9]:
            # Check if file already exists
            if not os.path.isfile(row[8]):
                read = row[8][:-3] + "_read.html"
                write = row[8][:-3] + ".html"
                # If not, download it from url
                wget.download(row[9], read)
            # Read downloaded HTML
            with open(read, "r", encoding="utf8") as html_read:
                html_write = open(write, "w", encoding="utf8")
                # Extract div with content of interest
                soup = bs4.BeautifulSoup(html_read, "html.parser")
                div = soup.find("div", {"class": "kbentry post row-fluid"})
                content = div.prettify().replace("=\"/storage/attachments/",
                                                 "=\"https://knowledge.safe.com/storage/attachments/")
                html_write.write(str(content))
            # Close files, delete temp files
            html_write.close()
            html_read.close()
            os.remove(read)
            # Use pandoc to convert to md
            subprocess.run("pandoc " + write + " --extract-media=" +
                           row[8].rsplit('/', 1)[-2]
                           + "/Images --strip-comments -f html-native_divs-native_spans -t markdown -o "
                           + write[:-5] + "_read.md",
                           check=True,
                           shell=True)
            # Open md files
            read = row[8][:-3] + "_read.md"
            write = row[8][:-3] + ".md"
            with open(read, "r", encoding="utf8") as md_read: #
                md_write = open(write, "w", encoding="utf8")
                # Extract div
                for line in md_read:
                    # MD file replacements (should improve this)
                    line = line.replace("![](" + row[5] + "/", "![](")
                    line = line.replace("###", "")
                    line = line.replace("Article created with FME Desktop 2018.0", "")
                    line = line.replace("[thub.nodes.view.add-new-comment](#)", "")
                    line = line.replace("***Note:** this video was created with FME version 2016.0. Some of the steps might be slightly different, but the overall process is the same. The instructions below are for 2018.0.*", "")
                    md_write.write(line)
            # Close files and delete them
            md_write.close()
            os.remove(read)
            md_read.close()
            os.remove(row[8][:-3] + ".html")
            print("KC")
        # Non-KC chapter download process
        else:
            # Check if directory exists, make it if not
            if not os.path.exists(row[5]):
                os.makedirs(row[5])
            if not os.path.exists(row[5] + "/Images"):
                os.makedirs(row[5] + "/Images")
            # Download MD file
            # Form url
            url = bookpath + branch + row[7]
            print("MD url is " + url)
            # Check if file already exists
            if not os.path.isfile(row[8]):
                print("Downloading " + url)
                # If not, download it
                wget.download(url, row[8])
            # Download images
            with open(row[8], encoding="utf8") as md_read:
                # Iterate on md file lines to look for image links
                for line in md_read:
                    # Look for markdown images by line
                    if "](./" in line:
                        # Grab image filename
                        imgsplit = line.strip()[6:-1].rsplit('/', 1)[-1]
                        # Form url
                        url = bookpath + branch + row[0] + "/Images/" + imgsplit
                        print("Image url is " + url)
                        # Check if file already exists
                        if not os.path.exists(row[5] + "/Images/" + imgsplit):
                            # If not, download it
                            print("Downloading image " + url)
                            wget.download(url, row[5] + "/Images/" + imgsplit)
                    # Look for HTML images by line (for images in tables)
                    elif "<img src=" in line:
                        # Grab image filename from HTML
                        imgsplit = ""
                        # Split by HTML tags <>
                        tags = re.split(r'(?<=>)(.+?)(?=<)', line.strip())
                        # Iterate over tags
                        for i in tags:
                            # If tag is an image tag
                            if "img src=" in i:
                                # Set imgsplit to the image tag
                                imgsplit = i
                        # Grab image file name and ending from image tag
                        imgsplit = imgsplit.split("\"")[1].split("/")[2]
                        # Form url
                        url = bookpath + branch + row[0] + "/Images/" + imgsplit
                        print("Image url is " + url)
                        # Check if file already exists
                        if not os.path.exists(row[5] + "/Images/" + imgsplit):
                            # If not, download it
                            print("Downloading image " + url)
                            wget.download(url, row[5] + "/Images/" + imgsplit)

# Generate summary.md to create book structure; could probably combine with above
# Open SUMMARY.md to write
summary = open("SUMMARY.md","w")
# Write summary title
summary.write("# Summary \n\n")
# Open CSV
with open('chapters.csv', 'r') as csvfile:
    # Skip header
    next(csvfile, None)
    # Define csvreader
    data = csv.reader(csvfile, delimiter=',')
    # Read rows in csv
    for row in data:
        # If an include not a section, don't add to summary
        if row[2] == "":
            pass
        else:
            # Camel case to proper title
            title = ' '.join(camel_case_split(row[6]))
            # Write link in summary with proper indentation
            summary.write(2*int(row[3])*" " + "* [" + title[5:-3] + "](" + row[8] + ")\n")

# Close summary.md
summary.close()

# Run edit book function from edits.py, which makes edits according to
# edits.json
edits.editBook()
