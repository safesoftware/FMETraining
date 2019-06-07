<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 2</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Changing the Service Account running the FME Server Services</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Change the services to run under a Service Account vs Local Systems</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Changing the Logon account for the Core, Engines and Web Application Server to a Service Account</td>
</tr>

</table>

---
<!--Person X Says Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-quote-left fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">This exercise is for demonstration purposes only</span>
</td>
</tr>
</table>


This lab uses the Administrator account used to log into the training machine as the Service Account, however this account should ideally be an account created specifically for running the fme services. Group Managed Service Accounts are also an option if preferred.


---

<br>**1) Open Services Desktop App**
<br> Search and launch Services from the windows menu.


<br>**2) Find the FME Services**
<br> Search for the four "FME Server" Services FME Server Core, FME Server Database, FME Server Engines and FME Server Application Server.  


<br>**3) Change the Log On Account**
<br>

- Stop the FME Server Services

- Right click on the service and select properties and open the **Log On** tab.

- Select **This Account** and click Browse

- Type **Administrator** in the object name. Select the account and use the password **FMElearnings#1**

- Select **OK**

- Start the services in the following order:
    1. FME Server Database
    2. FME Server Core
    3. FME Server Engine
    4. FME Server Application Server





<!--Tip Section-->

<table style="border-spacing: 0px">
<tr>
<td style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-info-circle fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold;font-family:serif">TIP: Import Error</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange">
<span style="font-family:serif; font-style:italic; font-size:larger">
In order to assure the services are started in the right sequence use the Start FME Server application icon.
</span>
</td>
</tr>
</table>

---



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
<ul><li>Change the account running Services</li>
<li>Restart the Services individually</li></ul>
</span>
</td>
</tr>
</table>
