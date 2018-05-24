# What's New #
This file documents major changes made to training materials in 2018

---

## FMEData ##
These changes are for the FMEData dataset that accompanies FME training
- Updated Community Map Geodatabase with new URLs for libraries (also extended field size)
- Updated libraries with more numeric information such as book count, circulation, user visits
- Updated parks with more numeric information such as tree count and visitor count
    + Data is randomly generated, not from an official source
    + Removed excess attributes from parks (NSStreet, EWStreet)
- Renamed Crime2011.csv to Crime.csv

---

## Desktop Advanced ##
These changes are for the FME Desktop Advanced Training Course.

### General ###
- All screenshots now used Curved rather than Straight connections
- Chapter reordering
- New Review Desktop Basic exercise in the Course Introduction

### Advanced Attribute Handling ###
- Moved from Chapter 4 to Chapter 1
- Updated screenshots to reflect changes to Function changes in Text and Arithmetic editors
- Added a small paragraph about null values in key/attribute joins
- Advanced exercise at the end of Exercise 4
- A fix in 2018.1 resolves an issue with a bad display in Exercise 2c (screenshot: https://www.screencast.com/t/ZnYXiTX69cn)
  - The issue appears to be just a display fault, and the exercise/workspace works correctly

### Advanced Workspace Design ###
- Renamed from Performance to Advanced Workspace Design
- Added section on Feature Caching 
- Added section on bookmarks with an emphasis on collapsable bookmarks for performance
- Condensed all entire performance section. 
    + General tips for performance added
    + Assessing Reader/Writer performance condensed into one section
    + Dropped False Reader/Writer section 
    + Focus on 64-bit for performance with minor notes on 32-bit
    + Condensed Transformer Performance section into one section
    + Condensed Reading/Writing databases into one section called Optimizing Databases
    + Moved Server and Cloud Performance before Parallel Processing
- Exercises 1-3 changed to reflect changes in performance, continuous scenario
    + Batch reading GeoTIFFs, raster clipping, remove raster no data, writing out to GeoTIFF. 
    + Exercise 1: Workspace design to introduce feature caching and bookmarks
    + Exercise 2: Interpreting the log file and rejection codes
    + Exercise 3: Raster handling and workspace optimization
- Added bookmarks to Exercises 4-5 to keep consistent with chapter
    + Exercise 4: Added tip about collapsing bookmarks and then deleting to remove all
- Added batch processing section using the WorkspaceRunner and Batch Deploy

### Advanced Reading/Writing ###
- Expanded connection type list for Web-Based Datasets
- Changed example from Google Drive to AutoCAD A360 connection 
- Condensed Generic Reader/Writer into one section (more of a server topic)
- New Exercise 1: moved to after web-based datasets
    + Introduces users to 3D and point clouds
    + Connect to FME Server for file storage using the FMEServerResourceConnector
- Exercise 2: create a .zip file as an output
- Exercise 3-5: Update screenshots for bookmarks being added when generating a workspace

### User Parameters ###
- Changed wording from Add Parameter to Create User Parameter
- Updated screenshots to reflect new attributes in Parks.tab
- Exercise 1: UserCompanyName parameter set in the ParameterFetcher, a new BuildNumber parameter added for FME_BUILD_NUM
- Exercise 2: Advanced workspace updated to include the use of bookmarks

### Custom Transformers ###
- Exercise 1-3: Screenshots and text now refer to the year when talking about each ExpressionEvaluator
- Exercise 4: New tip on how to display transformer version
- Exercise 5: Changed exercise to reflect 64-bit parallel processing
- Exercise 6: New looping in a custom transformer exercise 

-

### Course Wrap Up ###
- Updated screenshots of safe.com 
