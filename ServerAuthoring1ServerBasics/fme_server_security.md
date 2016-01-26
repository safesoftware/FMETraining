# FME Server Security

FME Server includes security to prevent unauthorized users from accessing services and other resources.

All security information for FME Server is stored in the repository database and is managed using the FME Server Web User Interface.

The key to setting up FME Server security is to have a clear plan on which services and accounts will be provided with open access, and which need to be restricted.

These policies are then set up using the Security section of the Web User Interface.

**Roles and Users**

Security is implemented using a system of roles and users. A role is best described as a function of the person; for example user, author, or administrator. Each user account is associated with one or more roles.

A default set of roles and user accounts is defined when FME Server is installed:

For example, in the previous example, if you logged in using the admin account, then you have both the role of fmeadmin and fmesuperuser.

Rather than apply security settings to individual users, FME Server allows you to apply them to specific roles. That way the settings can be changed for multiple users at once.

The role is selected under the Role Policies tab:

**Security Policies**

There are various sections of security policies that can be set for each role.

**General**

These are general policies such as the ability to manage jobs, services, and security. For example, if you don’t have the ability to manage security, that item will be missing from the main menu of the user interface.

**Topics**

Topics are related to Notifications, which we’ll cover later. Different capabilities – read, write, publish, remove – can be assigned for each topic you create.

**Resources**

Resources are files and datasets stored on FME Server. Different permissions – read, write, upload, delete – can be assigned to each resource.

**Services**

Services are key items of functionality on FME Server. They are the different methods by which a workspace can be run and output data delivered. Each role can be allowed – or not – to use a particular service.

**Repositories**

As you know, repositories are a place to store and categorize workspaces. Each role can be given different permissions for each and every repository.

**Components**

Components are different pieces of workspace functionality – Readers, Writers, and Transformers – that can be controlled through security settings.

For example, you may wish to prevent a particular role from running workspaces on Server using the FMEServerJobSubmitter transformer.

**Applications**

Applications are the different ways in which FME Server can be accessed. For example, it’s possible to control access to the FME Server Web Interface for a specific role.

Each security policy can be set for a particular role, meaning it is applied to all users who are assigned to that role. If one user needs a specific set of security settings, different to any other user in that role, then you simply create a new role to apply to them.

**Other Security Functions**

FME Security can be fully integrated with both Active Directory and Integrated Windows Authentication (IWA). The FME Server Administrators Guide explains how this can be achieved.

**Encryption**

FME Server also allows Secure Sockets Layer (SSL) connections in order to encrypt transaction data. This is most important for ensuring sensitive log in information is not exposed and is particularly important when you are using Active Directory.

Again, the FME Server Administrators Guide explains the steps needed to implement this. In brief the process consists of two steps:
• Modify web service URLs to use HTTPS instead of HTTP
• Enable SSL on the web and/or application server.

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">Judge GIS says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
‘I am the law! The FMESuperUser role is the high court of FME Server
and is granted all permissions on all security settings. What’s more,
these permissions cannot be revoked, unset, or appealed against!
So, be sure not to assign accounts to the FMESuperUser role unless you
really, really mean for them to be given that degree of power.’
</span>
</td>
</tr>
</table>

Follow these steps to inspect different security settings.

**1) Connect to Server – 1**

As in Exercise 1a, connect to the FME Server web user interface in your web browser.

If you are already logged in then log out using the tool in the top-right of the interface:

Now try to log in using the default guest account (Username:guest, Password: guest).

The log in will fail because – by default – this account does not have permission to access the web user interface:

**2) Connect to Server – 2**

Now log in using the default administrator account (Username: admin, Password: admin).

For the purposes of this exercise the account needs to be assigned to a role with permission to manage security. By default only the fmeadmin role has this capability, and the only account assigned to that role is *admin*.

**3) Open Security Settings**

Click Manage on the top right side, and select Administration then Security:

If you don’t see an option for Security then the account you have chosen does not have permissions to access this functionality.

Click on the Role Policies tab and choose the role fmeguest

**4) Examine Security**

Examine the different security options for the fmeguest role. Notice, for example, that it can read the Samples repository, and run a workspace within it, but cannot publish a new workspace and cannot delete an existing one.

At the bottom of the list of security settings, locate Manage Repositories. Put a checkmark to allow the guest role to carry out this function.

Scroll to the top of the list of security settings. Put a checkmark to allow the guest role to use the FME Server Web User Interface. **Also put a checkmark to allow the guest role to use ‘Web Connection, REST Service’.**

**Click the Apply Changes button to apply the new security policies!**

**5) Create New User**

Now let’s create a new user account. Click on the Users tab and then on the New button:

When prompted, create a new user with the following parameters:

User Name: WebGuest
Full Name: Web Interface Account
Roles: fmeguest
Password: WebGuest1

**6) Log In as New User**

Now log out of the web user interface and log in again using the WebGuest account. You should be able to log in, because the setting was changed to allow guest users access to the web user interface.

Notice that the menu options will be severely restricted for this user! Only the Home, Workspaces and Help items will be available, because repositories are the only feature this role is allowed to manage.