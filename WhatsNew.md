# What's New #
This file documents major changes made to training materials in 2017

---

## FMEData ##
These changes are for the FMEData dataset that accompanies FME training

- Added a dataset of Parking Meters (MapInfo TAB, FMEData\Data\Transportation\ParkingMeters)
- Building Footprints dataset converted from AutoCAD Map 3D to plain AutoCAD DWG
- Building Footprints user attributes cleaned up and renamed
- Resources folders all restructured
- Roads dataset updated to include information about one-way streets (instead of being a separate dataset)
- Added an "Event" field to the AddressSchema.xsd resource file
- Updated and cleaned up crime data

---

## Desktop Basic ##
These changes are for the FME Desktop Basic Training Course.

### General ###
- All operations, descriptions, and exercises are updated to use the new Parameter Editor dialog in FME Workbench 2017
- All 2016.1 additions have been moved from a separate box to the main content (where appropriate)
- All screenshots have been updated from FME2016 to FME2017
- All screenshots and wording have been updated from Windows 7 to Windows Server 2016 (equivalent to Windows 10)
 
### Data Translation Basics ###
- Added Parameter Editor window as a new Workbench component. Only show components that are there by default
- Added that F11 now won't close floating windows (only docked ones)
- Creating Translation/New Workspace/Running Workspace - all screenshots updated to show same translation (Geodatabase to GML)
- Data Inspector - all screenshots updated to show same dataset (Geodatabase Community Map)
- Changes to Table View window in Data Inspector (now need to select table to view it)
- Addition of clickable feature counts in the Data Inspector (plus pop-up tooltips) 
- Update to feature counts when a filter is applied
- Moved up section on using shift/control keys in Data Inspector to earlier in the manual
- Moved back the section on background maps to later in the manual

### Data Transformation ###
- Renumbered image filenames to 3 digits (eg Img2.001.xxxx.png)
- New layout of reader/writer feature type dialogs
- Parameter Editor Window for Transformers
- Exercise 4: Added a StringConcatenator in place of the in-dialog editor of the LabelPointReplacer (the logic being that one transformer is not much of a parallel stream, plus in-dialog editors come later)
- Exercise 6: Added the advanced task to use a Reprojector transformer instead of the Navigator coordinate system parameters

### Best Practice ###
- MOVED BEST PRACTICE TO FINAL CHAPTER IN MANUAL
- Renumbered image filenames to 3 digits (eg Img3.001.xxxx.png)
- Switched the order of User and Summary annotation
- More emphasis on bookmark properties dialog (introduced in 2016.1)
- General Style section now split into two parts:
	- Object Layout (includes newly restored Autolayout tool)
	- Connection Style (includes new connection style functionality)
	- Transformer renaming moved to Transformer Methodology
	- Workspace Properties moved to Projects (may move it again)
- Added back Autolayout information
- Reorganized chapter. Brought forward organizational parts into Methodology section
- Created a "prototyping" section
- Removed paragraph on "Single Feature Counts" as I can find no evidence this is still possible!
- Expanded on ways to get incorrect feature counts.
- Move "workspace searching" from Debugging to Methodology. Made it more generic.
- Renamed "Testing Isolated Sections" to "Workspace Testing" and made more generic.
- Added a section on debugging Writer output
- Exercise 1 now includes section on setting FME Options (inc new colour blindness theme)
- Exercise 1 now includes two completed workspaces, with different layouts for different connection styles
- Exercise 2 changed from fixing workspace to constructing it properly in the first place

### Translation Components ###
- Renumbered image filenames to 3 digits (eg Img4.001.xxxx.png)
- Updated workspaces section as Workspace Parameters now includes Workspace Properties
- Quick Add Readers and Writers
- The Advanced Browser is now renamed (Select Multiple Files/Folders)
- Added info on the ability to read data directly from a web connection
- Feature Type parameters dialog updated. Also parameters appear in Parameter Editor window
- Made a note of Unexpected Input not working for CAD files any more 
- Exercise 3: Switched Import and Delete actions to add a second table before deleting the first

### Practical Transformer Use ###
- Renumbered image filenames to 3 digits (eg Img5.001.xxxx.png)
- New transformer categorization (includes Q+A question updates)
- FME Store renamed to FME Hub
- Updated Top 25 list of transformers according to order on web site
- More consistent examples for Tester/TestFilter
- Q+A Question - 4 filters in Top25, not 3
- Renamed Joiner to DatabaseJoiner
- Updated exercises 1, 2, and 3 to be part of one larger project
- Dropped the advanced part of exercise 3
- Exercise 4 is reworked by having one-way streets flagged as an attribute in the roads data
- Exercise 4 also fixed a logic error in the ShortestPathFinder where distance wasn't factored into the result


### Course Wrap Up ###
- Updated screenshots for web sites and - of course - created a new challenge!

---

## Desktop Advanced ##
These changes are for the FME Desktop Advanced Training Course.

### General ###
- All operations, descriptions, and exercises are updated to use the new Parameter Editor dialog in FME Workbench 2017
- All 2016.1 additions have been moved from a separate box to the main content (where appropriate)
- All screenshots have been updated from FME2016 to FME2017
- All screenshots and wording have been updated from Windows 7 to Windows Server 2016 (equivalent to Windows 10)

### User Parameters ###
- Ability to Copy/Paste user parameters
- Text parameters seem to now work better with encoded characters - but the recommendation is still to use text-multiline
- Changed the example in Linking Parameters (from TextFile BOM parameter to PostGIS Features per Transaction)

### Performance ###
- xxxx

### Custom Transformers ###
- xxxx

### Advanced Reading/Writing ###
- xxxx

### Advanced Attribute Handling ###
- xxxx

---

## Server Authoring ##
These changes are for the FME Server Authoring Training Course.


### General ###
- All operations, descriptions, and exercises are updated to use the new Parameter Editor dialog in FME Workbench 2017
- All screenshots have been updated from Windows 7 to Windows Server 2016 (equivalent to Windows 10)

### xxxx ###
- xxxx

### xxxx ###
- xxxx

### xxxx ###
- xxxx

### xxxx ###
- xxxx

### xxxx ###
- xxxx

---

## Server Administration ##
This is a new course for 2017
