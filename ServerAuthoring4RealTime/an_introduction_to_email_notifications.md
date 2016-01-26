# An Introduction to Email Notifications

An Introduction to Email Notifications Email is probably the most commonly used notification protocol

It’s important to cover email notifications in some detail because they are the most commonly used type of notification on FME Server.

“Email” is actually a protocol used by Publication and Subscription components. Email Publications receive incoming email and Email Subscriptions send outgoing email.

**Email Protocols**

FME Server can make use of email messages as both an incoming and outgoing notification protocol.

There are two email-related protocols available in FME Server: “SMTP” and “IMAP”.

The SMTP protocol is the ability to directly send or receive an email through an email server built into FME Server.

The IMAP protocol acts a little differently. It is an indirect process that connects to an email account on a server elsewhere.

When that account receives an email the IMAP protocol passes it on to FME Server.

SMTP can be used as both a Subscription and a Publication protocol; IMAP can only be used for a Publication (i.e. it can only be used to detect incoming emails).

**SMTP Publications**

SMTP Publications are when data is published to FME Server via a direct email. FME Server receives an email and triggers a Topic in response.

**Setting up an Email Publication**

Creating an SMTP publication is done in the Notifications section of the Web User Interface, by choosing the Email (SMTP) protocol for a new Publication.

Once the protocol type is selected, the publication must also be given a name and an existing topic chosen to be triggered.

The final parameter is the Email User Name; in this example it is set up to be RoadInfo.

Notice the author is suffixing the publication and topic names with _Incoming so that there is no confusion over which topics are being used for incoming notification and which ones for outgoing.

Now, whenever an email is sent to RoadInfo@serverhost.com – for example someone is sending an email to report snow on the road – the RoadConditions_Incoming topic is triggered.

**Setting up the Email Server**

SMTP email publications are possible because FME Server includes an in-built email server as one of its components. However, this does require that the server has a domain name registered with a DNS name server.

The steps to set up the email server for notifications are documented in the FME Server Reference Manual, and also in the following exercise.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Sister Intuitive says …</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“FME Cloud instances are automatically configured for email
notification, and have a public domain name too, so you don’t need
to do any additional setup.”
</span>
</td>
</tr>
</table>

**IMAP Publications**

IMAP (Internet Message Access Protocol) is a variation on email for incoming (Publication) notifications.

Instead of using the in-built email server, an IMAP Publication connects to another email server and monitors it for incoming email. When an email arrives in that account then the Topic to which it is tied becomes triggered.

Setting up an IMAP Publication

Like the SMTP protocol, IMAP Publications are set up in the Notifications section of the Web User Interface, by creating a new Publication and choosing the Email (IMAP) protocol.

Here are the parameters for an IMAP Publication:

Notice that most parameters are for defining the IMAP (Email) server connection.

Two important parameters let you decide the interval to check for emails and decide whether to fetch all unread emails or new emails only.

There is also a parameter to select an FME Server resource location in which to store any email attachments:

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Monsieur D. Server says …</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
“Most email servers support IMAP functionality, as do the majority
of cloud-based email providers such as Gmail, Outlook.com, Yahoo!,
etc; so it’s very easy to have FME Server scan a Gmail account for
incoming mail, and then act on its contents.”
</span>
</td>
</tr>
</table>

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 4A </span>
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
Publications
and
Topic
Notification</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Starting Workspace</td>
<td style="border: 1px solid darkorange">n/a</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Finished Workspace</td>
<td style="border: 1px solid darkorange">n/a</td>
</tr>

</table>

This exercise is the first part in setting up a system that provides email-driven access to image files. In this part we’ll concentrate on setting up a Topic and Publication.

For this setup you may use either the SMTP or IMAP protocol for email.

For SMTP, this exercise requires your FME Server to have a DNS record and SMTP configured.

For IMAP, this exercise requires access to an email server that supports the IMAP protocol.
Gmail, Outlook, and Yahoo! all are acceptable web-based solutions.

**1. Create a Topic**

The first step is to create a topic that will be triggered by the email.
Open the Web User Interface in a web browser by visiting http://<servername>/fmeserver

Click on the menu item labelled Manage > Notifications and then click the tab labelled Topics.

Click New and enter a topic name such as ImageProcessing.
Enter a description such as “Topic used to trigger an image processing workspace”.

Click OK to close the dialog and create the Topic.

**2. Create a Publication**

In the Notifications part of the web interface click on the Publications tab. Click the New button to create a new Publication.

The new publication can be created to use either the Email protocol or the IMAP protocol.

**Email Protocol**

Enter Email Receiver as the new publication’s name. Then click in the text box labelled Click to Select under Topics to Publish To. Select the newly created ImageProcessing topic from the drop-down list.

Now select Email (SMTP) as the Publication Protocol. This will open the Email User Name parameter. Enter a name for receiving email, for example in the format FirstnameLastname

This will create an email address <name>@<hostname> The hostname is assumed, so you don’t need to enter it yourself.

Now all emails sent to that address will trigger the ImageProcessing topic.

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
“If you don’t have access to a web-based email account, use
fmeserver2014@gmail.com with the password lizardisland.”
</span>
</td>
</tr>
</table>

**IMAP Protocol**

IMAP is the easier way to handle incoming email where computers might not have a proper DNS record, such as on an internal network.

Enter IMAP Email as the new publication’s name.

Next, click in the text box labelled Click to Select under Topics to Publish To. Select the newly created ImageProcessing topic from the drop-down list.

Now select Email (IMAP) as the Publication Protocol. This will open a number of other parameters. Enter them according to your email account:

In case it is of use, the usual server information is as follows:

Set the Poll Interval to 60 seconds and Emails to Fetch to New Emails Only.

Select a Resource Folder for attachments to be saved to and click OK to close the dialog and create the new Publication.

**3. Start Monitoring Topic**

The monitoring tool lets you know when a notification is received.

NB: To use monitoring requires the WebSocket port (usually 7078) to be open. This should automatically be the case on FME Cloud, but other systems may require some manual firewall configuration.

On the Notifications page click the tab labelled Topic Monitoring and select ImageProcessing as the topic to monitor:

**4. Send an Email**

Now let’s test the setup so far by sending an email to FME Server. At the moment you can use any subject line or contents for the email, as FME is not yet using them to do anything.

If you chose the SMTP protocol then the email should be sent to <emailname>@<hostname>.

For example an FME Cloud address would be like this: MyName@server-tutorial.safe-software.fmecloud.com And an Amazon AWS machine would have an address like this:

MyName@ec2-54-224-106-213.compute-1.amazonaws.com

If you used the IMAP protocol then send an email to the account you chose in the Publication.

For IMAP there will probably be a slight delay because FME is only checking for email every minute, plus it will take a short while for the email to arrive. However, shortly the email will be recognized by FME Server, the notification topic triggered, and the activity reported by the monitor:

**Congratulations!**
You have now triggered an FME Server notification using email.