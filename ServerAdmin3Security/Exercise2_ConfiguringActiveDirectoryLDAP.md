<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Configuring FME Server for Active Directory (LDAP)</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Connect FME Server to an existing Active Directory service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Configuring Active Directory in FME Server, Importing Users and Groups</td>
</tr>

</table>

---
<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">This exercise is for demonstration purposes only</span>
</td>
</tr>
</table>

This lab requires an Windows domain controller to be present and available to connect to from the FME Server system.  The training environment being used today does not have access to a domain controller.  The following steps and video are presented as a guide for configuring the typical active directory to work with FME Server.  It does not cover all possible configurations that may be required for your particular active directory.

---


<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Due to security requirements and restrictions it is not possible to complete this exercise.<br>
Instead, please watch <a href="https://youtu.be/XzoCR-X5TKQ">this video demonstrating the exercise</a>.
</span>
</td>
</tr>
</table>

---

<br>**1) Connect to FME Server**
<br>Open the FME Server web interface, either through the web interface option on the Windows Start Menu or directly in your web browser http://**&lt;your fmeserver host&gt;**/fmeserver, and log in with an admin account.

Click *Security*, under the Admin heading on the left sidebar, and then select **Active Directory**.


<br>**2) Create Connection to Active Directory**
<br>By creating a new connection, you can incorporate your organization’s Active Directory users and groups into your FME Server security configuration.

To get started, select **New** to open the Create New Server Connection page.

Enter the following information:

- **Name:** FME Active Directory
- **Host:** dc.fme.com
- **Port:** 389
- **Search Account Name:** DC\Administrator
- **Search Account Password:** dcAdmin2017

Click **OK** to save the new Active Directory connection. You will be returned to the Active Directory page. Wait for the Status to change from Yellow to Green, indicating that the connection is successful.


<br>**3) Import Users**
<br>Now that the connection is established, select the **Import Users** icon to add users from the Active Directory connection.

On the Browse Users page, type in *mvector* and press Enter. Select Miss Vector's user and click **Import**.

A notification will appear in the top right of the web browser window to indicate that the user was successfully imported.

Note: If Miss Vector belonged to any Active Directory groups, we could have instead imported that as an FME Server Role – and all users that are a member of would be imported automatically.



<!--Tip Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP: Import Error</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
When importing users from Active Directory you may encounter this message.  
This is because a username of the same value already exists in the SYSTEM users.
<br>
<br><br><img src="./Images/3.215.Ex2.ImportUserError.png">
<br><br>It is recommended that you remove the SYSTEM user account, and reimport the Active Directory user.  
<br>This error can also occur if you are importing users from a second domain that contains
<br>a same named user as the first domain. In this case it will be necessary to provide a
<br>different username on this dialog to represent the user from the second domain.  
<br><strong>NOTE</strong>: FME Server creates an aliase for the imported usernames and this is linked to the
<br>user account in the Active Directory.
</span>
</td>
</tr>
</table>

---


<br>**4) Configure User Permissions**
<br>After the Active Directory user is imported to FME Server, you must configure the permissions.

Select Security &gt; **Users** under the Admin heading on the left sidebar of the FME Server web interface. Click on the **Miss Vector** user that was just created to open the Edit User page.

Click in the text box area for **Assigned Security Roles** and select **fmeauthor**. Notice all the inherited permissions from the fmeauthor Role that are now selected.

Select **OK** at the bottom to apply the changes.


<br>**5) Test the New User Account**
<br>Test that the import and assigning permissions was successful by logging into FME Server as Miss Vector.

Either logout of the admin account or open a new private browsing window, and login using the credentials below:

- **Username:** mvector
- **Password:** dcFME2017

---

<!--Exercise Congratulations Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-thumbs-o-up fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">CONGRATULATIONS!</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
By completing this exercise you have learned how to:
<br>
<ul><li>Connect FME Server to an existing Active Directory configuration</li>
<li>Import Users and Groups from Active Directory</li></ul>
</span>
</td>
</tr>
</table>
