#!/usr/bin/env python3
"""
Python OpenGL practical application.
"""

import sys  # for system arguments

# External, non built-in modules
import OpenGL.GL as GL
from animation import KeyFrameControlNode  # standard Python OpenGL wrapper
import numpy as np  # all matrix manipulations & OpenGL args
import glfw  # lean window system wrapper for OpenGL

from core import Shader, Mesh, Viewer, Node, load
from skybox import SkyBox
from transform import translate, identity, rotate, scale, vec, quaternion, quaternion_from_euler
from textures import Terrain, TexturedSphere, TexturedCylinder, TexturedPlane, TexturedTree, ForestTerrain, \
    LakeForestTerrain
from texture import Texture
from particules import Particule, leafParticle, FallingLeaf, FallingLeaves


class Axis(Mesh):
    """ Axis object useful for debugging coordinate frames """

    def __init__(self, shader):
        pos = ((0, 0, 0), (1, 0, 0), (0, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1))
        col = ((1, 0, 0), (1, 0, 0), (0, 1, 0), (0, 1, 0), (0, 0, 1), (0, 0, 1))
        super().__init__(shader, attributes=dict(position=pos, color=col))

    def draw(self, primitives=GL.GL_LINES, **uniforms):
        super().draw(primitives=primitives, **uniforms)


class Triangle(Mesh):
    """Hello triangle object"""

    def __init__(self, shader):
        position = np.array(((0, .5, 0), (-.5, -.5, 0), (.5, -.5, 0)), 'f')
        color = np.array(((1, 0, 0), (0, 1, 0), (0, 0, 1)), 'f')
        self.color = (1, 1, 0)
        attributes = dict(position=position, color=color)
        super().__init__(shader, attributes=attributes)

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        super().draw(primitives=primitives, global_color=self.color, **uniforms)

    def key_handler(self, key):
        if key == glfw.KEY_C:
            self.color = (0, 0, 0)

class Duck(Node):
    def __init__(self, material):
        super().__init__()
        self.add(*load('Objects/duck/10602_Rubber_Duck_v1_L3.obj', material))
        GL.glRotate(0, 90, 0)
        GL.glScalef(0.1, 0.1, 0.1)


# -------------- main program and scene setup --------------------------------
def main():
    """ create a window, add scene objects, then run rendering loop """
    viewer = Viewer()

    # default color shader
    shader = Shader("Shaders/color.vert", "Shaders/color.frag")
    shaderTexture = Shader("Shaders/texture.vert", "Shaders/texture.frag")
    shaderLight = Shader("Shaders/phong.vert", "Shaders/phong.frag")
    skyboxShader = Shader("Shaders/skybox.vert", "Shaders/skybox.frag")
    # shaderNormals = Shader("Shaders/normalviz.vert", "Shaders/normalviz.frag", "Shaders/normalviz.geom")

    # Textures
    trunk = Texture("Textures/tronc.jpg")
    leaves = Texture("Textures/leaves.jpg")
    leaf = Texture("Textures/leaf.png")
    grass = Texture("Textures/grass.png")
    water = Texture("Textures/water.jpg")

    light_dir = (1, -1, 1)


    # Loading and animating the duck
    duck_translate_keys = {0: vec(2, 11, 0), 1: vec(1.5, 11, 1.5), 2: vec(0, 11, 2), 3: vec(-1.5, 11, 1.5), 4: vec(-2, 11, 0),
                           5: vec(-1.5, 11, -1.5), 6: vec(0, 11, -2), 7: vec(1.5, 11, -1.5), 8: vec(2, 11, 0)}
    duck_rotate_keys = {0: quaternion_from_euler(0, 0, 270), 1: quaternion_from_euler(0, -45, 270),
                        2: quaternion_from_euler(0, -90, 270), 3: quaternion_from_euler(0, -135, 270),
                        4: quaternion_from_euler(0, -180, 270), 5: quaternion_from_euler(0, -225, 270),
                        6: quaternion_from_euler(0, -270, 270), 7: quaternion_from_euler(0, -315, 270),
                        8: quaternion_from_euler(0, 0, 270)}
    duck_scale_keys = {0: 0.3, 1: 0.3, 2: 0.3, 3: 0.3, 4: 0.3, 5: 0.3, 6: 0.3, 7: 0.3, 8: 0.3}

    duck_keynode = KeyFrameControlNode(duck_translate_keys, duck_rotate_keys, duck_scale_keys, repeat=True)
    duck_keynode.add(*load('Objects/duck/10602_Rubber_Duck_v1_L3.obj', shaderTexture))
    viewer.add(duck_keynode)

    # Loading and placing the volcano
    volcano_translate_keys = {0: vec(0, 0, 0), 1: vec(0, 0, 0)}
    volcano_rotate_keys = {0: quaternion_from_euler(0, 0, 0), 1: quaternion_from_euler(0, 0, 0)}
    volcano_scale_keys = {0: 6, 1: 6}

    volcano_keynode = KeyFrameControlNode(volcano_translate_keys, volcano_rotate_keys, volcano_scale_keys)
    volcano_keynode.add(*load('Objects/volcano/volcano.obj', shaderTexture))
    viewer.add(volcano_keynode)

    print("====Controls====\nLeft-click: rotate camera\nRight-click: move camera\nMouse wheel: Zoom/Dezoom\nZ: Show vertices\nSpace: Reset time to 0")

    # Skybox
    viewer.add(SkyBox(skyboxShader, "Textures/skybox/"))
    # Terrain with node (Trees, Lakes, ...)
    viewer.add(LakeForestTerrain(shaderLight, shaderTexture, grass, water, leaves, trunk, leaf, viewer, light_dir))

    # start rendering loop
    viewer.run()


if __name__ == '__main__':
    main()  # main function keeps variables locally scoped
