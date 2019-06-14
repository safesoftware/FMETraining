<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Changing the FME Server Database Provider</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">C:\Program Files\FMEServer\Server\database\sqlserver\sqlserver_createDB.sql
<br>C:\Program Files\FMEServer\Server\database\sqlserver\sqlserver_createUser.sql</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Change the database provider for FME Server</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Configuring a new SQL Server database</td>
</tr>

</table>

---

Your company has an Express Installation of FME Server already installed, but your Database Administrator has just informed you that you that the company will be switching its database providers from the default FME Database to a SQL Server database to allow for more control over database security.

---

<!--<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">FME Lizard says...</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
If you have completed the Configuring for HTTPS exercise, remember that the URL to connect to FME Server is now </span><span style="font-family:serif; font-style:italic; font-weight:bold; font-size:larger">https://localhost:8443/fmeserver</span><span style="font-family:serif; font-style:italic; font-size:larger"> and NOT http://localhost/fmeserver!
</span>
</td>
</tr>
</table>-->


<br>**1) Backup FME Server**
<br>Backing up your current FME Server instance is an important step before performing any post-installation configurations. Once you have changed the database provider, you can restore FME Server configurations all at once instead of having to go through the process of manually changing any settings, republishing workspaces, etc.

Note: If you have *already created an FME Server backup* you can use this existing .fsconfig file and continue to Step 2.

Open the FME Server web interface, either through the Web Interface option on the Windows Start Menu or directly in your web browser, and log in using the username and password *admin*.

Find **Backup & Restore** in the left sidebar, under the Admin heading in the FME Server web interface, and click to expand, then click **Backup**.

Select *Download* to save a backup file of FME Server - this can be thought of as a "snapshot." It will take a short time to run processes in the background to compile the FME Server backup, and once this is complete, it will automatically save to your local downloads folder.

---

<!--Tip Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
If you have a PostgreSQL installation instead of SQLServer, you can follow the instructions in the <a href="https://safe-software.gitbooks.io/fme-server-administration-training-2017/content/ServerAdmin4Scalability/Exercise2_SwitchingToAPostgreSQLDatabaseWithWindowsSystem.html">Server Administrator 2017 Course</a>. Just note that the path names might have changed slightly since 2017.
</span>
</td>
</tr>
</table>

<br>**2) Initial Database Configuration**
<br>For the purposes of this exercise a separate SQL Server database has been installed to the Training Machines.

The two SQL scripts we'll be using for this step and the next (3) can be found at: **C:\Program Files\FMEServer\Server\database\sqlserver\**
  - sqlserver_createDB.sql
  - sqlserver_createUser.sql

We need to create the FMESERVER database schema by configuring the local SQL Server database for FME Server. From the Windows Start Menu open **Command Prompt**.

<!--**Create the FMESERVER database schema**: The next step is to configure the local SQL Server database for FME Server. From the Windows Start Menu, open **Command Prompt**. -->

First, create a new database using the sqlserver_createDB.sql script.  You can review the SQL scripts in a text editor if you wish, but it isn't necessary. In the **Command Prompt** run the following:

    sqlcmd -S FMETRAINING\SQLEXPRESS -i "C:\Program Files\FMEServer\Server\database\sqlserver\sqlserver_createDB.sql"

![](./Images/4.211.Ex2.CommandPrompt1_fmeserver.png)

The output should look like this now in the **Command Prompt** window:

![](./Images/4.212.Ex2.CommandPrompt2_fmeserver.png)

This confirms the new Database "fmeserver" was created.  This SQL script creates all FME Server related tables, indexes, views, and triggers.


<br>**3) Create the FME Server Database User**

Next, we will create the new user *fmeserver* and grant all necessary permissions to the new user.
This SQL script creates a new user *fmeserver* with password *fmeserver*.  It uses the sqlserver_createUser.sql script.

    sqlcmd -S FMETRAINING\SQLEXPRESS -i "C:\Program Files\FMEServer\Server\database\sqlserver\sqlserver_createUser.sql"

The new user will be created with the appropriate login and permissions to access the *fmeserver* database.

![](./Images/4.213.Ex2.CommandPrompt3_fmeserver.png)
<br>Exit the **Command Prompt**.

<!-- May add SQL Server Studio steps to confirm database and user was created successfully.  This is optional to include but would help a new user confirm the database and user were created. -->

<br>**4) Configure the Database Connection**
<br>Open the *fmeCommonConfig.txt* file, located in the *C:\Program Files\FMEServer\Server\\* directory, using a text editor in administrator mode.

Under the heading *FME SERVER SETTINGS START*, locate the section titled *Database Connection*. We want to disable the default connection to the Postgres database and instruct FME Server to connect to the SQL Server database.

Comment out the *DB_TYPE=postgresql* section, by adding a number sign (#) in front of each line and uncomment the *DB_TYPE=sqlserver* section.  The final edits should look at as follows:

    #DB_TYPE=postgresql
    #DB_DRIVER=org.postgresql.Driver
    #DB_JDBC_URL=jdbc:postgresql://localhost:7082/fmeserver
    #DB_USERNAME=fmeserver
    #DB_PASSWORD=fmeserver
    #DB_CONNECT_EXPIRY=60
    #DB_SQLSTMTS_PATH=C:/Program Files/FMEServer/Server/database

    DB_TYPE=sqlserver
    DB_DRIVER=com.microsoft.sqlserver.jdbc.SQLServerDriver
    DB_JDBC_URL=jdbc:sqlserver://localhost:1433;databaseName=fmeserver
    DB_USERNAME=fmeserver
    DB_PASSWORD=$FME$1ser$ver
    DB_CONNECT_EXPIRY=60
    DB_SQLSTMTS_PATH=C:/Program Files/FMEServer/Server/database


Save and close the *fmeCommonConfig.txt* file.

<br>**5) SQL Server Modifications**

From the Start menu, Open **Microsoft SQL Server 2016 &#62; SQL Server Management Studio**
Accept the default server name *FMETRAINING* and *Windows Authentication* and click **Connect**.

![](./Images/4.214.Ex2.SQLServer_Login.png)

The first step is to set the Database Server to allow for SQL Server Authentication. This will permit the new *fmeserver* user to connect to the database.

In the *Object Explorer* tree right-click on the **FMETRAINING** and select *Properties*.

![](./Images/4.216.Ex2.SQLServer_Properties2.png)

In the resulting dialog click on *Security* and select the *SQL Server and Windows Authentication* option.

![](./Images/4.217.Ex2.SQLServer_Properties3.png)

Click OK, acknowledging that SQL Server requires a restart.

![](./Images/4.218.Ex2.SQLServer_Properties4.png)

In the *Object Explorer* tree right-click on the **FMETRAINING** and select *Restart*.

![](./Images/4.219.Ex2.SQLServer_Properties5.png)

And when prompted click *Yes*.

![](./Images/4.220.Ex2.SQLServer_Properties6.png)


 Finally, **Restart FME Server**.  From the start menu select **FME Server 2019.0.0.3 &#62; Restart FME Server**.


<br>**6) Post-Configuration Script**
<br>Starting in 2018.0 the Post-Configuration scripts are now run by the Core when connecting to a new FME Server System Database. There is one script that still needs to be run (step follows Add Queue).  Allow a few minutes for the scripts to run and complete loading the new metadata into the database.  Attempting to log in during this time may result in an incomplete Web UI appearing. Wait a few moments and refresh the browser.
<br> <br>

Next, **Restart FME Server**.  From the start menu select **FME Server 2019.0.0.3 &#62; Restart FME Server**.

<br>**7) Restore Your FME Server Configuration**
<br>Since a backup of FME Server was created in Step 1, we can now restore that same FME Server instance which contains all of the previous FME Server configuration settings.

Login to the FME Server web interface and select **Backup & Restore &gt; Restore** from the left sidebar.

Upload your saved backup configuration file from the beginning of this exercise. Navigate to *C:\Users\Administrator\Downloads\\* and locate the FME Server backup file (Hint: It has *.fsconfig* extension!). Drag-and-drop this file onto the FME Server Restore page:

![](./Images/4.209.Ex2.RestoreConfiguration.png)

The FME Server web interface will report if the restore is successful. If it is not, the log file is easily accessible from this page if further investigation is needed.

![](./Images/4.210.Ex2.RestoreSuccess.png)

<!--<br>**8) Update Service URLs to HTTPS**
Finally, since restoring the configuration does not update the service URLs we must redo the step from Chapter 3, Exercise3.  The reason the service URLs are not updated when restoring a configuration is that we may be restoring to an entirely different system with different URLs.

<br>To enable SSL for FME Server Services, login to the FME Server web interface (username and password *admin*), and select **Services** on the left sidebar.

![](./Images/4.221.Ex2.ServicesButton.png)

On the *Services* page, you can update specific services or all services at once. Let's update all services. Click **Change All Hosts**

![](./Images/4.222.Ex2.ChangeAllHosts.png)

The *Change All Hosts* dialog opens. Make sure **Host** is set to _https://localhost:8443_ and click **OK**.

![](./Images/4.223.Ex2.ChangeAllHosts2.png)

The URLs will be updated to their new, correct values on the Services page.

![](./Images/4.224.Ex2.NewServiceURLs.png)
-->
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
<ul><li>Change the database provider for FME Server</li></ul>
</span>
</td>
</tr>
</table>
