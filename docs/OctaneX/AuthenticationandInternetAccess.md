OctaneRender® requires authentication with its designated license key and requires internet access on its initial launch. OctaneRender requests your OTOY® credentials and attempts to retrieve an available license from the OctaneRender LiveTM server.

OctaneRender requires one available Standalone license on OctaneRender Live, while plugins require one available standalone license plus one available license for that specific plugin. Standalone licenses are bound to one machine, which means you can share the Standalone license across multiple plugins running on that machine. You can also run multiple instances of Standalone or a plugin on a single machine using the same license.

Closing the application releases the OctaneRender license, similar to a floating license scheme. Standalone edition just releases the standalone license, while plugins release both Standalone and their respective license. In either case, licenses are released if there is not another instance of Standalone or a plugin making use of that specific license. Note the distinctions below between just closing the applications and signing out of the applications.

  -------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
                       Exiting Or Closing The Application                                                                                                                                                                                                                Signing Out
  Standalone Edition   Releases the Standalone license key, except when there is a plugin edition that is also open and still bound to that Standalone license key.                                                                                                      Releases all OctaneRender license keys bound on that machine. If other OctaneRender instances are still running, you will be asked to close them before it can sign out and release all of the licenses.
  Plugin Edition       Releases the license keys bound to the plugin. This includes the Standalone license Key, unless the Standalone edition is open or other plugins are open and their keys are still bound to the same Standalone license key on the same machine.   Releases all OctaneRender license keys bound on that machine. If there are other instances of OctaneRender still running, you will be asked to exit those before it can sign out and release all OctaneRender licenses.
  -------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Deactivating from the [Octane live licenses administration page](https://render.otoy.com/account/octanelive.php?) is not necessary as this is done automatically by the application. This lets you use OctaneRender somewhere else without deactivating any licenses. Licenses in use by older versions have the Deactivate button next to them if you need to release the license. If the application didn\'t close properly from a crash or other circumstances, there is a chance the license isn\'t released. If the same machine accesses the same keys, this is not a problem as the same keys are still bound. The problem arises when you use OctaneRender on another machine, as the keys are still bound to the previous machine. In such cases, failsafe web deactivation unbinds the keys.

### Signing In To The Octane Licensing System

You need an internet connection before starting OctaneRender for the first time in order for it to communicate with the OctaneRender licensing system. When you start the application, this sign-in screen appears.

+-----------------------------------+---------------------------------------------------------+
| ![](images/NewItem_504.png)       | Activation                                              |
|                                   |                                                         |
|                                   | ![](images/Authentication_Internet_Access_Fig01_SE.jpg) |
+-----------------------------------+---------------------------------------------------------+

Figure 1: OctaneRender Activation window

Enter your OTOY account username and password, then click the Sign in button. At this point, the single sign-on and licensing system pulls a valid license key from your account on OTOY's secure server.

If OctaneRender detects a connection problem, make sure all communications use HTTPS (TCP port 443) for the following:

- Standalone edition
- Standalone edition daemon
- Your OctaneRender plugin\'s host application, if you are using a plugin

The above may require updating your firewall settings. If the issue persists, check your proxy settings. Refer to the HTTP Proxy Support topic in this manual for more information.

After signing in, OctaneRender keeps a session alive as long you run the Standalone or the plugin application on a regular basis. In most cases, you should not have to sign in to the OctaneRender licensing system again. This session also lets you link your local installation to other OTOY services like [The Render Network®](https://rendernetwork.com/) (TRN).

### Offline Authentication And Offline Licensing Mode

Offline authentication and offline licensing mode uses an offline license dongle to run your OctaneRender applications, regardless if your machine is connected to the internet. However, you need an internet connection to access the LiveDB asset database.

To set up your dongle with an offline license, you need to connect the dongle to an internet-connected PC and assign an OctaneRender license to the dongle. After you\'ve assigned your license to the dongle via your online OTOY user account, you can move the dongle to the offline machine and use it to authenticate the OctaneRender application without the internet connection. While the dongle is in use on an offline machine, the OctaneRender license assigned to that dongle is locked to that current machine in offline licensing mode. You can not use the offline license on any other machine until you sign out of OctaneRender and remove the dongle from the offline machine.

If you run your application with offline licensing for a long time, the licensing system closes the session, and you need to refresh the dongle.

+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
|                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| When using offline licensing for long period of time with no internet connection or no usage, OctaneRender will ask you for credentials again. This is because OctaneRender needs an active session for online licenses with the license server, or the dongle if using offline licensing, in order to retrieve the new license and yours might have expired, so in order to retrieve or refresh the license from our servers, your user information is required. |
+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

By default, offline licensing mode is not enabled. For more information about the offline licensing, contact us at [\[email protected\]](/cdn-cgi/l/email-protection#86eee3eaf6c6e9f2e9ffa8e5e9eb).

+-------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                  |
|                                                                                                       |
| Existing online licenses can be converted to offline licenses, but this conversion in not reversible. |
+-------------------------------------------------------------------------------------------------------+

### Manually Signing Out Of The OctaneRender® Licensing System

To close a session, go to the OctaneRender Authentication Management window by selecting Account from the File menu, then click the Sign Out button. This closes the current session and releases all licenses bound to the current machine. You must close all OctaneRender applications before continuing to sign out.

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_505.png)       | Activation Status                               |
|                                   |                                                 |
|                                   | ![](images/AuthenticationandInternet2_SEv4.png) |
+-----------------------------------+-------------------------------------------------+

Figure 2: OctaneRender Authentication Management window

### OctaneRender License Management

OctaneRender manages licenses several ways:

- If you have the Standalone edition, you must have one Standalone license to run the application.
- For each OctaneRender plugin you have, you must have a Standalone license and one license for that plugin to run it.
- You must have one Standalone license for each machine you run OctaneRender products on.
- You can run any number of Standalone and OctaneRender instances on one machine.

### Failsafe Web Deactivation (Unlocks)

Licenses deactivate when you shut down the OctaneRender application. However, if your machine crashes and your application does not close properly, the license may still be active on your machine. In this case, you need to restart the application again to release the license. Other scenarios that could prevent the license from deactivating your license includes:

- The hard disk containing your OctaneRender license data has crashed and you replace it.
- You erase the hard disk - for example, as part of a disk reformat or partition change.
- You change the network interface card and your network identification data changes for that machine.
- The OctaneRender license data on your machine is corrupt.

In all of these situations, the OctaneRender licensing system thinks your license is still active on that machine, but you and the licensing system are no longer able to access the license data. However, you can still deactivate your license using failsafe web deactivation.

+------------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                             |
|                                                                                                                  |
| Unlocking is only available for OctaneRender v3 licenses or higher. You can deactivate OctaneRender v2 licenses. |
+------------------------------------------------------------------------------------------------------------------+

In version 2 of the OctaneRender licensing system, OTOY creates a license key (a combination of a 12-digit user ID and an alphanumeric password) and assigns it to you. You can find the keys assigned to you by logging on to the customer area on the OctaneRender homepage using your OTOY credentials:

+-----------------------------------+-----------------------------------+
| ![](images/NewItem_591.png)       | Version 2                         |
|                                   |                                   |
|                                   | ![](images/V2.png)                |
+-----------------------------------+-----------------------------------+

Figure 4: Entering your username and password credentials

Once your account is activated, you must provide these authentication credentials each time you start OctaneRender.

+--------------------------------------------------------------------------------------------------------------+
| NOTE                                                                                                         |
|                                                                                                              |
| For licenses in use by older versions, you will still see the Deactivate option as they need to be released. |
+--------------------------------------------------------------------------------------------------------------+

### OctaneRender Live IP/URL Whitelisting

These are the URLs that OctaneRender requires access to as part of the activation process:

- account.otoy.com
- grpc.octanerender.com
- bridge.octanerender.com
- live.octanerender.com

As the services above use dynamic load-balancing, the IPs of these servers often change. If you are whitelisting by IP, you need to redirect traffic through our gateway server at 52.1.219.88. You can do this by overriding the octanerender.com domain on your internal DNS server, or by setting the IP manually in your machine\'s hosts file.

Host file locations:

- Windows®:C:\\Windows\\System32\\drivers\\etc\\hosts
- macOS®:/private/etc/hosts
- Linux:/etc/hosts

Host file entries:

3.33.213.211 account.otoy.com

75.2.18.158 account.otoy.com

 

13.248.248.116 grpc.octanerender.com

76.223.125.238 grpc.octanerender.com

 

76.223.55.208 live.octanerender.com bridge.octanerender.com

15.197.165.125 live.octanerender.com bridge.octanerender.com

If you have any problems, contact us [here](/cdn-cgi/l/email-protection#42313732322d3036022d2136232c2730272c2627306c212d2f).

### Unattended/Silent Authorization (Online Mode Only)

Another option for authorization is using an unattended authorization token. This allows OctaneRender to activate in online licensing mode without requiring you to enter in a username and password. This works by saving an authorization file downloaded from our SSO system to every machine that runs OctaneRender in a user-agnostic directory. This authorization file can be configured to only be valid for requests from a specific CIDR, preventing this file from being used outside your environment.

If the authorization file does not exist on a machine, you can still run OctaneRender, but you need to enter the username (or login email address) and password.

As this feature has security implications for the licenses in your account, you will need to contact support to request that this feature be enabled for your account. As this feature is an extension of online licensing mode, it requires an active internet connection to function. To request this feature, contact us [here](/cdn-cgi/l/email-protection#4a222f263a0a253e253364292527).
