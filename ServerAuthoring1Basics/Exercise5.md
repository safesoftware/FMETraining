<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1.5</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Daily Database Updates: Sharing a Repository</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Firehalls (GML)<br>Neighborhoods (KML)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a workspace to read and process departmental data and publish it to FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Share a repository with another FME Server user</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

</table>

---
In the last exercise, you created a schedule to automatically run the workspace you created in Exercise 1 once a day. But what happens if something goes wrong with this workspace or it needs to be updated and you're not available to fix it? It would be a good idea to allow other FME Server Authors within your department to be able to edit and run this workspace.

Let's ensure that other users that are part of the FME Server Author role have access to this repository to run and modify the workspace.

<br>**1) Enable Author Account**
<br>In FME 2020, the default accounts of Author, User, and Guest are now disabled on installation for enhanced security. We will need to enable the Author account before we continue.

Browse to the login page of the FME Server interface, and log in using the administrator account (admin/FMElearnings).

Under the Admin section on the side menu bar, expand User Management, then click on Users.

![](./Images/Img1.238.Ex5.UsersMenu.png)

Select the Author user, then in the Actions drop-down select Enable. A green checkmark should appear for the Author user under status.

![](./Images/Img1.239.Ex5.EnableAuthor.png)

<br>**2) Log In to Author Account**
<br>Now open an Incognito or Private window in your browser and open another instance of FME Server. Log in using the credentials author/author


The first thing you'll notice is that the menu and functionality is more restricted for this account (notice the Admin section is now gone):

![](./Images/Img1.240.Ex5.AuthorMenu.png)

Also, if you try to run a workspace, you'll find that this account does not have access to the Training repository where the existing workspace resides:

![](./Images/Img1.241.Ex5.AuthorRepository.png)

<br>**3) Share Repository**
<br>Minimize the incognito/private browser window where you are logged in as Author, and return to the browser where you are logged in as Admin.

You have the full set of menu entries, expand Workspaces and click on Manage Workspaces on the side menu. Under the list of repositories, locate the Training repository. Click the Share icon to the right:

![](./Images/Img1.242.Ex5.ShareButton.png)

In the Sharing Options dialog, select fmeauthor as the role to share with, and allow them full access to the repository:

![](./Images/Img1.243.Ex5.ShareDialog.png)

By selecting the *fmeauthor* role (rather than the single *Author* account), we allow anyone who is tagged as an Author to access the workspace; and by allowing them full access to the repository, we allow them to run, download, and make edits to our workspace.

<br>**4) Check Sharing**
<br>Switch back to the incognito/private window with the Author account.

This time, you should have access to the Training repository. Click Run Workspace (or refresh the page), select your workspace in the Training repository and run it. Check the Jobs page, and you'll see one entry for the workspace when it was run as the Author. There is only one entry because the Author does not have the privileges required to view any other users' jobs:

![](./Images/Img1.244.Ex5.CompletedJobAuthor.png)


Switch back to the Admin browser. Now, in the Jobs > Completed page, you should be able to see both the administrator's jobs and the Author's jobs:

![](./Images/Img1.245.Ex5.MultiUserJobsList.png)

That's because the administrator account has the permission to view all jobs.

---

<!--Exercise Congratulations Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Share a repository in FME Server and tested to ensure it is available to the right users</li></ul>
</span>
</td>
</tr>
</table>
