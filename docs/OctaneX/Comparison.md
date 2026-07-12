The Comparison node offers you the ability to use a logical comparison operator as a way to combine textures. The node takes ficve inputs: the first two inputs are the textures for comparison. The second input is for the comparison, and the last two inputs are the result of the comparison. In the following example a Checks texture node (input A) is used to compare the black and white of the checks texture against white (input B) where the black areas of the checks texture are less than input B which is white. If the statement is true (black areas), those areas will be replaced with blue. If the statement is false (white areas), those areas will be red (figure 1).

+-----------------------------------+-------------------------------------------+
| ![](images/NewItem_260.png)       | Comparison                                |
|                                   |                                           |
|                                   | ![](images/Comparison_Fig01_SE_v2022.jpg) |
+-----------------------------------+-------------------------------------------+

Figure 1: A Checks texture node is used to colorize the checks pattern with red and blue using the Comparison node
