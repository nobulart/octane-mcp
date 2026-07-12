Sometimes using more than two video cards causes Windows® and the NVIDIA® driver to register all cards, but OctaneRender® does not see them. You can fix this by updating the registry. This involves adjusting critical OS files, which we do not support.

1.  1.  Start the registry editor (press the Start button, then type \"regedit\" to launch it.)
    2.  Navigate to the following key: HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4D36E968-E325-11CE-BFC1-08002BE10318}
    3.  You will see keys for each video card starting with 0000, then 0001, etc.
    4.  Under each of the keys identified in step 3 for each video card, add two DWORD values: DisplayLessPolicy and LimitVideoPresentSources, and set each value to 1.
    5.  Once you add these to each video card, shut down Regedit and then reboot.

OctaneRender® should now see all video cards.
