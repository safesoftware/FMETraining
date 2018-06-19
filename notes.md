# Notes

## Updating Process
- Edit chapters.xlsx to reflect desired book structure
- Save as chapters.csv
- Edit edits.json to reflect desired edits (replacement or add includes)
- Run generateChapters.py in book directory

## Manual Steps for Updating
- Integration2LabDemonstration/2.26.IntegratedInspection.md has an added include (PlacingAnInspectorTransformer) that has to be updated manually from DesktopBasic2Transformation/2.11.DataInspectionFromWorkbench.md, as well as any images it links.
- generateChapters.py will successfully only download needed external sections, but currently if they already exist editing will be messed up. Basically need to generate from scratch to work.

## Improvements
- Combine chapters.xlsx with edits.json?
- Fix existing file issue with edits.py
- Better documentation of scripts
- Create functions in generateChapters.py
- Allow selection of branch with download
- Better handling of existing sections
- Command line choices
