# FME Training Content

This repository contains Safe Software's training content, including archived course manuals (2016-2023) and content for the [FME Academy online learning platform](https://community.safe.com/s/academy).

## FME Academy Content

Current FME Academy content is available on the `main` branch. Past year's Academy content will be archived in `fme-academy-YEAR` branches. The directory structure contains:

- `badges`: PNG and SVG versions of the FME Academy badges and Learning Path icons
- `courses`: each folder is a separate course (each associated with a badge). These chunks of content take 30 minutes to 2 hours to complete. They roughly correspond to a chapter or major chapter section in the archived training manuals. Course folders contain:
  - Unit folders: each is named after their unit. A unit is 5-20 minutes of content covering a single skill. Some have Exercise sections. All have a Quiz. Unit folders contain:
    - `images`: a folder containing unit images
    - `content.html`: the course text and images
    - `evaluation.json`: a JSON format quiz
    - `toc.html`: an HTML snippet containing links to section headings
  - `labels\labels.yml`: a YAML file containing course metadata
  - `badge.png`: the course badge
  - `module.json`: a file describing the course structure including filters, unit order, and time estimates
- `Learning Paths`: each folder is a separate Learning Path. Learning Paths are learning paths that link together two or more courses. Courses can belong to more than one Learning Path. A Learning Path is roughly equivalent to an entire manual or several chapters in the archived training manuals. Each Learning Path folder contains:
  - `labels\labels.yml`: a YAML file containing Learning Path metadata
  - `icon.png`: the Learning Path icon
  - `Learning Path.json`: a file describing the Learning Path structure, including filters and course order

## Content By FME Version

This list of courses is presented with their FME version. It is also roughly in the order we recommend learning the content.

|           FME Academy Learning Path          |                             FME Academy Course                      | FME Version |
|:------------------------------------:|:-------------------------------------------------------------------:|-------------|
| N/A                                  | Welcome to the FME Academy                                          | N/A         |
| Integrate Data with the FME Platform | Why Data Integration?                                               | 2022.0      |
| Integrate Data with the FME Platform | Connect To Data                                                     | 2022.0      |
| Integrate Data with the FME Platform | Transform Data                                                      | 2022.0      |
| Integrate Data with the FME Platform | Automate Workflows                                                  | 2022.0      |
| Transform Attributes                 | Create and Modify Attributes                                        | 2022.0      |
| Transform Attributes                 | Filter Data                                                         | 2022.0      |
| Transform Attributes                 | Join Tables                                                         | 2022.0      |
| Transform Attributes                 | Use Conditional Values                                              | 2022.0      |
| Integrate Spatial Data               | Learn Spatial Data Concepts                                         | 2020.1      |
| Integrate Spatial Data               | Turn Coordinates into Geometry                                      | 2020.1      |
| Integrate Spatial Data               | Analyze Spatial Data                                                | 2020.1      |
| Use Data Integration Best Practices  | Document Your Workspace                                             | 2022.0      |
| Use Data Integration Best Practices  | Debug Workspaces                                                    | 2022.0      |
| Use Data Integration Best Practices  | Design Workspaces for Advanced Reading and Writing                  | 2022.0      |
| Use Data Integration Best Practices  | Visually Compare and Merge Workflows                                | 2022.0      |
| Use Data Integration Best Practices  | Design For Performance                                              | 2022.0      |
| Use Data Integration Best Practices  | Optimize Workspace Performance                                      | 2022.0      |
| Use Data Integration Best Practices  | Design Modular and Maintainable Workspaces with Custom Transformers | 2022.0      |
| Use Data Integration Best Practices  | Build a Shared Library of Custom Transformers                       | 2022.0      |
| Build Advanced Workflows             | Read From and Write To Multiple Locations                           | 2021.1      |
| Build Advanced Workflows             | Work with Multiple Data Models Using Lists                          | 2021.1      |
| Build Advanced Workflows             | Leverage Ordered Data                                               | 2021.1      |
| Build Advanced Workflows             | Improve Data Quality by Handling Null and Missing Values            | 2021.1      |
| Build Advanced Workflows             | Build a Shared Library of Custom Transformers                       | 2021.1      |
| Build Advanced Workflows             | Design Modular and Maintainable Workspaces with Custom Transformers | 2021.1      |
| Publish Workflows to the Web         | What is FME Server?                                                 | 2022.0      |
| Publish Workflows to the Web         | Publish Workflows to the Web                                        | 2022.0      |
| Create Data Integration Apps         | Build Basic Self-Serve Workflows                                    | 2022.0      |
| Create Data Integration Apps         | Manage FME Server Data and Connections                              | 2022.0      |
| Create Data Integration Apps         | Build Versatile Self-Serve Workflows                                | 2022.0      |
| Create Data Integration Apps         | Create No-Code Web Apps                                             | 2022.0      |
| Automate Data Integration Tasks      | Build Basic Automations                                             | 2022.0      |
| Automate Data Integration Tasks      | Build Versatile Automations                                         | 2022.0      |
| Automate Data Integration Tasks      | Connect Automations with Job Orchestration                          | 2022.0      |
| N/A                                  | View Data                                                           | 2020.1      |
| N/A                                  | Digital Plan Submission                                             | 2020.1      |

## Mapping Between Archived Manuals and Academy

We have now published Learning Paths for [FME Desktop Basic](https://safe.my.Learning Pathhead.com/en/content/safe/Learning Paths/fme-desktop-basic), [FME Desktop Advanced](https://safe.my.Learning Pathhead.com/en/content/safe/Learning Paths/fme-desktop-advanced), and [FME Server Authoring](https://safe.my.Learning Pathhead.com/en/content/safe/Learning Paths/fme-server-authoring). Basic and Authoring are complete; Advanced has most of the previous content, but some user parameter sections are only available in the context of the Authoring Learning Path.

## Reuse

Partners are free to adapt and reuse this content according to the [License](LICENSE.md).

## Data

Training data is provided in the [FMEData repository](https://github.com/safesoftware/FMEData/). FME Academy workspaces and links point to an [S3-hosted version of the data](https://s3.amazonaws.com/FMEData/FMEData/index.html) where possible so that users do not have to download the entire FMEData repository to use the content.

## Archived Training Manuals

Other branches contain annual release versions of archived training manuals built using [`gitbook`](https://www.npmjs.com/package/gitbook). All archived manuals are available online at https://s3.amazonaws.com/gitbook/index.html. Substituting `index.html` for `Course-Name.pdf` gives you the PDF, e.g. https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/index.html becomes https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/Desktop-Basic-2019.pdf.

## Issues/Questions

Any issues or questions can be directed to train@safe.com or through opening a GitHub Issue.
