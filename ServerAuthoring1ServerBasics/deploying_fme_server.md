# Deploying FME Server

FME Server can be deployed in a number of configurations 

**Platforms**

FME Server can be deployed on a variety of platforms:

• **Local Infrastructure (Physical Hardware)**
This is the traditional platform where you purchase FME Server and install it on your own hardware systems.

• **Infrastructure as a Service (Virtual Hardware)**
This is where you purchase FME Server and install it on virtual hardware that is provided as service by a company such as Amazon.

•** Platform as a Service (FME Cloud)**
This is where FME Server is delivered pre-installed on an Amazon virtual computer, with the whole platform provided by Safe Software on a pay-as-you-go basis.

**Distributed Systems**

A distributed system is when different components of a system are located on separate, networked, computers.

In a distributed environment, FME Engines run on a computer or computers that are separate from the FME Server host. Administrators can configure the FME Engines to register with a failover FME Server host, which acts as a backup if the primary FME Server host fails.

Other failover mechanisms include an additional core and license server.

Follow these steps to log into the FME Server web user interface and examine the available functionality.

**1) Connect to Server**

In your web browser, enter the address to your FME Server.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
When FME Server is installed on either physical or virtual hardware, the address is
http://<servername>/fmeserver
If you are using FME Cloud, then the address is:
http://<server name>.fmecloud.com/fmeserver
</span>
</td>
</tr>
</table>

This will open the web user interface login screen for the FME Server being used. Bookmark this web address, since you will use this link quite often.

**2) Log In to Server**

In the User Login dialog, enter a username and password for your FME Server account. A common username/password combination for a training installation is admin/admin

Click the Arrow button.

**3) Examine User Interface.**

Examine the user interface. This is your primary method for interacting with FME Server. Notice that the bottom-left corner shows which version and build of FME Server is being used by this instance:

**4) Examine Repositories**

Let's look first at the system's repositories. Click the Run Workspace button.

This will open a page that shows a list of the available FME Server workspace repositories. A repository is a method for storing and categorizing workspaces. It holds a number of workspaces in the same way that a folder holds a number of files.

In this case there will be a repository for Samples and one for Utilities.
Click on the Samples repository. A list of workspaces in that repository is shown. These are workspaces that have been loaded into FME Server and are available to run.

**5) Examine Jobs**

Now click Manage, then Jobs. This tool shows you a list of jobs that have been run on the system, as well as jobs that are currently queued or currently running.

Jobs and Repositories are the two items that you will use for basic FME Server use and administration.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says…</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“You might have noticed that the start menu has a tool for adding
sample workspaces; but if you used the express installation then
you don’t need to use this – everything is installed automatically.
</span>
</td>
</tr>
</table>