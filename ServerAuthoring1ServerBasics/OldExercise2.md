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