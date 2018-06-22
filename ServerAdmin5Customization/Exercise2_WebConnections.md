<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Adding a Web Connection</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Resources\ServerAdmin\DropboxWebConnection.xml</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Authenticate a web connection for FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">How to add and authenticate a web connection for Dropbox</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">None</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\ServerAdmin\Customization-Ex2-WebConnections-Complete.fmw</td>
</tr>

</table>

---

Your GIS department is working with several other organizations on one big project. It is a lot to organize, so whenever there are additional files to be shared, each organization drops the file into the shared Dropbox for easy access for all organization members. Your task is to configure FME Server to access the Dropbox.

---


<br>**1) Create a Workspace**
<br>You must first create a Dropbox web connection. The first step in creating this web connection is to have a workspace to run! Open FME Workbench and create a new Blank Workspace.

The **DropboxConnector** transformer can access a Dropbox account and perform Delete, Download, List, and Upload actions.

Add a **Creator** transformer and a **DropboxConnector** transformer to the workspace. Join the Creator to the DropboxConnector. Add a **Logger** transformer connected to the Output port of the DropboxConnector.

![](./Images/5.201.Ex1.WebConnectionsWorkbench.png)


<br>**2) Configure DropboxConnector and Create Web Connection**
<br>Select DropboxConnector and open the parameters dialog or view them via the Parameter Editor pane.

Change the *Dropbox Action* to **List**.

Then select the drop-down for *Dropbox Connection* and select **Add Web Connection...**. The Dropbox Connection dialog box opens.

Set the *Connection Name* to **DropboxWebConnection** and click **Authenticate...**.

![](./Images/5.202.Ex1.AuthenticateConnection.png)

This opens a new window with a direct, secure connection to Dropbox. Fill in the *Web Service Authentication* credentials as follows:

- **Email:** fmedropbox@gmail.com
- **Password:** *&lt;distributed_during_course&gt;*

...and then click **Sign in**.

Note: The above email and password should be used solely for this exercise. You can use *your own Dropbox account*, but for this course, we have provided an account to use.

Click **Allow** to allow FME to access the Dropbox account.

Your *DropboxConnector* parameters should now look like the following:

![](./Images/5.203.Ex1.DropboxConnectorParameters.png)

Click **OK** to apply the changes.


<br>**3) Run the Workspace**
<br>It is a best practice to first run the workspace in FME Desktop before uploading it to FME Server. If the workspace does not run in FME Desktop, then it will not run in FME Server!

Click **Run** to make sure the translation is successful. Now we are ready to publish the workspace to FME Server.


<br>**4) Publish to FME Server**
<br>Select *Publish to FME Server* under the File Menu. Use the Publish to FME Server Wizard to place the workspace in the **Training** repository. 

On the *Upload Connections* step, make the DropboxWebConnection is selected and click **Next**. We will authorize our web connection using the FME Server web interface.

![](./Images/5.204.Ex1.UploadConnections.png)

Make sure that the workspace is registered with the **Job Submitter** FME Server Service. Click **Publish**.


<br>**5) Login to FME Server**
<br>Open the FME Server web interface, either through the Web Interface option on the Windows Start Menu or directly in your web browser, and log in using the username and password *admin*.

---

<!--Miss Vector says...-->

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
If you have completed the Configure for HTTPS exercise, remember that the URL to connect to FME Server is now </span><span style="font-family:serif; font-style:italic; font-weight:bold; font-size:larger">https://localhost:8443/fmeserver</span><span style="font-family:serif; font-style:italic; font-size:larger"> and NOT http://localhost/fmeserver!
</span>
</td>
</tr>
</table>

---

<br>**6) Configure the Dropbox Web Service**
<br>From the left sidebar go to **Connections &gt; Web Connections**.

Click **Manage Web Services** on the Web Connections page.

![](./Images/5.205.Ex1.ManageServices.png)

Select **Dropbox**. The *Editing Web Service "Dropbox"* page opens.

Fill in the *Client Information* parameters as follows:

- **Client Id:** lxx2amcu6xfs11r
- **Client Secret:** *&lt;distributed_during_course&gt;*
- **Redirect Uri:** https://localhost:8443/fmeoauth
<!--**SM: We need to figure out how to store the credentials for this and email**-->
The Client Id and Client Secret are how you connect your client to the web service. They are generated when you create a new API app for a web service. REST API Documentation pages such as this one for [Dropbox](https://www.dropbox.com/developers) explains in more detail about web service app creation.

Click **OK** to save these updates.

![](./Images/5.206.Ex1.EditWebConnection.png)


<br>**7) Authorize Web Connection**
<br>Go back to **Connections &gt; Web Connections**

Select *DropboxWebConnection* in your list of Web Connections.

On the *Edit* page, click the **Authorize** button:

![](./Images/5.207.Ex1.Authorize.png)

A window opens with the login screen for Dropbox. Sign in with:
<!--**SM create new email account**-->
- **Email:** fmedropbox@gmail.com
- **Password:** *&lt;distributed_during_course&gt;*

The window closes, and a message pops up:

![](./Images/5.208.Ex1.AuthorizedSuccessfully.png)

You have now successfully authorized a Dropbox web connection in FME Server for you to use in your workspaces!

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
<ul><li>Access a web service</li>
<li>Publish a web connection to FME Server</li>
<li>Configure a web service in FME Server</li>
<li>Authorize a web connection on FME Server</li>
</ul>
</span>
</td>
</tr>
</table>
