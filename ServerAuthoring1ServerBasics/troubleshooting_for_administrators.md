# Troubleshooting for Administrators

This section shows a few basic troubleshooting techniques in case of emergency

**Web User Interface**

If you are unable to access the Web User Interface then the following suggestions may be of help.

• Confirm that FME Server is installed and running!
The easiest way to be sure is to restart FME Server using Start > Programs > FME Server > Windows Service > Restart

• Check whether FME Server was installed using an application server port other than 80. For example, if port 80 was already being using the installer might have used a different port; 8080 is most common.

To check, try entering the URL with this syntax http://<host>:<port>/fmeserver - for example http://localhost:8080/fmeserver