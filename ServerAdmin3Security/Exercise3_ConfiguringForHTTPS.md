<!--Exercise Section-->

<table style="border-spacing: 0px;border-collapse: collapse;font-family:serif">
<tr>
<td width=25% style="vertical-align:middle;background-color:darkorange;border: 2px solid darkorange">
<i class="fa fa-cogs fa-lg fa-pull-left fa-fw" style="color:white;padding-right: 12px;vertical-align:text-top"></i>
<span style="color:white;font-size:x-large;font-weight: bold">Exercise 3</span>
</td>
<td style="border: 2px solid darkorange;background-color:darkorange;color:white">
<span style="color:white;font-size:x-large;font-weight: bold">Configuring FME Server for HTTPS</span>
</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Data</td>
<td style="border: 1px solid darkorange">N/A</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Overall Goal</td>
<td style="border: 1px solid darkorange">Change access to the FME Server Web User Interface to HTTPS</td>
</tr>

<tr>
<td style="border: 1px solid darkorange; font-weight: bold">Demonstrates</td>
<td style="border: 1px solid darkorange">Creating a self-signed certificate and importing into the FME Server keystore</td>
</tr>

</table>

---

Your company is rapidly expanding and hiring many new employees. Now, instead of having everyone able to access to FME Server, you have set up logins so only trusted personnel have access. You also want to set up extra precautions to keep the transferred information secure.

HTTPS ensures that communication between the client and the server is encrypted, so that if it is intercepted, the third party cannot easily view or use the information. For FME Server, you can use HTTPS to ensure that sensitive login information is not exposed.

For any HTTPS (SSL) page, a certificate is required. For development and testing purposes, self-signed certificates are supported. For production use, we recommend that you use SSL certificates from a verified SSL certificate authority (CA).


<br>**1) Create a Keystore File**
<br>First, you must generate a keystore that contains a certificate chain using the Java Keytool from the Java Developer Kit (JDK).

Open a **Command Prompt** and run as administrator.

Navigate to the Java bin directory (*C:\apps\FMEServer\Utilities\jre\bin\\*)

Run the following command to create a new keystore file:

	keytool -genkey -alias tomcat -keyalg RSA -keystore tomcat.keystore
 
Set a password for the new keystore and specify the server domain name (for example, *localhost*) as your first and last name.

Enter *yes* when prompted if inputs are correct.

When prompted for the password for the alias &lt;tomcat&gt;, press RETURN.

A new keystore is created in *C:\apps\FMEServer\Utilities\jre\bin\\*

Copy the new keystore file to the tomcat directory in the FME Server installation: *C:\apps\FMEServer\Utilities\tomcat\\*

![](./Images/3.404.ConfigureForHTTPS_createKeytool.png)


<br>**2) Working with the Certificate** 
<br>The new keystore must be imported into the FME Server keystore for trusted certificates. In the command prompt, enter the following command:

	keytool -importkeystore -srckeystore tomcat.keystore -destkeystore C:\apps\FMEServer\Utilities\jre\lib\security\cacerts

You will be prompted to enter two passwords. One for the destination keystore and one for the source keystore. The password for the destination keystore is **changeit**. The password for the source keystore is the password that was specified in Step 1 above.

![](./Images/3.405.ConfigureForHTTPS_selfSignedCertificate.png)

---

<br>**Configuring Tomcat**
<br>In the next steps, we need to modify three configuration files of Apache Tomcat. All three files are located in the FME Server installation directory: *C:\apps\FMEServer\Utilities\tomcat\conf\\* 

It is a good idea to make copies of any files you will be changing and hold them in a separate directory until you have verified that the edits are working successfully.

---

<br>**3) Configure server.xml**
<br>Open the *server.xml* file in a text editor in administrator mode.

Locate the *SSLEngine* setting in the *&lt;Listener&gt;* element, including *className="org.apache.catalina.core.AprLifecycleListener"* and change the *“on”* value to *“off”*.

Locate the *&lt;Connector&gt;* element that contains *protocol="org.apache.coyote.http11.Http11NioProtocol"* and replace it with the following:

		<Connector protocol="org.apache.coyote.http11.Http11NioProtocol"
		port="8443" minSpareThreads="5"
		enableLookups="true" disableUploadTimeout="true"
		acceptCount="100" maxThreads="200"
		scheme="https" secure="true" SSLEnabled="true"
		keystoreFile="<FMEServerDir>\Utilities\tomcat\tomcat.keystore"
		keystorePass="<your_password>"
		clientAuth="false" sslEnabledProtocols="TLSv1,TLSv1.1,TLSv1.2"
		sslImplementationName="org.apache.tomcat.util.net.jsse.JSSEImplementation"
		ciphers="TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256,TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA,
		TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384,TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA,
		TLS_RSA_WITH_AES_128_GCM_SHA256,TLS_RSA_WITH_AES_256_GCM_SHA384,
		TLS_RSA_WITH_AES_128_CBC_SHA256,TLS_RSA_WITH_AES_256_CBC_SHA256,
		TLS_RSA_WITH_AES_128_CBC_SHA,TLS_RSA_WITH_AES_256_CBC_SHA,
		SSL_RSA_WITH_3DES_EDE_CBC_SHA"
		URIEncoding="UTF8" />
 
		<Connector port="80" protocol="HTTP/1.1"
		redirectPort="8443"/>
		
Make sure to change *&lt;FMEServerDir&gt;* and *&lt;your_password&gt;* with the install directory of FME Server and the password of the keystore that was specified in Step 1.

Save and close the *server.xml* file.


<br>**4) Configure web.xml**
<br>Open the *web.xml* file in a text editor in administrator mode.

Add the following code block to the end of the file, just before the closing *&lt;/web-app&gt;* element:

		<security-constraint>
		<web-resource-collection>
		<web-resource-name>HTTPSOnly</web-resource-name>
		<url-pattern>/*</url-pattern>
		</web-resource-collection>
		<user-data-constraint>
		<transport-guarantee>CONFIDENTIAL</transport-guarantee>
		</user-data-constraint>
		</security-constraint>

Save and close the *web.xml* file.


<br>**5) Configure context.xml**
<br>Open the *context.xml* file in a text editor in administrator mode.

Add the following to the end of the file, just before the closing *&lt;/context&gt;* element:

		<Valve className="org.apache.catalina.authenticator.SSLAuthenticator"
		disableProxyCaching="false" />

Save and close the *context.xml* file.


<br>**6) Verify the Configuration** 
<br>Now that we have made our changes, we want to verify that HTTPS was configured correctly for FME Server.

**Restart the FME Server Application service.**

Open a browser and navigate to *https://localhost:8443/*. 

You should see the FME Server login page in a secured format.

![](./Images/3.406.verifyConfiguration.png)

Note: If a self-signed certificate is used for testing, your browser may report the page as not secure:

![](./Images/3.411.ConnectionNotSecure_Warning.png)

For self-signed certificates, click the **Advanced** button and add an exception for *https://localhost:8443/*.


<br>**7) Modify Service URLs to Use HTTPS** 
<br>To enable SSL for a service, login to the FME Server Web User Interface (username and password *admin*), and select **Services** on the left sidebar. 

![](./Images/3.407.ServicesButton.png)

On the *Services* page, you can update specific services or all services at once. Let's update all services. Click **Change All Hosts**

![](./Images/3.413.ChangeAllHosts.png)

The *Change All Hosts* dialog opens. Make sure **Host** is set to *https://localhost:8443* and click **OK**.

![](./Images/3.414.ChangeAllHosts2.png)

Check on the *Services* page that your update worked.

![](./Images/3.410.checkItWorked.png)

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
<ul><li>Create a self-signed certificate</li>
<li>Import a certificate in the FME Server Java keystore</li>
<li>Change FME Server Web Services to use HTTPS URLs</li></ul>
</span>
</td>
</tr>
</table>
