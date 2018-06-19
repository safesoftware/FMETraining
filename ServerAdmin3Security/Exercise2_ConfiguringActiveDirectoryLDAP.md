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

While FME Server provides a means to control access to its components and items within by creating Users and Roles, your company has instructed you to connect FME Server to an existing Active Directory service. After this connection is completed, you will import existing users and groups and configure permissions.

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
Due to security requirements and restrictions it may not be possible to complete this exercise.<br>
Instead, please watch <a href="https://drive.google.com/a/safe.com/file/d/0B9i4bX_jniydaThpUGZqOF9JVkk/view?usp=sharing">this video demonstrating the exercise</a>.
<!-- ** SM: create a new video for this... ** -->
</span>
</td>
</tr>
</table>

---

<br>**1) Connect to FME Server**
<br>Open the FME Server web interface, either through the web interface option on the Windows Start Menu or directly in your web browser (http://localhost/fmeserver), and log in using the username and password *admin*.

Click *Security*, under the Admin heading on the left sidebar, and then select **Active Directory**.


<br>**2) Create Connection to Active Directory**
<br>By creating a new connection, you can incorporate your organization’s Active Directory users and groups into your FME Server security configuration.

To get started, select **New** to open the Create New Server Connection page.

Enter the following information:

- **Name:** FME Active Directory
- **Host:** dc.fme.com
- **Port:** 389
- **Domain Search User:** DC\Administrator
- **Domain Search Password:** dcAdmin2017

Click **OK** to save the new Active Directory connection. You will be returned to the Active Directory page. Wait for the Status to change from Yellow to Green, indicating that the connection is successful.


<br>**3) Import Users**
<br>Now that the connection is established, select the **Import Users** icon to add users from the Active Directory connection.

On the Browse Users page, type in *mvector* and press Enter. Select Miss Vector's user and click **Import**.

A notification will appear in the top right of the web browser window to indicate that the user was successfully imported.

Note: If Miss Vector belonged to any Active Directory groups, we could have instead imported that as an FME Server Role – and all users that are a member of would be imported automatically.


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
