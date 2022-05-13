# FME Training Content

This repository contains Safe Software's training content, including archived course manuals (2016-2020) and content for the [FME Academy online learning platform](https://community.safe.com/s/academy).

## FME Academy Content

Current FME Academy content is available on the `main` branch. Past year's Academy content will be archived in `fme-academy-YEAR` branches. The directory structure contains:

- `badges`: PNG and SVG versions of the FME Academy badges and trail icons
- `modules`: each folder is a separate module (each associated with a badge). These chunks of content take 30 minutes to 2 hours to complete. They roughly correspond to a chapter or major chapter section in the archived training manuals. Module folders contain:
  - Unit folders: each is named after their unit. A unit is 5-20 minutes of content covering a single skill. Some have Exercise sections. All have a Quiz. Unit folders contain:
    - `images`: a folder containing unit images
    - `content.html`: the module text and images
    - `evaluation.json`: a JSON format quiz
    - `toc.html`: an HTML snippet containing links to section headings
  - `labels\labels.yml`: a YAML file containing module metadata
  - `badge.png`: the module badge
  - `module.json`: a file describing the module structure including filters, unit order, and time estimates
- `trails`: each folder is a separate trail. Trails are learning paths that link together two or more modules. Modules can belong to more than one trail. A trail is roughly equivalent to an entire manual or several chapters in the archived training manuals. Each trail folder contains:
  - `labels\labels.yml`: a YAML file containing trail metadata
  - `icon.png`: the trail icon
  - `trail.json`: a file describing the trail structure, including filters and module order

## Content By FME Version

This list of modules is presented with their FME version. It is also roughly in the order we recommend learning the content.

|           FME Academy Trail          |                             FME Academy Module                      | FME Version |
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
| Use Data Integration Best Practices  | Design Workspaces for Advanced Reading and Writing                  | 2021.0      |
| Use Data Integration Best Practices  | Visually Compare and Merge Workflows                                | 2022.0      |
| Use Data Integration Best Practices  | Design For Performance                                              | 2021.0      |
| Use Data Integration Best Practices  | Optimize Workspace Performance                                      | 2021.0      |
| Use Data Integration Best Practices  | Design Modular and Maintainable Workspaces with Custom Transformers | 2021.1      |
| Use Data Integration Best Practices  | Build a Shared Library of Custom Transformers                       | 2021.1      |
| Build Advanced Workflows             | Read From and Write To Multiple Locations                           | 2021.1      |
| Build Advanced Workflows             | Work with Multiple Data Models Using Lists                          | 2021.1      |
| Build Advanced Workflows             | Leverage Ordered Data                                               | 2021.1      |
| Build Advanced Workflows             | Improve Data Quality by Handling Null and Missing Values            | 2021.1      |
| Build Advanced Workflows             | Build a Shared Library of Custom Transformers                       | 2021.1      |
| Build Advanced Workflows             | Design Modular and Maintainable Workspaces with Custom Transformers | 2021.1      |
| Publish Workflows to the Web         | What is FME Server?                                                 | 2021.1      |
| Publish Workflows to the Web         | Publish Workflows to the Web                                        | 2021.1      |
| Create Data Integration Apps         | Build Basic Self-Serve Workflows                                    | 2021.1      |
| Create Data Integration Apps         | Build Versatile Self-Serve Workflows                                | 2021.1      |
| Create Data Integration Apps         | Manage FME Server Data and Connections                              | 2021.1      |
| Create Data Integration Apps         | Create No-Code Web Apps                                             | 2021.1      |
| Automate Data Integration Tasks      | Build Basic Automations                                             | 2021.1      |
| Automate Data Integration Tasks      | Build Versatile Automations                                         | 2021.1      |
| Automate Data Integration Tasks      | Connect Automations with Job Orchestration                          | 2021.1      |
| N/A                                  | View Data                                                           | 2020.1      |
| N/A                                  | Digital Plan Submission                                             | 2020.1      |

## Mapping Between Archived Manuals and Academy

We have now published trails for [FME Desktop Basic](https://safe.my.trailhead.com/en/content/safe/trails/fme-desktop-basic), [FME Desktop Advanced](https://safe.my.trailhead.com/en/content/safe/trails/fme-desktop-advanced), and [FME Server Authoring](https://safe.my.trailhead.com/en/content/safe/trails/fme-server-authoring). Basic and Authoring are complete; Advanced has most of the previous content, but some user parameter sections are only available in the context of the Authoring trail.

## Reuse

Partners are free to adapt and reuse this content according to the [License](LICENSE.md).

## Data

Training data is provided in the [FMEData repository](https://github.com/safesoftware/FMEData/). FME Academy workspaces and links point to an [S3-hosted version of the data](https://s3.amazonaws.com/FMEData/FMEData2021/index.html) where possible so that users do not have to download the entire FMEData repository to use the content.

## Archived Training Manuals

Other branches contain annual release versions of archived training manuals built using [`gitbook`](https://www.npmjs.com/package/gitbook). All archived manuals are available online at https://s3.amazonaws.com/gitbook/index.html. Substituting `index.html` for `Course-Name.pdf` gives you the PDF, e.g. https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/index.html becomes https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/Desktop-Basic-2019.pdf.

## Issues/Questions

Any issues or questions can be directed to train@safe.com or through opening a GitHub Issue.
