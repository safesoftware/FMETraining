<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4D </span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Basic
Notifications
and
Email
Subscription</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Scenario</td>
<td style="border: 1px solid darkorange">Airphoto Data Vendor</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">GeoTiff Orthophotos</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Provide
email-­‐driven
self-­‐serve
access
to
image
files</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Email
Subscriptions</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise4d-­‐Begin.fmw</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">C:\FMEData2015\Workspaces\ServerAuthoring\Exercise4d-­‐Complete.fmw</td>
</tr>

</table>

Having already set up a solution for incoming email notifications (in Exercise 4b) and used that information to select an area of interest (Exercise 4c) we can now expand upon that to return an email containing the data chosen by the user.

**1. Open the Starting Workspace**

In FME Workbench open the starting workspace for this exercise.

You must open this workspace as it is slightly modified from the one in Exercise 4c. A UUIDGenerator transformer and a dataset fanout has been added so that the output JPEG file has a unique name and is written to the FME Server Resources/Data/Output directory.

**2. Create an Email Topic**

Remember, it’s important for a setup like this to use different topics for incoming and outgoing notifications; otherwise the process will end up in an infinite loop.

So open the Web User Interface and click the Notifications link on the Manage menu. In the Topics tab click New to create a new Topic. Enter the name sendemail. Enter some text in the description to say “Use this topic to trigger an email using an Email Subscription”.

**3. Create an Email Subscription**

Continue in the Notifications part of the Web User Interface. Click the Subscriptions tab and then click New.

Enter EmailSender as the subscription name and choose the sendemail topic created in step 2.

**4. Enter Email Settings**

Select email as the protocol for the new subscription.

Use the table below to enter your email settings depending on your email service. Please note that if you are using your own internal email system the settings may differ and you may need to ask your IT provider.

The following settings are same regardless of email service:

Email to: <leave blank>

Email cc: <leave blank or enter an admin cc email address>

Email from: <your email address>

Email Subject: Your Data is Attached

Email Format: TEXT

Email Template: <leave blank>

We can leave some of these fields empty because they will be populated from the workspace when we send the email notification message.
Click OK to accept the settings and create the new Subscription.

**5. Add FMEServerEmailGenerator**

Back in FME Workbench, click on the workspace canvas and start typing “FMEServer” to locate and add an FMEServerEmailGenerator transformer.

This is a Custom Transformer that will be downloaded from the FME Store – as denoted by the small arrow on its icon in the Quick Add dialog.

The transformer is designed to be a quick and easy way to set up an outgoing email.

**6. Connect Custom Transformer**

Connect the newly placed custom transformer on a new connection from the UUIDGenerator: DO NOT connect it between the UUIDGenerator and the Writer feature type. We’ll shortly add a new Writer to connect it to.

**7. Set Transformer Parameters**

Click on the red cog-wheel icon to open the parameters dialog for the FMEServerEmailGenerator transformer. As you’ll see, there are many parameters to help us create the JSON message we will be sending to the email Subscription.

The important parameters should be set as follows:

**To:** This value depends on whether you are using IMAP or SMTP to send your email to FME Server. Click the drop-down arrow to the right and select Attribute Value > clipper_email_publisher_from or clipper_imap_publisher_from. This attribute contains the address the incoming email was received from and therefore should be used for who the outgoing email will be sent to.

**Attachments:** Click the drop-down arrow to the right and select Open Text Editor. This value will be slightly more complex than an attribute and we need to construct it with an editor such as this.

Enter the following into the text editor field: $(FME_SHAREDRESOURCE_DATA)/Output/@Value(_uuid)/AirphotoMosaic.jpg

This tells FME to use the data created by the JPEG writer as an attachment to the outgoing email message. Click OK to close the dialog.

The other fields can be set as follows:

CC: blank

From: blank

Reply to: blank

Subject: Your Image Order is Attached

Message: Please find attached the image you requested.

Note that the blank parameters will come from the Email Subscription we set up in Step 1

**8. Add a Notification Writer**

Having created the email to send we now need to add a Writer to pass it to the Notification service.

Select Writers > Add Writer from the menubar. Create a writer with the following parameters:

Writer Format: Text File

Writer Dataset: C:\FMEData2015\Output\Email.json

Once added, connect the FMEServerEmailGenerator transformer to the new feature type.
The transformer automatically generates the text_line_data attribute required by this Writer.

**9. Publish the Workspace (Step 1)**

This workspace is the heart of a system of incoming and outgoing notification messages; therefore it needs to be published to FME Server as both a Publication and Subscription!

As always, start the Publish Wizard, enter the connection parameters, and choose the Training repository to store the workspace.

As in Exercise 4c, click the Select Files button to ensure that the VancouverNeighborhoods.kml file will be uploaded to the repository, and that the image data is not.

Again as in Exercise 4c, click OK and then – when warned about invalid references – for each of the Orthophoto references, click the […] ellipsis button and browse to the true file location in the resources folder.

**10. Publish the Workspace (Step 2)**

In the Services dialog check the Notification Service and click its Edit button.
Again select ImageProcessing as the Subscribed Topic, and set the Notification Reader to the email[TEXTLINE] Reader.

In the same Edit Service Properties dialog scroll down and expand the Notify on Job Completion settings.

Set Topics to Publish (Success) to the sendemail topic you previously created.

Set the Notification Writer should be set to your Email[TEXTLINE] Writer.

Leave Topics to Publish (Failure ) blank, but notice this is where you could handle a failure in workspace if you wanted to.

Click OK and then Publish to complete the wizard.

**11. Send an Email to FME Server**

Again send an email to your FME Server using the email address you have been using, and entering either Downtown or West End as the subject of the email.

After a minute or two you will receive an email back with the image attached. The image will be an orthophoto clipped to the neighbourhood you entered in the subject line.

Congratulations! Without writing any code you have set-up an email ordering system for imagery.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Mr. Flibble says …</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Exercise4d. As with 4b and 4c, unsubscribe it from the notification
if you are using IMAP and don’t want all incoming emails to keep
triggering the workspace.”
</span>
</td>
</tr>
</table>