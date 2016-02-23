<!--Instructor Notes-->

<!--Exercise Section-->
<!--NB: In GitBook world we don't give a number to exercises-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 1</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold"></span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">Orthophoto images (GeoTIFF)</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Provide email-driven access to orthophoto files</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Notification topics and email publications</td>
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

As a technical analyst in the GIS department a recent project involved setting up a Data Download solution for users to serve orthophoto data to themselves. Having read up about notifications in FME Server, you think that it should be possible to set up a system that uses email-based automation.

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
For this exercise you may use either the SMTP or IMAP protocol for email. 
<br>For SMTP, this requires your FME Server to have a DNS record and SMTP configured. 
<br>For IMAP this requires access to an email server that supports the IMAP protocol. Gmail, Outlook, and Yahoo! all are acceptable web-based solutions. 
</td>
</tr>
</table>

---

<br>**1) Create Topic**
<br>The first step is to create a topic that will be triggered by the email. So log in to the FME Server web interface and click on the menu item labelled Manage &gt; Notifications.

Click the tab labelled Topics and click the button labelled New. When prompted enter a topic name such as ImagesIncomingRequest. Enter a description such as “Topic used to trigger an image processing workspace”:

![](./Images/Img4.35.Ex1.CreateIncomingTopic.png)

Click OK to close the dialog and create the Topic.



<br>**2) Add Email Publication**
<br>In the same Notifications page, click the Publications tab and then click the New button.

The new publication can be created to use either the Email protocol or the IMAP protocol.

---

***Email Protocol***

Enter Email Receiver as the new publication’s name. Then click in the text box labelled Click to Select under Topics to Publish To. Select the newly created ImageProcessing topic from the drop-down list.

Now select Email (SMTP) as the Publication Protocol. This will open the Email User Name parameter. Enter a name for receiving email, for example in the format FirstnameLastname

This will create an email address <name>@<hostname> The hostname is assumed, so you don’t need to enter it yourself.

Now all emails sent to that address will trigger the ImageProcessing topic.

---

***IMAP Protocol***

IMAP is the easier way to handle incoming email where computers might not have a proper DNS record, such as on an internal network.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">InteropGeek68 says …</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
If you don’t have access to a web-based email account, use fmeserver2014@gmail.com with the password lizardisland.
</span>
</td>
</tr>
</table>

Enter IMAP Email as the new publication’s name.

Next, click in the text box labelled Click to Select under Topics to Publish To. Select the newly created ImageProcessing topic from the drop-down list.

Now select Email (IMAP) as the Publication Protocol. This will open a number of other parameters. Enter them according to your email account:

In case it is of use, the usual server information is as follows:

Set the Poll Interval to 60 seconds and Emails to Fetch to New Emails Only.

Select a Resource Folder for attachments to be saved to and click OK to close the dialog and create the new Publication.
xxxx


<br>**3) Create Workspace**
<br>xxxx


<br>**4) Publish Workspaces**
<br>xxxx


 
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
<ul><li>Send and receive messages via WebSockets</li>
<li>Publish and run message-streaming workspaces</li>
<li>Cancel message-streaming workspaces and check their log files</li>
<li>Extract attributes from JSON messages</li>
<li>Use transformers to transform and filter a message according to its content</li>
<li>Set up workspaces to handle group-based transformers in a real-time scenario</li>
<li>Record incoming messages into a database</li>
<li>Set up a hybrid system with message streaming <strong>and</strong> notifications</li></ul>
</span>
</td>
</tr>
</table>   
