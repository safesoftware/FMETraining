<!--Instructor Notes-->
<!--This exercise uses a basic amount of FME Workbench as a test for students-->
<!--If students have problems now, it is unlikely they will have much success at further exercises-->

<!--Exercise Section-->
<!--NB: In GitBook world we don't give a number to exercises-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Earthquake Processing</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Earthquakes (GeoJSON)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Create a workspace to read and process earthquake data and publish it to FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Setting security options in FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

</table>

---

You're a technical analyst in the GIS department of your local city. You have plenty of experience using FME Desktop, and your department is now investigating FME Server to evaluate its capabilities.

You've already created a workspace to read a feed of earthquake data and published it to FME Server. Now you want to make sure that other users have permission to run it. 


<br>**1) Connect to Server**
<br>Open the FME Server interface, either through the Web User Interface option on the start menu or directly in your web browser, and log in. Select Manage &gt; Administration &gt; Security from the menu.


<br>**2) Create User**
<br>Let’s create a new user account for a person who might make use of this workspace. Click on the Users tab and then on the New button:

![](./Images/Img1.60.Ex4.CreateNewUser.png)

When prompted, create a new user with the following parameters:

- **User Name:** WebGuest
- **Full Name:** Web Interface Account
- **Roles:** fmeguest
- **Password:** WebGuest1


<br>**3) Check Role Permissions**
<br>If this user is to have access to the web interface, we should check that in the security settings.

Click on the Role Policies tab and then choose the fmeguest role as the one to examine. At the very bottom of the list is a parameter for FME Server Web User Interface. It will be turned off by default. This means someone in this role could not possibly access the workspace through the web interface.

We could simply turn on that parameter - but then that would give every guest user the ability to access the interface, and this might not be a good idea. So, let's create a new role.


<br>**4) Create Role**
<br>Click the Role tab and select the checkbox for the fmeguest role. Click the Duplicate button to create a copy of it:

![](./Images/Img1.62.Ex4.DuplicateGuestRole.png)

Call this role EmergencyPreparedness. Remove the guest account from this role and click OK to create it.


<br>**5) Set Role Permissions**
<br>Now back in the Role Policies tab choose the EmergencyPreparedness role as the one to examine. 

Firstly check the option for Manage Repositories. This will let the user find workspaces and run them.

Next set the parameter for Web Interface access to yes:

![](./Images/Img1.61.Ex4.GuestWebInterfaceSetting.png) 

Also scroll up slightly and check the settings for the Training repository. This role needs to have full access to this repository, as shown:

![](./Images/Img1.63.Ex4.TrainingRepSecurity.png)

Click the Apply Changes button to save the changes you have made.


<br>**6) Test Role**
<br>Log out of the web interface (Admin &gt; Log Out) and then log in again as the new WebGuest account.

Click the Run option on the menu and run the earthquake workspace. 

---

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Miss Vector says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
If you don't see a Run option on the menu, you probably missed setting Manage Repositories = Yes in step 5.
</span>
</td>
</tr>
</table>

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
<ul><li>Create a new user and new role on an FME Server installation</li>
<li>Set permissions on an FME Server role</li>
<li>Test a newly created role/account to ensure it works correctly</li></ul>
</span>
</td>
</tr>
</table>


 
