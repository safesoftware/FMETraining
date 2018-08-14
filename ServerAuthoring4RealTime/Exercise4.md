<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4.4</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Building Updates Notification System</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Building footprints (Esri Shapefile)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Provide email-driven notifications for updates</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Email publications and Notification service</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\ServerAuthoring\RealTime-Ex4-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2018\Workspaces\ServerAuthoring\RealTime-Ex4-Complete.fmw</td>
</tr>

</table>

---

As a technical analyst in the GIS department, you were involved in a recent project to set up a Directory Watch solution for users to automatically update the corporate database.

Having learned that not all users are able to access the internal network where FME Server is hosted, you think that it should be possible to also set up a system that uses email-based automation to handle the same updates.

---

<br>**1) Create Resource Folder**
The first step is to create another Resource folder to save all the email attachments to. Log into the FME Server web interface and then navigate to Resources > Data then create a new folder called Emails. 

<br>**2) Create Topic**
<br>Next, Navigate to the Notifications page. Click the Publications tab and then select New.

Enter "Email Receiver" as the Name. Then click on the text box under Topics to Publish To. Type in *ShapeIncomingEmail* and click on it to add. This will create a new Topic and assign it to this Publication.

![](./Images/Img4.424.Ex4.CreateIncomingTopic.png)

The new Publication can be created to use either the Email (SMTP) protocol or the Email (IMAP) protocol.

SMTP is easier to set up, but FME Server must reside on a server with a proper DNS record (all FME Cloud and Training machines will have this). IMAP is necessary when FME Server resides on an internal network.

---

***Email Protocol***

To use the SMTP protocol select Email (SMTP) as the Publication Protocol. This will open the Email User Name parameter. Enter a name for receiving email, for example: *fmeshapeprocessing*

![](./Images/Img4.425.Ex4.CreateSMTPPublication.png)

Clicking OK will create an email address *fmeshapeprocessing@&lt;hostname&gt;* - for example:

<table>
<tr><th>Host</th><th>Example Email Address</th></tr>
<tr><td>FME Cloud</td><td>fmeshapeprocessing@myfmeserver.fmecloud.com</td></tr>
<tr><td>Amazon AWS</td><td>fmeshapeprocessing@ec1-23-456-789-012.compute-1.amazonaws.com</td></tr>
</table>

Now all emails sent to that address will trigger the ShapeIncomingEmail topic.

---

***IMAP Protocol***

To use the IMAP protocol select Email (IMAP) as the Publication Protocol. This will open a number of other parameters. Enter them according to your email account.

In case it is of use, the server information for Gmail, Outlook, and Yahoo! are as follows:

<table style="border: 0px">

<tr>
<td style="font-weight: bold">IMAP Server Host</td>
<td style="">imap.gmail.com</td>
<td style="">imap-mail.outlook.com</td>
<td style="">imap.mail.yahoo.com</td>
</tr>

<tr>
<td style="font-weight: bold">Server Port</td>
<td style="">993</td>
<td style="">993</td>
<td style="">993</td>
</tr>

<tr>
<td style="font-weight: bold">Connection Security</td>
<td style="">SSL/TLS</td>
<td style="">SSL/TLS</td>
<td style="">SSL/TLS</td>
</tr>

<tr>
<td style="font-weight: bold">Verify SSL Certificates</td>
<td style="">Yes</td>
<td style="">Yes</td>
<td style="">Yes</td>
</tr>

</table>

You will also need to check the settings in your email account to make sure IMAP is turned on. Regardless of the email provider, you should set these parameters as follows:

<table style="border: 0px">

<tr>
<th style="font-weight: bold">Parameter</th>
<th style="">Value</th>
</tr>

<tr>
<td style="font-weight: bold">Poll Interval</td>
<td style="">1 Minute</td>
</tr>

<tr>
<td style="font-weight: bold">Emails to Fetch</td>
<td style="">New Emails Only</td>
</tr>

<tr>
<td style="font-weight: bold">Download Attachments To</td>
<td style="">A Resource folder of your choice</td>
</tr>

</table>


You may select any Resource folder for attachments to be saved to; but (if you have already completed exercise 1-3) don't choose the BuildingUpdates folder, or else you'll cause the previous topics to be triggered by each email attachment!


<br>**3) Test Publication**
<br>Now let's test the publication. In the Notifications page on FME Server, click the tab marked Topics. Set up Topic Monitoring to watch the topic *ShapeIncomingEmail*:

![](./Images/Img4.426.Ex4.MonitorTopic.png)

Now send an email *with an attachment* to the address selected for the new publication. When the email is received by FME Server (SMTP), or FME Server fetches it (IMAP), the topic will be triggered with a message. (Remember that an IMAP publication only checks for an email every 60 seconds, so the result might not be immediate!)

![](./Images/Img4.427.Ex4.MonitorTopicResult.png)

Recall that in the previous exercise you used the Logger Protocol and Logger transformers to record the JSON formatted notification message. The same information is displayed in the Topic Monitoring window. So copy the text from the Topic Monitoring window and paste it into a text editor for use later in this exercise.

![](./Images/Img4.428.Ex4.JSONNotificationMessage.png)


<br>**4) Update Workspace**
<br>You already have a created a workspace in FME Workbench to handle incoming notifications from Directory Watch. Let's modify the workflow so that it can work with both Publication protocols. Open the existing workspace C:\FMEData2018\Workspaces\ServerAuthoring\RealTime-Ex4-Begin.fmw in FME Workbench.

Open the JSONFlattener parameters, and add *imap&#95;publisher&#95;attachment{0}* and *email&#95;publisher&#95;attachment{0}* under Attributes to Expose:

![](./Images/Img4.429.Ex4.JSONFlattenerParameters.png)

You can see these are two of the available attributes that are returned by the Topic Message.

<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Ms Analyst says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
Adding both imap&#95;publisher&#95;attachment and email&#95;publisher&#95;attachment modifies this workspace so that it can work with both Email (SMTP) and Email (IMAP) Publications!
</span>
</td>
</tr>
</table>


<br>**5) Add AttributeManager**
<br>The next step is to insert a transformer that will determine where the data is coming from (Directory Watch or an Email Publication) - this is a task where conditional statements are invaluable.

Add an AttributeManager transformer in between the JSONFlattener and FeatureReader. Open the parameters and add *&#95;dataset* as a new Output Attribute.

Select, from the drop-down menu, the option to set the attribute as a Conditional Value:

![](./Images/Img4.430.Ex4.AttributeManagerParameters.png)

Configure the Conditional Value as follows:

![](./Images/Img4.431.Ex4.ConditionalDefinition.png)

<table style="border: 0px">

<tr>
<th style="">Attribute</th>
<th style="">Test</th>
<th style="">Set &#95;dataset To</th>
</tr>

<tr>
<td style="">dirwatch&#95;publisher&#95;path</td>
<td style="">Attribute has a value</td>
<td style="">dirwatch&#95;publisher&#95;path</td>
</tr>

<tr>
<td style="">email&#95;publisher&#95;attachment{0}</td>
<td style="">Attribute has a value</td>
<td style="">email&#95;publisher&#95;attachment{0}</td>
</tr>

<tr>
<td style="">imap&#95;publisher&#95;attachment{0}</td>
<td style="">Attribute has a value</td>
<td style="">imap&#95;publisher&#95;attachment{0}</td>
</tr>

</table>

In other words:

- If *dirwatch&#95;publisher&#95;path* has a value, then copy that value into the *&#95;dataset* attribute.
- Else, if *email&#95;publisher&#95;attachment{0}* has a value, then copy that value into the *&#95;dataset* attribute.
- Else, if *imap&#95;publisher&#95;attachment{0}* has a value, then copy that value into the *&#95;dataset* attribute.

So *&#95;dataset* gets the location of the data to be processed, whether it comes from the directory watch notification, or an email notification of either type.


<br>**6) Edit FeatureReader**
<br>The final step is to change the Dataset parameter in the FeatureReader transformer. Instead of pointing to dirwatch&#95;publisher&#95;path, it should be changed to point at the new &#95;dataset attribute:

![](./Images/Img4.432.Ex4.FeatureReaderParameters.png)

The workflow should now look like this:

![](./Images/Img4.433.Ex4.FinalWorkspace.png)


<br>**7) Edit User Parameter**
<br>As with Exercise 3, specify the output dataset to be written into the FME Server Resources Folder.

Locate the user parameter DestDataset&#95;SPATIALITE (under User Parameters &gt; Published Parameters in the Navigator window) and double-click it to open an editor dialog.

In that dialog enter:

<pre>
    $(FME&#95;SHAREDRESOURCE&#95;DATA)/Output/building&#95;footprints.sl3*
</pre>

![](./Images/Img4.434.Ex4.DestinationDatasetUserParameter.png)


<br>**8) Publish Workspace**
<br>Publish this workspace to FME Server, registering it under the Notification service. When the Notification service is selected, it is highlighted in red indicating its parameters need to be configured.

Click the "Edit" button and set *ShapeIncomingEmail* for the "Subscribe to Topics" parameter. Set the "Parameter to Get Topic Message" as *Source Text File(s)*:

![](./Images/Img4.435.Ex4.PublishWorkspaceNotificationService.png)


<br>**9) Update Directory Watch Subscription (Optional)**
<br>If you have completed Exercise 3, using the FME Server web interface you can set the "Process Building Updates" Subscription to point at this new workspace.


<br>**10) Test Workspace**
<br>Test the workspace by sending an email to the Publication email address. Be sure to attach a zip file of the Shapefile datasets (.dbf, .prj, .shp, .shx) from C:\FMEData2018\Data\Engineering\BuildingFootprints to the email.

You can verify if the workflow was successful by checking the Completed Jobs page and the timestamp of the SpatiaLite database in Resources &gt; Data &gt; Output in the FME Server web interface.


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
<ul><li>Create an Email Publication</li>
<li>Create a new FME Workspace Subscription as part of the Publishing process</li>
<li>Use incoming email to trigger Topics/Notifications</li>
<li>Configure a workspace to handle triggers by multiple Publication types</li></ul>
</span>
</td>
</tr>
</table>   
