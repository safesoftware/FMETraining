# FME Training Content Archive

This repository contains an archive of Safe Software's training content, including:

1. Archived course manuals (2016-2020) 
2. Content for the original FME Academy online learning platform (2020-2022)
3. Content from the [relaunched FME Academy](https://academy.safe.com/) online learning platform (2023-present)

This training material can be reused and adapted under our [Terms of Use](https://engage.safe.com/legal/terms-and-conditions/fme-training/) and [License](LICENSE.md).

# FME Academy Content

Current FME Academy contentis available on the `main` branch. Past years' Academy content is archived in `fme-academy-YEAR` branches. The directory structure for 2024 forward contains:

- Folders by FME version
  - Within folders, learning paths
    - Within learning paths, courses
      - Within courses, lessons
        - Within lessons, the lesson content is stored in `index.html`. Some lessons have hotlinked images and some have images included in an `images` folder. We eventually hope to have all images saved in the repo.

For older FME Academy content, the directory structure contains:

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

# Reuse

Partners can adapt and reuse this content according to the [Terms of Use](https://engage.safe.com/legal/terms-and-conditions/fme-training/) and [License](LICENSE.md).

# Data

Training data is provided in the [FMEData repository](https://github.com/safesoftware/FMEData/). FME Academy workspaces and links point to an [S3-hosted version of the data](https://s3.amazonaws.com/FMEData/FMEData/index.html) where possible so that users do not have to download the entire FMEData repository to use the content. You can download archived ZIPs of older FME Data content from the [Training Archive](https://academy.safe.com/page/training-archive). These are also mirrored on S3 with the year in the URL, e.g., https://s3.amazonaws.com/FMEData/FMEData2023/index.html.

# Archived Training Manuals

Other branches contain annual release versions of archived training manuals built using [`gitbook`](https://www.npmjs.com/package/gitbook). All archived manuals are available online at https://s3.amazonaws.com/gitbook/index.html. Substituting `index.html` for `Course-Name.pdf` gives you the PDF, e.g. https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/index.html becomes https://s3.amazonaws.com/gitbook/Desktop-Basic-2019/Desktop-Basic-2019.pdf.

# Issues/Questions

Any issues or questions can be directed to train@safe.com or by opening a GitHub Issue.
