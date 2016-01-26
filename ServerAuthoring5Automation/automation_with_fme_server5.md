# Automation with FME Server

Automation involves workspaces processing data without a user having to manually initiate the process.

**What is Automation?**

Automation is the ability for FME Server to run a workspace without any user intervention or initiation.

For example, a system administrator sets up a workspace to do a daily update of a corporate database from file-based field updates. The translation can either be set up to start at the same time every weekday, or in response to files being deposited in a folder; and can be set up to run a series of workspaces according to logic inside a control workspace.

These automations are handled in three ways: Scheduling, Automated Data Processing, and Workflow Management.

**Scheduling**

Scheduling is the ability to initiate a workspace based on a particular time and/or date.

Schedules can be very simple – for example a one-off translation at a set date/time – or can be more complex and involve setting regular repetition, job priorities, and selection of a particular engine.

**Automated Data Processing**

Automated Data Processing is simply starting a workspace in response to an event.

For example, a workspace might be started in response to an email from an administrator, or by connecting FME Server to a cloud automation service such as IFTTT or Zapier.

**Workflow Management**

Workflow Management is the ability to create a branched translation, where a control workspace automatically determines other workspaces to run based on a set of inbuilt logic.
