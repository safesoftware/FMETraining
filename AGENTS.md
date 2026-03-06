# AGENTS.md — Rules for AI Agents Working in This Repository

## Issue Tracking

Track issues in `ISSUES.md`. Use headers to indicate if issues are **Open**, **In Review**, or **Closed** (currently uses **Fixed**/**Won't Do**/**Future Work**). Number issues sequentially. Keep the file up-to-date when making changes — move issues between sections and add new ones as appropriate. Focus on issues listed under **Open** unless the user specifies otherwise.

## Critical Rules

1. **You are working in a sensitive environment. Do not attempt to commit files in the /data or /artifacts folder, and always use environment variables for credentials.**

2. **Never hardcode credentials or print API keys to stdout/logs.**
   The `OPENAI_API_KEY` and any other secrets must only be read from the `.env` file via `python-dotenv`. Never commit `.env`.

3. **The lesson index.html files are read-only inputs — never write to them.**
   HTML training content under version folders (e.g. `2025.0/`, `2024.1/`) is source content. Do not modify these files.

4. **Artifact files are run-specific.**
   Once a `manifest/changelog/recommendations` file is written for a `run_id`, do not overwrite it. The report (`report-{RUN_ID}.html`) may be regenerated via `--report-only`.

## Development Notes

- Python 3.11+ required
- Install dependencies: `pip install -r requirements.txt`
- Copy `.env.sample` to `.env` and fill in `OPENAI_API_KEY` before running
- Preview scope without API calls: `python pipeline.py --dry-run`
- Run steps 1 and 2 first to validate scope and Jira filtering before incurring API costs: `python pipeline.py --steps 1,2`
- Resume an interrupted run: `python pipeline.py --resume <RUN_ID>`

## Repository Structure

```
{version}/{learning_path}/{course}/{lesson}/index.html
```

- Version folders: top-level, e.g. `2025.0/`
- Learning paths: e.g. `fme-form-basic/`
- Courses: include version suffix in folder name, e.g. `Connect To Data 2025.0/`
- Lessons: contain `index.html` and `images/`
