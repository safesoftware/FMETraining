# For python 2.7

# import required modules
import os # lib for operating system operations
import shutil # lib for file copying

# define variables
# update bookpath if repo changes
bookpath = "https://raw.githubusercontent.com/safesoftware/FMETraining/"
branch = "Desktop-Basic-2018/" # update for current branch/version
coursename = "DesktopBasic"

# merge md files by folder
# get dir structure
dir = "C:\Users\swalker\Documents\GitHub\FMETraining"
for dirpath, dirnames, filenames in os.walk(dir):
# for folders starting with desktopbasic
    for foldername in [f for f in dirnames if f.startswith(coursename)]:
        with open('C:\Users\swalker\Documents\GitHub\FMETraining\\' + foldername + 'Merged.md', 'w') as outfile: # open write file
            for filename in [f for f in os.listdir(os.path.join(dir, foldername)) if f.endswith(".md")]: # isfile(join(dir, foldername, f)) # find md files in folders
                mdfile = os.path.join(dir, foldername, filename)
                with open(mdfile) as infile: # write merged md
                    outfile.write(infile.read() + "\n\n")

# copy images to one folder. currently doesn't make new folder properly so I did it manually
destination = "C:\Users\swalker\Documents\GitHub\FMETraining\Images"
for dirpath, dirnames, filenames in os.walk("./"):
    for filename in [f for f in filenames if f.endswith(".png")]:
        shutil.copy(os.path.join(dirpath, filename),destination)
