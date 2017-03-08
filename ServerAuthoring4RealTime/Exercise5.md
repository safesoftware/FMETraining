<!--Instructor Notes-->

<!--Exercise Section-->


<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 5</span>
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
<td style="border: 1px solid darkorange">Email subscriptions</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Start Workspace</td>
<td style="border: 1px solid darkorange">RealTime-Ex4-Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">End Workspace</td>
<td style="border: 1px solid darkorange">RealTime-Ex4-Complete.fmw</td>
</tr>

</table>

---

After configuring FME Server to process building footprints updates with both the Directory Watch and Email Publications, your supervisor is wondering if they can receive an email whenever the corporate database is updated.

Using an external email server, you think that it is possible configure another Notification in FME Server to satisfy this requirement.

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
This exercise continues where Exercise 4 left off. You must have completed Exercise 4 to carry out this exercise.
<br>Access to an SMTP Email Server is required for sending email in this exercise. Gmail, Outlook, and Yahoo! are examples acceptable web-based solutions if you do not have access to an internal email server.
</td>
</tr>
</table>

---

<br>**1) Add Subscription**
<br>Open the FME Server web user interface and navigate to the Notifications page. Click the Subscriptions tab and then click New to create a new Subscription. This will be an email service through which a response will be sent.

Give the subscription a name like *Send Building Update Email* and create a new topic for it such as *BuildingUpdateEmail* (it's important to use a different topic than from the previous exercises).

Set the protocol to Email and set up your SMTP email server parameters.

In case it is of use, the server information for Gmail is as follows:

- SMTP Server: smtp.gmail.com
- SMTP Server Port: 465
- Connection Security: SSL/TLS

Regardless of the email provider, you should set these parameters as follows:

- Email To: An email address you have access to check
- Email From: Your email account (for example fmeshapeprocessing@gmail.com)
- Email Subject: "Building Footprints Database Updated"
- Email
- Email Template: 
The Building Footprints database has been updated!
<fmeblock type="optional"\>
{NumFeaturesOutput} features were updated at {timeFinished}.
Job {id} Log: {logUrl}
</fmeblock\>

  
  
  


<br>**2) Test Publication**
<br>Now let's test the publication. In the Notifications page on FME Server, click the tab marked Topics. Set up Topic Monitoring to watch the topic *ShapeIncomingEmail*:

![](./Images/Img4.419.Ex4.MonitorTopic.png)

Now send an email *with an attachment* to the address selected for the new publication. When the email is received by FME Server (SMTP), or FME Server fetches it (IMAP), the topic will be triggered with a message. (Remember that an IMAP publication only checks for an email every 60 seconds, so the result might not be immediate!)

![](./Images/Img4.420.Ex4.MonitorTopicResult.png)

Recall that in the previous exercise you used the Logger Protocol and Logger transformers to record the JSON formatted notification message. The same information is displayed in the Topic Monitoring window - copy this text and place it into a new file for use later in this exercise.

![](./Images/Img4.421.Ex4.JSONNotificationMessage.png)


<br>**3) Update Workspace**
<br>You already have a created a workspace in FME Workbench to handle incoming notifications from Directory Watch. Let's modify the workflow so that it can work with both Publication protocols. Open the existing workspace C:\FMEData2017\Workspaces\ServerAuthoring\RealTime-Ex4-Begin.fmw in FME Workbench.

Open the JSONFlattener parameters, and add *imap_publisher_attachment{0}* and *email_publisher_attachment{0}* under Attributes to Expose:

![](./Images/Img4.422.Ex4.JSONFlattenerParameters.png)

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
Adding both imap_publisher_attachment and email_publisher_attachment modifies this workspace so that it can work with both Email (SMTP) and Email (IMAP) Publications!
</span>
</td>
</tr>
</table>

The next step is to insert a transformer that will determine where the data is coming from (Directory Watch or an Email Publication) - this is a task where conditional statements are invaluable.

Add an AttributeManager transformer in between the JSONFlattener and FeatureReader. Open the parameters and add *_dataset* as a new Output Attribute. 

Set the Attribute Value as a Conditional Value:

![](./Images/Img4.423.Ex4.AttributeManagerParameters.png)

Configure the Conditional Value as follows:

![](./Images/Img4.424.Ex4.ConditionalDefinition.png)

The final step is to change the Dataset in the FeatureReader to point at the new _dataset attribute:

![](./Images/Img4.425.Ex4.FeatureReaderParameters.png)

The workflow should now look like this:

![](./Images/Img4.426.Ex4.FinalWorkspace.png)


<br>**4) Publish Workspace**
<br>Publish this workspace to FME Server, registering it under the Notification service. When the Notification service is selected, it is highlighted in red indicating its parameters need to be configured. 

Click the "Edit" button and set *ShapeIncomingEmail* for the "Subscribe to Topics" parameter. Set the "Parameter to Get Topic Message" as *Source Text File(s)*:

![](./Images/Img4.427.Ex4.PublishWorkspaceNotificationService.png)


<br>**5) Update Directory Watch Subscription (Optional)**
<br>If you have completed Exercise 3, using the FME Server web user interface you can set the "Process Building Updates" Subscription to point at this new workspace. 


<br>**6) Test Workspace**
<br>Test the workspace by sending an email to the Publication email address. Be sure to attach a zip file of the Shapefile datasets (.dbf, .prj, .shp, .shx) from C:\FMEData2017\Data\Engineering\BuildingFootprints to the email.

You can verify if the workflow was successful by checking the Completed Jobs page and the timestamp of the SpatiaLite database in Resources > Output in the FME Server web user interface.



<br>**2) Edit Workspace**
<br>Open the workspace from exercise 4 (or the begin workspace listed above). Add two new transformers - the FMEServerEmailGenerator (a custom transformer) and an FMEServerNotifier - as a separate stream of data:

![](./Images/Img4.50.Ex4.WorkspaceWithEmailGeneration.png)
  

<br>**3) Edit JSONFlattener**
<br>To send an email back to the same person who sent the incoming email, we need to expose an attribute with that account name. So, open the properties dialog for the JSONFlattener and in the Attributes to Expose parameter, add *email&#95;publisher&#95;from* and *imap&#95;publisher&#95;from* 

![](./Images/Img4.51.Ex4.ExposeSourceAccountAttr.png)


<br>**4) Edit Clipper**
<br>We need the exposed attributes in the two transformers we placed earlier, but currently it's unlikely such attributes make it past the Clipper transformer. So, open the Clipper parameters dialog and check the box labelled Merge Attributes:

![](./Images/Img4.52.Ex4.ClipperMergeAttributes.png)


<br>**5) Edit FMEServerEmailGenerator**
<br>Now open the parameters dialog for the FMEServerEmailGenerator. We could just set the To parameter to one of the attributes we've exposed, depending on what incoming protocol we are using. However, a better solution is to set up the workspace to work regardless of protocol.

So, click the drop-down arrow to the right of the To parameter and choose Conditional Value. Double-click the first row (where it says "If") and a dialog will open in which to enter a test condition. Set up a test where *email&#95;publisher&#95;from* "Has Value". Set the output value to the *email&#95;publisher&#95;from* attribute: 

![](./Images/Img4.53.Ex4.ConditionalToField1.png)

In other words, if *email&#95;publisher&#95;from* has a value then use it for the To field. Click OK to close that dialog.

Now, back in the previous dialog, double-click in the Else &gt; Output Value field and select Attribute &gt; *imap&#95;publisher&#95;from* from the attribute list:

![](./Images/Img4.54.Ex4.ConditionalToField2.png)

In other words, if *email&#95;publisher&#95;from* has a value then use it for the To field, else use *imap&#95;publisher&#95;from*

Close this dialog and in the other fields of the FMEServerEmailGenerator, enter a Subject and Message (such as "Your Data is Ready"):

![](./Images/Img4.55.Ex4.FMEServerEmailGeneratorParameters.png)

Click OK to close the dialog and we have an email ready to send. 


<br>**6) Edit FMEServerNotifier**
<br>Now edit the parameters for the FMEServerNotifier transformer. In the first dialog enter the connection parameters. In the second dialog pick the topic created earlier (ImagesOutgoingResponse) and for the content select the attribute text_line_data (this is what was created by the FMEServerEmailGenerator):

![](./Images/Img4.56.Ex4.FMEServerNotifierParameters.png)
  

<br>**7) Publish to FME Server**
<br>Publish the workspace to FME Server. You may (or may not) need to also upload the source raster and KML datasets (depending on whether your FME Server can access the files on your authoring system). Simply register the workspace with the Job Submitter service. 

If the workspace you publish has a different name to that in exercise 3, be sure to navigate to the workspace subscription (Process Images Request) and change it to point to the correct workspace.


<br>**8) Test Workspace**
<br>Test the workspace by sending an email to the Publication email address. Be sure to make the subject line one of the neighborhoods in Vancouver:

- Downtown
- Fairview
- Kitsilano
- Mount Pleasant
- Strathcona
- West End

You should receive an email in return, alerting you to when your data is ready to collect. If there is no return email, remember to check to ensure the workspace is triggered and run (in the Topic Monitoring and/or Jobs pages) and then look for the output dataset in Resources &gt; Data &gt; Output 



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
<ul><li>Set up an outgoing email subscription</li>
<li>Set up email content within an FME workspace</li>
<li>Trigger an email subscription through the FMEServerNotifier transformer</li></ul>
</span>
</td>
</tr>
</table>   
