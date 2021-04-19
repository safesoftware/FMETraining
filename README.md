# FME Training Content

This repository contains Safe Software's training content, including archived course manuals (2016-2020) and content for the FME Academy online learning platform.

## FME Academy Content

Current Academy content is available on the `main` branch. Past year's Academy content will be archived in `fme-academy-YEAR` branches. The Academy content is stored as required by our platform, Salesforce myTrailhead. The directory structure contains:

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

## Reuse

Partners are free to adapt and reuse this content according to the [License](LICENSE.md).

## Data

Training data is provided in the [FMEData repository](https://github.com/safesoftware/FMEData/). The FME Academy content here links to an [S3-hosted version of the data](https://s3.amazonaws.com/FMEData/FMEData2021/index.html) where possible so that users do not have to download the entire FMEData repository to use the content.

## Archived Training Manuals

Other branches contain annual release versions of archived training manuals built using [`gitbook`](https://www.npmjs.com/package/gitbook). All archived manuals are available online at https://s3.amazonaws.com/gitbook/index.html. Substituting `index.html` for `Course-Name.pdf` gives you the PDF, e.g. https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/index.html becomes https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/Desktop-Basic-2019.pdf.

## Issues/Questions

Any issues or questions can be directed to train@safe.com or through opening a GitHub Issue.
