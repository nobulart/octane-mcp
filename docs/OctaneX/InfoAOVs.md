The Info AOVs are typically not shaded render passes (with a couple of exceptions) and are used to help isolate elements from the various Render AOVs for compositing, or somehow driving other shading AOVs and comps. Info [AOVs](https://docs.otoy.com/cinema4d/AOVIntroduction.md) are Render AOVs that provide a view of the effects of normals, UVs and other geometric data within the scene. When any of these AOVs are enabled, they can be previewed in the Render Viewport window.

#### Available Info AOVs

- Ambient Occlusion AOV - Assigns a color to the camera ray\'s hit point proportional to the amount of occlusion by other geometry. The AO Distance option controls the distance of the ambient occlusion shadowing spread. This setting should be adjusted in order to achieve realistic results depending on the scale of the objects in the scene. For example, a small value is more appropriate for small objects such as toys and larger values for an object such as a house.Enable AO Alpha Shadow with this option, otherwise the result will contain additional information.
- Baking Group ID AOV - Colors each distinct baking group in the scene with a color based on its ID.
- Diffuse Filter (info) AOV - Outputs the unshaded base diffuse color (albedo).
- Geometric Normal AOV - Assigns a color for the geometry normal at the position hit by the camera ray.
- Index of Refraction AOV - Outputs a grayscale of the IOR of scene objects. IORs closer to 1.0 will be near black. Larger IOR values will be brighter.
- Light Pass ID AOV - Colors the emitters based on their Light Pass ID.
- Material ID AOV - Assigns RGB values according to the materials mapped to the geometry.
- Motion Vector AOV - Renders the motion vectors as 2D vectors in screen space. The X coordinate (stored in the red channel) is motion to the right, in pixels. The Y coordinate (stored in the green channel) is the motion up, in pixels. When this pass is enabled, the rendering of motion blur is disabled.
- Object ID AOV - Colors each distinct object in the scene with a color based on its ID.
- Object Layer Color AOV - This is the color specified in the Object Layer node.
- Opacity AOV - Outputs a unshaded grayscale of the Opacity channel of scene objects. Opacity values closer to 1.0 will be near white. Lower opacity values will be dimmer.
- Position AOV - Assigns RGB values according to the intersection point of the camera ray.
- Reflection Filter (info) AOV - Outputs a unshaded grayscale value of the Reflection channel of scene objects. Reflection values closer to 1.0 will be near white. Lower Reflection values will be darker
- Refraction Filter (info) AOV - The transmission color of the specular/universal material that caused the ray of the sample to refract.
- Render Layer ID AOV - Colors objects on the same layer with the same color based on the Render Layer ID.
- Render Layer Mask AOV - Grayscale value of the render layer selected in the render layer mask AOV node.
- Roughness AOV - Grayscale representation of the roughness of each object in the scene.
- Shading Normal AOV - Assigns a color for the shading normal at the position hit by the camera ray.
- Smooth Normal AOV - Assigns a color for the smooth normal at the position hit by the camera ray.
- Tangent Normal AOV - Assigns a color to the Tangent (local) normal at the position hit by the camera ray.
- Texture Tangent AOV - The tangent vector of U texture coordinates (Dp, Du).
- Transmission Filter (info) AOV - The color of the transmission channel of diffuse materials. 
- UV Coordinates AOV - Assigns RGB values according to the geometry\'s texture coordinates.
- Wireframe AOV - Triangulated wireframe display of the geometry.
- Z-Depth AOV - Assigns a gray value proportional to the camera ray hit distance. Image planes closest to camera position will appear black, and the furthest will appear white. Depth maps should always be saved in a 32-bit image format for maximum precision. When this image pass is rendered, it will appear to be completely white, but the depth information is still there.
