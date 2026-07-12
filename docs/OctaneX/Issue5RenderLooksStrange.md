----------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Problem:    Concentric circles over the image or unusual effects including Bump map not working.
  Solution:   Check the imported scene\'s scale and change the Ray Epsilon value. This is due to the scale being incorrect by a factor of 100 or 1000. OctaneRender® expects one unit in the scene to equal one meter. Adjust export settings in the modeling application, or adjust the import settings in OctaneRender®.
               
  Problem:    Facetting occurs, revealing the underlying polygonal mesh, geometry, or normals issues.
  Solution:   Ensure that the geometry and normals are correct in the modeling program. Re-export the scene if necessary. Make sure the Normal Smoothing boolean value (smooth) is enabled for each material in the Node Inspector.
               
  Problem:    Bump map does not show up.
  Solution:   When a Bump map and Normal map are loaded, the Normal map takes priority and the Bump map will not be used.
               
  Problem:    Images do not look right on the model.
  Solution:   This may be due to the way the model was UV unwrapped. This may need to be redone more precisely in the 3D modeling application and exported again.
  ----------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
