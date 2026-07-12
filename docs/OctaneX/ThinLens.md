The Thin Lens camera is the typical camera type used for most rendering scenarios.

+-----------------------------------+--------------------------------------+
| ![](images/NewItem_384.png)       | Thin Lens Parameters                 |
|                                   |                                      |
|                                   | ![](images/ThinLens_Fig1_SE2018.jpg) |
+-----------------------------------+--------------------------------------+

Figure 1: The parameters of the Thin Lens camera in the Node Inspector

### Thin Lens Parameters

Orthographic - The camera shows an orthographic view. If disabled, the camera shows a perspective view.

#### Physical Camera Parameters

Sensor Width - The sensor or film width, in millimeters.

Focal Length - The lens focal length, in millimeters.

F-Stop - The aperture-to-focal-length ratio.

#### Viewing Angle

[Field Of View](javascript:void(0);) - Sets the horizontal field-of-view for the camera in the scene, measured in degrees. Large values let the camera see more of the scene, and smaller values make the camera see less of the scene.

Scale Of View - Sets the camera\'s orthographic view width in meters.

Distortion - Adjusts the spherical and cylindrical distortion. The rendered image displays the entire sphere and uses equidistant cylindrical projection, also known as lat-long projection.

Lens Shift - This is useful if you want to render images of tall buildings/structures from a similar height as the human eye, but keep the vertical lines parallel.

Perspective Correction - If Up-Vector is vertical, enabling this option keeps vertical lines parallel.

Pixel Aspect Ratio - Squashes or stretches the depth-of field disc and renders it to a non-square pixel format (like NTSC or PAL).

#### Clipping

Near Clip Depth - Distance from the camera to the nearest clipping plane, measured in meters.

Far Clip Depth - Distance from the camera to the farthest clipping plane, measured in meters.

#### Depth of Field

Auto-Focus - Keeps the focus on the closest visible surface at the center of the image, regardless of the aperture, the aperture edge, and focal depth values. This setting is on by default.

Focal Depth - The depth of the plane in focus, measured in meters. If you are having trouble seeing a result when you adjust this setting, double-check to make sure that Auto-Focus is enabled. Auto-Focus overrides the Focal Depth setting.

[Aperture](javascript:void(0);) - The radius of the camera\'s lens opening, measured in centimeters. Low values have a wide depth-of-field, where everything is in focus. High values have a shallow depth-of-field, where objects in the foreground and background will be out of focus.

Aperture Aspect Ratio - This allows users to squash and stretch the depth-of-field disc.

Aperture Edge - This controls aperture edge detection at all points within the aperture. Lower values give more pronounced edges to out-of-focus objects affected by the a shallow depth-of-field, such as objects in the foreground and background. The aperture edge modifies the depth-of-field\'s bokeh effect. High values increase the contrast towards the edge.

Bokeh Side Count - The number of edges making up the bokeh shape.

Bokeh Rotation - The bokeh shape orientation.

Bokeh Roundedness - The roundness of the bokeh shape\'s sides.

#### Position

Position - The camera\'s X,Y,and Z positions in the scene.

Target - The target position where the camera is pointed in the scene.

Up-Vector - The camera\'s up direction in the scene. The default setting is in the Y-direction (0, 1, 0).

#### Stereo

Stereo Output - This specifies the output rendered in stereo mode.

- - Left - Renders the left eye image.
  - Right - Renders the right eye image.
  - Side-By-Side - Renders the scene as a pair of two-dimensional images.
  - Anaglyphic - Makes the render viewable with red/blue 3D glasses.
  - Over-Under - The pair of two-dimensional images is placed one above the other for special viewers.

Stereo Mode - Determines whether the stereo mode is off-axis or parallel.

Eye Distance - The distance between the left and the right eye in stereo mode, measured in meters.

Swap Eyes - This swaps left and right eye position when stereo mode is showing both.

Left Stereo Filter/Right Stereo Filter - The left and right filter colors used to create the anaglyphic stereo effect in the render.
