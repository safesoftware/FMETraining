# What's New #
This file documents major changes made to training materials in 2018

---

## FMEData ##
These changes are for the FMEData dataset that accompanies FME training

- Updated Community Map Geodatabase with new URLs for libraries (also extended field size)
- Updated libraries with more numeric information such as book count, circulation, user visits.
- Updated parks with more numeric information such as tree count and visitor count
	- Removed excess attributes from parks (NSStreet, EWStreet)

---

## Desktop Basic ##
These changes are for the FME Desktop Basic Training Course.

### General ###
- FME version used for developing materials switched from 32-bit to 64-bit 
	- We suggest all training is now undertaken on 64-bit FME

 
### Data Translation Basics ###
- Added a new introductory exercise to get 'hands-on' earlier (open/run existing workspace)
- Compressed What is FME and FME Data Model into one section
- Compressed Introduction to Workbench and Workbench Components into one section
- Added information on Visual Preview/Data Inspection window into components sections
- Dropped the section on Translation Previews (new caching mode renders unnecessary)
- Compressed Introduction to Data Inspector and Data Inspector Components into one section
- Changed Miscellaneous DI functionality section to purely focus on background maps
- Added sections on Reader/Writer parameters (moved here from the redesigned chapter 3)
- Exercise 2 (was 1) changed output format from DWG to GeoJSON (to get filled polygons and attributes in DI)
- Exercise 4 (was 3) completely redesigned to be more relevant. 
	- Introduces students to transformers
	- Includes reader/writer parameters

### Data Transformation ###
- Rewrote Structural Transformation to reinforce the nature of readers, writers, feature types
- Rewrote sections about transformation to reinforce tabular as being distinct (not just attrs for spatial)
- Added a table of different combinations and outcomes for coordinate system reprojection
- Exercise 1: Switched step 2 (now rename feature type) and 3 (now update attribute definitions)
- Exercise 1: Added change of data type for VisitorCount column (smallint to integer)

### Workspace Design ###
- Changed Translation Components chapter to one on Workspace Design


### Practical Transformer Use ###
- xxxx


### Best Practice ###
- Correctly numbered Best Practice as chapter 5
- Moved parts of Best Practice relating to design to Workspace Design chapter


### Course Wrap Up ###
- Updated with new web site images
- Mentioned podcast episodes on the blog

