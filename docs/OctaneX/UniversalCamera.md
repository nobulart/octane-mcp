The Universal camera is a full-featured camera, with support for five different camera types:

- Thin lens
- Orthographic
- Fisheye
- Equirectangular
- Cubemap

+-----------------------------------+-------------------------------------------------+
| ![](images/NewItem_385.png)       | Universal Parameters                            |
|                                   |                                                 |
|                                   | ![](images/Universal_Camera_Fig01_SE_v2020.jpg) |
+-----------------------------------+-------------------------------------------------+

Figure 1: Universal Camera parameters

### Universal Camera Parameters

#### Physical Camera Parameters

Sensor Width - The film\'s or sensor\'s width in millimeters.

Focal Length - The lens\'s focal length in millimeters.

F-Stop - The aperture-to-focal-length ratio.

#### Viewing Angle

[Field Of View](javascript:void(0);) - The horizontal field-of-view, measured in degrees.

Scale Of View - The width of the orthographic view, measured in meters.

Lens Shift X - The lens shift on X, as a factor of the image width.

Lens Shift Y -- The lens shift on Y, as a factor of the image height.

Pixel Aspect Ratio - The pixels\' X:Y aspect ratio.

#### Fisheye

Field Of View - The camera\'s field of view, measured in degrees.

Fisheye Type - Choose between covering the lens circle in the sensor, or covering the whole sensor.

Hard Vignette - Renders the lens (Circular fisheye only).

Fisheye Projection - The projection function used for the fisheye.

#### Panoramic

Horizontal Field of View - The horizontal field of view, in degrees. This sets the X-coordinate for the camera\'s horizontal field of view in the scene. This is ignored when cube mapping is used.

Vertical Field of View - The vertical field of view, in degrees. This sets the Y-coordinate for the camera\'s vertical field of view in the scene. This is ignored when cube mapping is used.

Cubemap Layout - Determines the configuration for laying out the cubemap.

Equi-angular Cubemap - Activates an equi-angular cubemap projection.

#### Distortion

Use Distortion Texture - Enables the distortion texture.

Distortion Texture - The Distortion texture input.

Spherical Distortion - The amount of spherical distortion.

Barrel Distortion - Straight lines appear curved.

Barrel Distortion Corners - Straight lines appear curved, affecting corners.

#### Aberration

Spherical - Rays hitting the edge of the lens focus closer to the lens.

Coma - Rays hitting the lens edge have a larger field of view.

Astigmatism - Sagittal and tangential rays focus at different distances from the lens.

Field Curvature - The curvature of the plane in focus.

#### Clipping

Near Clip Depth - Distance from the camera to the nearest clipping plane, measured in meters.

Far Clip Depth - Distance from the camera to the farthest clipping plane, measured in meters.

[](javascript:void(0);)

#### [Depth of Field](javascript:void(0);)

Auto-Focus - Keeps the focus on the closest visible surface at the center of the image, regardless of the aperture, the aperture edge, and focal depth values. This setting is on by default.

Focal Depth - The depth of the plane in focus, measured in meters. If you are having trouble seeing a result when you adjust this setting, double-check to make sure that Auto-Focus is enabled. Auto-Focus overrides the Focal Depth setting.

[Aperture](javascript:void(0);) - The radius of the camera\'s lens opening, measured in centimeters. Low values have a wide depth-of-field, where everything is in focus. High values have a shallow depth-of-field, where objects in the foreground and background will be out of focus.

Aperture Aspect Ratio - This allows users to squash and stretch the depth-of-field disc.

Aperture Shape - Controls the shape of the aperture.

Aperture Edge - Modifies the relative distribution of rays across the aperture, impacting the hardness of the edges of bokeh shapes. Higher values increase the contrast towards the edge. Values between 0 and 1 simulate an apodization filter.

Aperture Blade Count - The number of blades forming the iris diaphragm.

Aperture Rotation - The rotation of the aperture shape in degrees.

Aperture Roundedness - The roundness of the blades forming the iris diaphragm.

Central Obstruction - Simulates the obstruction from the secondary mirror of a catadioptric system. This option is only enabled on circular apertures.

Notch Position - Determines the position of the notch on the blades.

Notch Scale - Scale of the notch.

Custom Aperture - Sets the custom aperture opacity map. The projection type must be set to OSL Delayed UV.

#### Optical Vignetting

Optical Vignette Distance - The distance between the lens and the opening of the lens barrel.

Optical Vignette Scale - The scale of the opening of the lens barrel relative to the aperture.

#### Split-Focus Diopter

Enable Split-Focus Diopter - Enables the split-focus diopter.

Diopter Focal Depth - Depth of the plane in focus measured in meters.

Diopter Rotation - Rotation of the split-focus diopter in degrees.

Diopter Translation - Translation of the split-focus diopter.

Diopter Boundary Width - Width of the boundary between the two fields.

Diopter Boundary Falloff - Controls how quickly the Split-Focus diopter focal depth blends into the main focal depth.

Show Diopter Guide - Displays guide lines, toggling this option on or off will restart the render.

#### Position

Position - The camera\'s position.

Target - The target\'s position that the camera points to.

Up-Vector - The camera\'s up direction in the scene.

Keep Upright - The panoramic camera always orients towards the horizon, and the up-vector stays in its default vertical direction (0, 1, 0).

#### Stereo

Stereo Output - This specifies the output rendered in stereo mode.

- Left - Renders the left eye image.
- Right - Renders the right eye image.
- Side-By-Side - Renders the scene as a pair of two-dimensional images.
- Anaglyphic - Makes the render viewable with red/blue 3D glasses.
- Over-Under - The pair of two-dimensional images is placed one above the other for special viewers.

Stereo Mode - Determines whether the stereo mode is off-axis or parallel.

Eye Distance - The distance between the left and the right eye in stereo mode, measured in meters.

Swap Eyes - This swaps left and right eye position when stereo mode is showing both.

Left Stereo Filter/Right Stereo Filter - The left and right filter colors used to create the anaglyphic stereo effect in the render.
