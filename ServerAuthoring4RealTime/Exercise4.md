<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4 (Advanced)</span>
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
<td style="border: 1px solid darkorange">Email publications and subscriptions</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">RealTime-Ex4-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">RealTime-Ex4-Complete.fmw/td>
</tr>

</table>

---

As a technical analyst in the GIS department you were involved in a recent project to set up a Directory Watch solution for users to automatically update the corporate database. Having learned that not all users are able to access the internal network where FME Server is hosted, you think that it should be possible to also set up a system that uses email-based automation to handle the same updates.

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
This exercise continues where Exercise 3 left off. You must have completed Exercise 3 to carry out this exercise.
<br><br> Access to an SMTP Email Server is required for this exercise for sending email. Gmail, Outlook, and Yahoo! are examples acceptable web-based solutions if you do not have access to an internal email server.
</td>
</tr>
</table>

---

<br>**1) Create Topic**
<br>The first step is to create a topic that will be triggered by the email. Log in to the FME Server Web UI and navigate to the Notifications page.

Click the Publications tab and then click the New button.

Enter "Email Receiver" as publication name. Then click in the text box under Topics to Publish To. Type in ShapeIncomingEmail and click on it to add. This will create a new topic and assign it to this publication. 

![](./Images/Img4.417.Ex4.CreateIncomingTopic.png)

The new publication can be created to use either the Email (SMTP) protocol or the Email (IMAP) protocol. 

SMTP is easier to set up but FME Server must reside on a server with a proper DNS record (all FME Cloud and Training machines will have this). IMAP is necessary when FME Server resides on an internal network.

---

***Email Protocol***

To use the SMTP protocol select Email (SMTP) as the Publication Protocol. This will open the Email User Name parameter. Enter a name for receiving email, for example *fmeshapeprocessing*

![](./Images/Img4.418.Ex4.CreateSMTPPublication.png)

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

In case it is of use, the server information for Gmail is as follows:

- IMAP Server Host: imap.gmail.com
- IMAP Server Port: 993
- Connection Security: SSL
- Verify SSL Certificate: Yes

You will also need to check the settings in your Gmail account to make sure IMAP is turned on (by default it is not). Regardless of the email provider, you should set these parameters as follows:

- Poll Interval: 1 minute
- Emails to Fetch: New Emails Only.

Select a Resource Folder for attachments to be saved to and click OK to close the dialog and create the new Publication.


<br>**2) Test Publication**
<br>Now let's test the publication. In the Notifications page on FME Server, click the tab marked Topics. Set up Topic Monitoring on the topic *ShapeIncomingEmail*:

![](./Images/Img4.419.Ex4.MonitorTopic.png)

Now send an email *with an attachment* to the address selected for the new publication. When the email is received by FME Server (SMTP) or FME Server fetches it (IMAP) the topic will be triggered with a message. (Remember, an IMAP publication only checks for an email every 60 seconds, so the result might not be immediate!)

![](./Images/Img4.420.Ex4.MonitorTopicResult.png)

Recall that in the previous exercise you used the Logger Protocol and Logger transformers to record the JSON formatted notification message. The same information is displayed in the Topic Monitoring window - copy these text and place it into a new file for use later.

![](./Images/Img4.421.Ex4.JSONNotificationMessage.png)


<br>**3) Update Workspace**
<br>You already have a created a workspace in FME Workbench to handle incoming notifications from Directory Watch. Let's modify the workflow so that it can work with both Publications Protocols. Open the existing workspace C:\FMEData2017\Workspaces\ServerAuthoring\RealTime-Ex4-Begin.fmw in FME Workbench.

Open the JSONFlattener parameters, and add imap_publisher_attachment{0} and email_publisher_attachment{0} under Attributes to Expose:

![](./Images/Img4.422.Ex4.JSONFlattenerParameters.png)

---

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
Adding both imap_publisher_attachment and email_publisher_attachment modifies this workspace so that it will work with both Email (SMTP) and Email (IMAP) Publications!
</span>
</td>
</tr>
</table>

---

The next step is to insert a transformer that will determine where the data is coming from (Directory Watch or an Email Publication) - this is a task where conditional statements are invaluable! 

Add an AttributeManager transformer in between the JSONFlattener and FeatureReader. Open the parameters and add "_dataset" as a new Output Attribute. Set the Attribute Value as a Conditional Value:

![](./Images/Img4.423.Ex4.AttributeManagerParameters.png)

Configure the Conditional Value as follows:

![](./Images/Img4.424.Ex4.ConditionalDefinition.png)

The final step is to change the Dataset in the FeatureReader to point at the new _dataset attribute:

![](./Images/Img4.425.Ex4.FeatureReaderParameters.png)

The workflow should now look like this:

![](./Images/Img4.426.Ex4.FinalWorkspace.png)


<br>**4) Publish Workspace**
<br>Publish this workspace to FME Server

Open the JSONFlattener parameters, and add imap_publisher_attachment{0} and email_publisher_attachment{0} under Attributes to Expose:

![](./Images/Img4.427.png)




---

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
In a training course more than one student might be using the IMAP account fmeimageprocessing@gmail.com, so don't be surprised by multiple messages arriving!
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
<ul><li>Create a new Publication</li>
<li>Create a new Topic as part of the Create Publication process</li>
<li>Use incoming email to trigger topics/notifications</li>
<li>Test a publication/topic using Topic Monitoring</li></ul>
</span>
</td>
</tr>
</table>   
