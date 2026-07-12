### Troubleshooting Network Rendering Issues

 

#### OctaneRender® Registers One Render Node GPU Out Of A Multiple Number Of Render Node GPUs

Make sure that you are not controlling with the Windows Remote Desktop tool, particularly on Windows® 10 systems. This method allocates one [GPU](javascript:void(0);) to the session, causing OctaneRender to see one GPU over the entire network.

 

#### OctaneRender Registers One GPU Or Some Render Node GPUs But Not All The Render Node GPUs In The Network

You can not activate devices by specifying GPUs directly if these are not activated automatically. If there are some underlying issues in the system already, then devices register inconsistently during startup.

Try unplugging some of the GPUs to see if the computer works fine with less cards, then add more one-by-one to know when the network and system begins to fail. It\'s possible that there is a defective network cable that pulls connection speed down to unexpected lows.

 

#### Primary Node Indicates \"Render Node Failed\" And Render Node Indicates \"Detected Heartbeat Of Render Node Stopped -\> Stopping Render Node\"

Make sure no other program is running on the Render Node or Primary Node machine that could obstruct signals or cause heartbeats to stop. This is the result of antivirus software or the Windows® OS Security measures, which may kill normal operations once it suspects these operations are similar to a computer virus.

 

#### Network Rendering Worked In A Previous Session, But After A Few Days With No Changes To The Machines, The Network Rendering Feature No Longer Works

Ensure that the Render Node daemons in the Render Node machines have appropriate permissions. Try running the Render Node daemons with administrative rights (right click then click on Run As Administrator).

 

For other issues, consult the OctaneRender community board and forums, or contact [\[email protected\]](/cdn-cgi/l/email-protection).
