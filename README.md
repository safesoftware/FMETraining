# Introduction to FME Desktop

## Overview

This course introduces the essential components and capabilities of FME through hands-on problem-solving exercises. It is a condensed version of the more in-depth [FME Desktop Basic training](https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/index.html) and is a great start to become an efficient user of FME.

Through this course, you will learn what FME is, how it works, how to accomplish basic data translation and transformation, and how to set up your FME workflows following best practices. By the end of the course, you will be ready to create workspaces or to take further training specific to your needs. Because a wide variety of industries use FME, this course is a general introduction to FME that will show how FME works with data regardless of format or structure.

The course covers:
- Format Translations
- Transformation Tools
- Common Workflows

## Learning Objectives

- Learn what FME Desktop is and what it can do for you
- Convert data from one format to another using FME Workbench
- View and inspect data using FME Data Inspector and Visual Preview
- Manipulate data structure and content with transformers
- Work with multiple datasets in a single workspace
- Apply best practices to workspaces

## Prerequisites

- None

## Training Resources

To complete this training, you need a licensed version of FME Desktop installed. You can request a [free trial](https://www.safe.com/fme/fme-desktop/trial-download/) or may be eligible for a [grant license](https://www.safe.com/free-fme-licenses/). The training material is produced using FME Desktop 2019.0, but many of the steps are applicable to older versions.

You can download the data [here](https://s3.amazonaws.com/FMEData/FMEData2019.zip). After downloading, extract the data to C:\FMEData2019.

If you wish to inspect the output data in a native application, you should download and install the free software [Google Earth Pro](https://www.google.com/earth/versions/), or [follow instructions for viewing KML files in Google Earth Pro in Google Chrome](https://support.google.com/earth/answer/7365595?co=GENIE.Platform%3DDesktop&hl=en).

## Current Status

The current status of this manual is: **READY FOR REVIEW**: this manual should **NOT** be used for training.

This manual applies to **FME2019.0**

The status of each unit is:

- Unit 1: Ready for review
- Unit 2: Ready for review
- Unit 3: Ready for review
- Unit 4: Ready for review
- FMEData: Complete

***NB:*** *Even for completed content, Safe Software Inc. assumes no responsibility for any errors in this document or their consequences, and reserves the right to make improvements and changes to this document without notice. See the full licensing agreement for further details.*

## Overlap with FME Desktop Basic Training

|Introduction|Basic|
|-|-|
|**Introduction**|-|
|Getting Started (20 minutes)|Similar skills as first half of [Data Translation Basics](https://github.com/safesoftware/FMETraining/tree/Desktop-Basic-2019/DesktopBasic1Basics)|
|What is FME?|[What is FME?](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.01.WhatIsFME.md)|
|FME Desktop Components|[FME Desktop Components](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.02.FMEDesktopComponents.md)|
|FME Workbench|[Introduction to FME Workbench](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.03.IntroductionToWorkbench.md)|
|Exercise 1.1|Similar skills as  [Exercise 1: Exploring FME](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.Exercise1.md)|
|Quiz|-|
|**Translations (30 minutes)**|Similar skills as second half of [Data Translation Basics](https://github.com/safesoftware/FMETraining/tree/Desktop-Basic-2019/DesktopBasic1Basics) and first half of [Data Transformation](https://github.com/safesoftware/FMETraining/tree/Desktop-Basic-2019/DesktopBasic2Transformation)|
|Generate Workspace|[Creating a Translation](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.05.CreatingATranslation.md)|
|Exercise 2.1|Similar skills as [Exercise 2: Basic Workspace Creation](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.Exercise2.md)|
|Inspecting Data|[FME Data Inspector](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.09.DataInspector.md)|
|Exercise 2.2|Similar skills as [Exercise 3: Basic Data Inspection](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.Exercise3.md)|
|Feature Caching|[Feature Caching](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic1Basics/1.13.FeatureCaching.md)|
|Exercise 2.3|-|
|Schema and Data Model|[Structural Transformation](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic2Transformation/2.02.StructuralTransformation.md)|
|Exercise 2.4|Similar skills as [Ex 1: Schema Editing ](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic2Transformation/2.Exercise1.md) and [Exercise 2: Structural Transformation](https://github.com/safesoftware/FMETraining/blob/Desktop-Basic-2019/DesktopBasic2Transformation/2.Exercise2.md)|
|Quiz|-|
|**Transformations (45 minutes)**|Similar skills as first third of [Practical Transformer Use](https://github.com/safesoftware/FMETraining/tree/Desktop-Basic-2019/DesktopBasic4Transformers)|
|Transformers|[Transformation with Transformers](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic2Transformation/2.05.TransformationWithTransformers.html)|
|Exercise 3.1|-|
|Locating Transformers|[Locating Transformers](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic4Transformers/4.01.LocatingTransformers.html) and children|
|Exercise 3.2|-|
|Common Transformations|[Most Valuable Transformers](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic4Transformers/4.04.MostValuableTransformers.html)|
|Exercise 3.3a|-|
|Exercise 3.3b|-|
|Quiz|-|
|**Workflows (30 minutes)**||
|The Workflow|[Transformers in Series](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic2Transformation/2.07.TransformersInSeries.html) and [Transformers in Parallel](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic2Transformation/2.09.TransformersInParallel.html)|
|Multiple Readers, Writers, and Feature Types|[Multiple Readers and Writers](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic3WorkspaceDesign/3.06.AddReadersWriters.html)|
|Exercise 4.1|-|
|Best Practice|[Annotating Workspaces](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic5BestPractice/5.02.AnnotatingWorkspaces.html) and [Bookmarks](https://safe-software.gitbooks.io/fme-desktop-basic-training-2018/content/DesktopBasic5BestPractice/5.03.Bookmarks.html)|
|Exercise 4.2a|-|
|Exercise 4.2b||-
|Quiz|-|
|Wrap-up|-|
