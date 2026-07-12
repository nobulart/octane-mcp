### Uploading VR Quality Synthetic Rendered Images To The Samsung Galaxy Gear VR

If you are rendering images for viewing on the Gear VR headset, make sure the images have the following requirements:

- - 18K Cube map renders
  - Stereo images rendered via a stereoscopic panoramic camera with a Cube map projection of equal sides (+x,-x,+y,-y,+z,-z)
  - Image saved as an 8-bit PNG

After rendering an image via OctaneRender®, you can upload and view this image on the Gear VR by following these steps:

1.  1.  Download and install the OTOY® [ORBX](javascript:void(0);) Media Player from the Oculus Store onto your Samsung smartphone. Additional content can be downloaded from <http://m.otoy.com/media/ORBX.zip> as well, and added by unzipping the media archive and placing the resulting files on your phone under the ORBX/Media directory.
    2.  To start uploading your own rendered image, connect the data cable from the phone to your PC.
    3.  Copy the image and add it into your phone's ORBX/Media directory.
    4.  Attach the phone to the Gear VR headset.
    5.  Wearing the headset, navigate to the ORBX player. At this point, the ORBX player detects the just-uploaded PNG file, then it generates the JSON file, which includes the name of the PNG file, the author, and other data. Then it loads the thumbnail picked up from the JSON file, along with all the other thumbnails in its Media directory, and displays these in a menu.
    6.  Locate your new image among the loaded images.

The updated build of the ORBX Media Player also supports both ZIP packages and ORBX®, and has new features to support ORBX® videos and interactive media. You can stitch 18K Cube map renders together to create videos using high-level JSON/[Lua](javascript:void(0);) fields. For a sample project using Lua and some sample content, go here: <https://render.otoy.com/forum/download/file.php?id=46517>.

To learn more about the ORBX Player, watch this video (<https://www.youtube.com/watch?v=0LLHMpbIJNA>) from the 11:11 - 15:24 mark.

 

### FAQ

#### Is Running An 18k Cube Map Sequence Longer Than 11 Frames Possible? Is There A Limit?

To load more than a few dozen SCM frames, you need to compress and package them as OKX compressed textures, which we do on ORCTM right now for each specific platform/[GPU](javascript:void(0);) combo we support in the player (GVR only). OKX for mobile takes a while to encode - up to nine minutes per frame. If you render on ORCTM, this can be done between frames.

We are adding script nodes (see above post) that accept Camera node inputs for a set of keyframes on a path, and ORCTM can generate the in-between frames for you. Right now, if you send a stereo Cube map ORBX to ORCTM and render it, you can also package and compress it to an ORBX file, which can load in your scene or play back as a video file in the player.

 

#### Can I Brand The ORBX Viewer To Make Our VR Panoramas Appear More Valuable/Professional As Opposed To Placing Them As One Of Many Apps In A Main Entertainment-Oriented Interface?

We are working on signed/certs for ORBX media packages. If you use OMP to load an ORBX link or a local file (via android intent, icon shortcut, shell app, URL web link, etc.), it will bypass the home screen/media browser and run the ORBX project as if it were a standalone app. This is also how it works on the PC.

Packaging your project folder as a ZIP works well in the current app for things like images and scripts, but it can break other media, depending on the ZIP software you use. The reason we have ORBX containers is they are meant to be packaged by our software for the target device in order to make sure the assets work at their optimum. We are also adding digitial signatures, encryption, and buffered streaming cache to ORBX containers that is based on your OctaneRender® ID and the settings you set for the package. If you launch a signed ORBX file with the player (via a URI request or android intent from another app, for example), you bypass the home screen and run the ORBX content with whatever other paramaters the URI defines.

 

#### Will ORBX Viewer 3 Also Allow Precise Hotspot Positioning And The Ability To Use PNG Sequences For Animated Hotspots?

The ORBX 3 player adds support for Mesh layers (including hidden bounding box of scene objects) exported from OctaneRender® v3. You can use this for precise and almost automatic hotspot scene authoring. The hotspot metadata could be handled in a Script node you attach to the object layer.
