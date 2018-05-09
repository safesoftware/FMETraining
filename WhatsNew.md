# What's New #
This file documents major changes made to training materials in 2018

---

## FMEData ##
These changes are for the FMEData dataset that accompanies FME training

- Updated Community Map Geodatabase with new URLs for libraries (also extended field size)
- Updated libraries with more numeric information such as book count, circulation, user visits
- Updated parks with more numeric information such as tree count and visitor count
	- Data is randomly generated, not from an official source
	- Removed excess attributes from parks (NSStreet, EWStreet)
- Renamed Crime2011.csv to Crime.csv

---

## Desktop Basic ##
These changes are for the FME Desktop Basic Training Course.

### General ###
- FME version used for developing materials switched from 32-bit to 64-bit 
	- We suggest all training is now undertaken on 64-bit FME
- All screenshots now use Curved rather than Straight connections

 
### Data Translation Basics ###
- Added a new introductory exercise to get 'hands-on' earlier (open/run existing workspace)
- Compressed What is FME and FME Data Model into one section
- Compressed Introduction to Workbench and Workbench Components into one section
- Added information on Visual Preview/Data Inspection window into components sections
- Dropped the section on Translation Previews (see in chapter 3 under inspection)
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
- Exercise 2: Changed advanced task to be simply adding a bookmark to introduce Best Practice
- Exercise 7: Changed to use FeatureJoiner instead of FeatureMerger

### Workspace Design ###
- Completely new chapter.
- Changed Translation Components chapter to one on Workspace Design
- Chopped section on Dev/Testing/Acceptance/Production - more advanced than is required
- New exercises - generating Garbage Collection areas

### Practical Transformer Use ###
- Changed Top 25 transformers to Top 30. Switched table to two-columns reading top-bottom
- Removed AttributeRenamer and AttributeCopier from list of transformers that can set values
	- They can set values, but only in limited circumstances, not in general
- New AttributeManager ability to cut/copy/paste/duplicate rows 
- Mentioned new Union alias for the Junction transformer
- Renamed Attribute Joins to Key-Based Joins (and Spatial Joins to Spatially Based Joins)
- Added new FeatureJoiner to Key-Based Joins, keeping the FeatureMerger
- Added the InlineQuerier to Key-Based Joins
- A new exercise to add interaction at the start of the chapter
- Attribute Handling Exercise: Now uses Excel template (not XML)
	- Also uses FeatureJoiner not FeatureMerger

**May 2018**

- Added example workspaces for demonstrating content in manual (see FMEData2018\Workspaces\InstructorUse)
- Updated screenshots and examples in manual to be consistent with new example workspaces 

### Best Practice ###
- Correctly numbered Best Practice files as chapter 5
- Moved sections on Prototyping, Testing, etc to Workspace Design chapter
- Dropped sections on Templates, Reusing items, Workspace searching
- Removed references to Header Annotation, since it no longer exists
- Changed "Bookmarks for Sectioning" to "Bookmarks for Design" and included Collapsible Bookmarks
- Added a new section on Bookmarks for Performance (related to Feature Caching)
- Removed references to Magnet icon, since it no longer exists
- Removed Ms Analyst question about types of annotation
- Methodology section now divided by Maintenance and Performance, rather than Transformers/Formats
- Rewrote methodology sections to cover more information in a better way
- Merged the sections on Logging (options) and Interpreting the Log
- Dropped Timestamp interpretation (it's more of an advanced task)
- Rewrote most of the debugging section to concentrate on best debugging methodologies
- Exercises 1-3: Changed to Vancouver Walkability study


### Course Wrap Up ###
- Updated with new web site images
- Mentioned podcast episodes on the blog

