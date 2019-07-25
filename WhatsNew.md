# What's New #
This file documents major changes made to training materials in 2019

---

## FMEData ##
These changes are for the FMEData dataset that accompanies FME training

- Added various raster datasets to the Zoning folder, for nodata and palette examples
- Added an Owners field to the Excel address template in the Resources folder

---

## Desktop Advanced ##
These changes are for the FME Desktop Advanced Training Course.

### General ###
- The people of Interopolis (advice sections) have been replaced by the FME Lizard. 
- Q+A questions are now interactive in the HTML version of the manual
- The Q+A answer page is now removed, since the answers are supplied with the question
- Made updates for 2019.1 changes

### Advanced Attribute Handling ###
- Compressed exercise 2 (used to be three separate pieces) into a single set of instructions

### Advanced Workspace Design ###
- Removed the sections on Feature Caching, Partial Runs, and Bookmarks; as it is covered in basic training.
- Removed the Parallel Processing content because it no longer applies in 2019
- Restructured the Log File Interpretation section
- Changed log examples from screenshots to preformatted text, to make editing/localization easier
- Dropped all references to 32/64-bit differences, since 64-bit is pretty much the default now
- Moved definition of performance to first section. Removed "Performance and FME"
- Moved "Remove Unattached" function to section on Optimizing Readers
- Changed General Performance Tips to introduce the idea of Authoring vs Production
- New exercises 1-3 (4 is the same as before)
- Included information on Bulk Mode and the order of features from the Tester in bulk mode. Included in exercise too.
- Mentioned new Sorter capabilities for .1 (in ex3)

### Advanced Reading/Writing ###
- Changed "Zip Files" to "Compressed Files", since 2019 now supports other archived or compressed file formats
- Added info on new web services for 2019.1
- Changed examples that read from the City of Vancouver website, to a "City of Interopolis" site on S3.
- Changed exercise 1 to:
	- Simplify the scenario
	- Include reading (and doing a join with) a web-based dataset
	- Writing a zip file with the FeatureWriter
	- Reinforce the use of conditional values (from chapter 1)

### User Parameters ###
- None

### Custom Transformers ###
- Changed the section on "Schema" to "Input" because it is more about the input to parameters than schema
	- Rewrote this section to be clearer with a new example/analogy
- Expanded the Parallel Processing content because it is more relevant in 2019
- Created a new, more involved, exercise on Parallel Processing, again because it is more relevant in 2019
- Removed section on Custom Transformer licensing, since Hub packages make it less relevant
- Create a new, but less involved, exercise for looping. It should be easier, quicker, and more realistic.


***NOTE:*** *I strongly suspect a bug exists that can occur in the first two steps of exercise 3 for Custom Transformers (probably in step 2). Somehow the density results can end up being the same for 2001 and 2011. The only way I have found to resolve the problem is to close the workspace (without saving) and follow steps 1 and 2 again.*

### Course Wrap Up ###
- Changed the FME Knowledge Centre to the FME Community, with Q+A Forum changing to Forums 
