If you run OctaneRender® behind an existing proxy, OctaneRender tries to find and use your current proxy setup. Workarounds to bypass the proxy settings are invalid.

If you are trying to setup your proxy for the first time or your proxy requires authentication, you may configure it either by using your operating system proxy settings or environment variables.

### Proxy Server Configuration Via System Settings

This option allows OctaneRender to retrieve your system settings. The configuration depends on your host operating system.

#### Windows®

OctaneRender can obtain its proxy configuration several different ways.

From Internet Explorer\'s LAN Settings, this configuration applies only to the current user. To change IE proxy settings:

1.  1.  Press the Win+R keys.
    2.  Enter inetcpl.cpl,4 and click OK. The Internet Properties window displays.
    3.  Click LAN Settings.
    4.  Select the Use A Proxy Server For Your LAN checkbox.
    5.  In the Address box, enter the proxy server\'s IP address.
    6.  In the Port box, enter the port number.

If you have a dedicated proxy for HTTPS traffic, click on Advanced, clear the Use The Same Proxy For All Protocols checkbox, and specify the proxy address and port for the Secure server type.

##### From The WinHTTP Configuration

This configuration is system-wide, and stored in the registry. You can manage it using netsh winhttp. For more information, please check Windows HTTP documentation from Microsoft®. The proxy exceptions list is ignored.

#### macOS®

OctaneRender reads the proxy settings stored in System Preferences. To change your proxy settings:

1.  1.  Open System Preferences.
    2.  Click on Network.
    3.  Click on Advanced \...
    4.  Click on the Proxies tab.
    5.  Choose either Web proxy (HTTP) or Secure web proxy (HTTPS) depending on your proxy type.
    6.  In the Web Proxy Server section, enter your server\'s IP address and port number.

OctaneRender does not support bypassing proxy settings. Port numbers default to 80 if you\'re using HTTP, and 443 if you\'re using HTTPS.

Macintosh® systems don\'t support the proxy authentication through proxy settings. If your proxy requires a username and password, please refer to the following section about proxy configuration via environment variables.

#### Linux

The proxy settings can vary between distributions, so proxy configuration on Linux is supported via environment variables.

OctaneRender supports the following proxy environment variables:

- https_proxy: Specifies a proxy server for HTTPS network traffic.
- all_proxy: Specifies a proxy server for all network traffic.

These are commonly used environment variables for specifying proxy configuration, specially on Linux. This may affect other applications that use these proxy configurations. If one of these variables are found, they will override your system\'s proxy preferences, even if there\'s already a configured proxy.

+----------------------------------------------------------------------------------+
| NOTE                                                                             |
|                                                                                  |
| Environment variables are case sensitive, even on Windows, for security reasons. |
+----------------------------------------------------------------------------------+

The accepted syntax for proxy environment variables is \[protocol://\]\[user:password@\]proxyhost\[:port\]

For example, you may specify a proxy for HTTPS network traffic as https_proxy=johndoe:[\[email protected\]](/cdn-cgi/l/email-protection). This tells OctaneRender to use 127.0.1.50 as your proxy\'s address using the default port 80, and authenticate as user johndoe with password mypass.
