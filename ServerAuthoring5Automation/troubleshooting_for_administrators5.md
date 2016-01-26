# Troubleshooting for Administrators

This section shows a few basic troubleshooting techniques in case of emergency

A Scheduled Workspace Fails to Run

If a scheduled workspace appears to have not been run at the expected time, then the following suggestions may be of help.

• Ensure an engine is available, and that the scheduled job is not in a queue.

• Check the date and time very carefully to ensure the correct values were entered

• Check the timezone is correct. The web interface operates on local timezone, which is not necessarily the same timezone as the server is physically located.

**A Notification Fails to Start a Workspace**

If a notification fails to start a workspace as expected then check the troubleshooting suggestions at the end of chapter 4 (Real-Time).

**The REST API Fails to Start a Workspace**

If a workspace fails to run using the REST API then check the troubleshooting suggestions at the end of chapter 2 (Running Workspaces).

**The FMEServerJobSubmitter Fails to Start a Workspace**

If a workspace fails to run using the FMEServerJobSubmitter transformer then check the troubleshooting suggestions at the end of chapter 2 (Running Workspaces).