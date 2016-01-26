# Troubleshooting for Administrators

This section shows a few basic troubleshooting techniques in case of emergency

**FME Workbench-FME Server Connection**

If you are unable to connect from FME Workbench to FME Server then the following suggestions may be of help.

• Check if there is a firewall running on either your computer or the FME Server. If so, you must open port 7071 to use Direct Connection or port 80 (or 8080) to use the Web Connection.

• Restart the FME Server Services. On Windows, go to Start > Programs > FME Server > Windows Service > right-click Restart and select Run as administrator.

**Workspaces are Queued but not Run **

If a workspace appears in the FME Server queue, but is never executed, then it may be because no engines are running.

• Check the Web User Interface (Manage > Engine Management) to confirm engine status.
If no engines are available check licensing and update as necessary. Restart FME Server once a proper licence is in place.

**Workspaces Fail when Run**

If a workspace fails when it is being run, then the following suggestions may help 

• Run the workspace first on FME Desktop. If it does not work there, it will not work on FME Server.

• Check the FME log file using Manage > Jobs > Completed in the Web User Interface. This may help to explain why there is a problem.

• Commonly data paths cause problems when moving from a local Desktop machine to a Server environment. Check the dataset parameters (Reader and Writer) to ensure they are not referring to a local path that does not exist on the Server.

You may need to change the parameter to use the Resources dialog (Browse) and not a file path dialog (Specify Location).

• If you are trying to read data with a UNC path, ensure that the FME Server Windows Service is being run by a user with the proper domain access permissions.