# Troubleshooting for Administrators

This section shows a few basic troubleshooting techniques in case of emergency FME Server Fails to Receive Email

If you are unable to receive email on FME Server then the following suggestions may be of help.

• Ensure you carry out the post-installation configuration steps as noted in the reference manual. Without this only local mail could be delivered.

• Is the FME Server’s email SMTP port open? Typically this will be port 25 or 465.

• Does your FME Server have a DNS name that is available on an internet name server or your local DNS setup? Email cannot be delivered to it if it cannot be found!

• For IMAP, is the FME Server’s IMAP port open? Typically this will be port 993. 

**FME Server Fails to Send Email** 

If you are unable to send email on FME Server then the following suggestions may be of help.

• Have you created and properly configured the Email Subscriber? The Data Download and Job Submitter services have pre-defined Subscribers, but they will need to be properly configured.

• Is the FME Server’s email SMTP port open? Typically this will be port 25 or 465.

• Does the FME Server have an internet connection?

**Email Uses Defaults**

If email sent by FME Server uses default parameters instead of those you had configured, then the following suggestions may be of help.

• If you are sending an email using the FMEServerNotifier transformer ensure that the Content parameter is set to an attribute that contains the email message information in JSON format (use the custom transformer FMEServerEmailGenerator)

• If you are sending an email from a completed workspace using the Notification Service and Topics to Notify (Success) ensure the Notification Writer is set to the Text File writer which is writing the email information.

**Cannot Connect to WebSockets Server**

If you cannot connect to a WebSockets server then the following may be of help.

• Ensure the FME Server’s WebSockets port (default 7078) is open.

• Ensure you are using the correct stream_id for sending and receiving between your applications

**Workspace Subscription is not Triggered by Topic**

If a workspace set to subscribe to a topic is not triggered by it, then the following suggestions may
be of help.

• Check the Push subscription for the workspace in the Web User Interface and make sure the required Topic is in the list of Topics subscribed to.

• Check the Push subscription for the workspace in the Web User Interface and confirm the username and password for the subscription. If you have changed your password recently the password for the subscription needs to be changed as well

**Topic Monitoring Fails**

If topic monitoring fails then the following may be of help.

• Monitoring requires the use of WebSockets, so ensure the FME Server’s WebSockets port (default 7078) is open.