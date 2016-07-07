# What's New #
This file documents major changes made to training materials in 2016

---

## Desktop Basic ##
These changes are for the FME Desktop Basic Training Course.

### Data Translation Basics ###
- Split the "More Data Inspector Functionality" section into two parts
- Added information on 2016.1 updates to Data Inspector styling

### Data Transformation ###
- Transformer Ports: replaced Counter with 2DForcer as an example of single input/output port (as Counter got a rejected port in 2016.1)
- Made note of other transformers with new rejected ports in 2016.1

### Best Practice ###
- The data used for the "I love bridges" debugging exercise has been cleaned up so that it is in the correct position
- Includes a new exercise called "Design Patterns"
- Removed the way-too-simple exercise on templates
- Made note of transformers with new rejected ports in 2016.1
- Updated bookmark sections with new 2016.1 functionality
- Added information on output port reordering in 2016.1
- Added information on the new Junction transformer in 2016.1
- Added information on the ability to hide connections in 2016.1

### Translation Components ###
- All previous exercises have been replaced by new ones centred around a fundraising walk scenario. These use a new GPS trail dataset
- Made note of new design of Geodatabase (ArcObjects) parameters dialog in 2016.1

### Practical Transformer Use ###
- The wrapping-up exercise (HTML property report) has been dropped and the prior exercise (data joins with crime data) promoted to take its place
- The Attribute section has been restructured on a task-basis, rather than transformer-by-transformer. That structure better accommodates the new AttributeManager transformer 
- Noted Help window no longer automatically updates in 2016.1
- Noted difference between Tester Regex operations in 2016.0 and 2016.1
- Made note of transformers with new rejected ports in 2016.1

### General ###
- Exercises are now numbered 1,2,3,etc within their particular chapter. A name (rather than number) denotes the chapter. This is because chapter numbers do not match the numbers GitBook assigns
- Improved (I hope) exercise descriptions and scenarios
- There are many more Q+A questions, all of which have the answers as the final section of their particular chapter
- Removed the update date from the course introduction page, as it cannot be easily kept up-to-date
- Changed text/screenshot to reflect renaming from Community Answers to Q&A Forum 

---

## Desktop Advanced ##
These changes are for the FME Desktop Advanced Training Course.

### User Parameters ###
- Replaced 2015 exercise 1c (Simplifying Workspace) with a new exercise based on parameterizing the basic training Grounds Maintenance project workspace

### Performance ###
- Updated exercise from 2015 with a Cloner transformer to increase the amount of data being processed without increasing the size of the source dataset
- Added option to run Exercise 4 using a PostGIS database as the source dataset
- Changed (from 2015) one of the workspaces for the Parallel Processing exercise
- Made note of transformers with new rejected ports in 2016.1

### Custom Transformers ###
- Dropped (from 2015) the section/exercise on manual schema editing
- Changed (from 2015) the parallel processing exercise to something more realistic (in terms of technique)
- Made note of new options (Hide Connections/Connect Junctions) on Workbench context menu in 2016.1
- Made note of transformers with new rejected ports in 2016.1
- Made note of bug in 2016.1 (resolved in 2016.1.1) that prevented exercise 3 from working correctly
- Updated warning in exercise 5 to include not running it in Full Inspection mode (as well as debug mode)

### Advanced Reading/Writing ###
- Made note (in exercise 2) about fme_feature_type being exposed automatically for dynamic translations in 2016.1.1

### Advanced Attribute Handling ###
- Changed (from 2015) the first exercise on attribute/value construction
- Made note (in exercise 2) about ability to connect multiple objects using Quick Add in 2016.1.1

### General ###
- Exercises are now numbered 1,2,3,etc within their particular chapter. A name (rather than number) denotes the chapter. This is because chapter numbers do not match the numbers GitBook assigns
- Improved (I hope) exercise descriptions and scenarios
- There are many more Q+A questions, all of which have the answers as the final section of their particular chapter
- Removed the update date from the course introduction page, as it cannot be easily kept up-to-date
- Changed text/screenshot to reflect renaming from Community Answers to Q&A Forum 
- Ran all exercises to confirm correct operation in FME2016.1.1 (used build 16601)