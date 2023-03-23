#!/usr/bin/env python3
"""
Python OpenGL practical application.
"""

import sys  # for system arguments

# External, non built-in modules
import OpenGL.GL as GL  # standard Python OpenGL wrapper
import numpy as np  # all matrix manipulations & OpenGL args
import glfw  # lean window system wrapper for OpenGL

from core import Shader, Mesh, Viewer, Node, load
from skybox import SkyBox
from transform import translate, identity, rotate, scale
from texture import Terrain, TexturedSphere, TexturedCylinder, TexturedPlane, TexturedTree, ForestTerrain, Texture, LakeForestTerrain


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


# -------------- main program and scene setup --------------------------------
def main():
    """ create a window, add scene objects, then run rendering loop """
    viewer = Viewer()

    # default color shader
    shader = Shader("Shaders/color.vert", "Shaders/color.frag")
    shaderTexture = Shader("Shaders/texture.vert", "Shaders/texture.frag")
    shaderLight = Shader("Shaders/phong.vert", "Shaders/phong.frag")
    skyboxShader = Shader("Shaders/skybox.vert", "Shaders/skybox.frag")
    shaderNormals = Shader("Shaders/normalviz.vert", "Shaders/normalviz.frag", "Shaders/normalviz.geom")
    
    #Textures
    trunk = Texture("Textures/tronc.jpg")
    leaves = Texture("Textures/leaves.jpg")
    grass = Texture("Textures/grass.png")
    water = Texture("Textures/water.jpg")

    light_dir = (1, -1, 1)

    # place instances of our basic objects
    viewer.add(*[mesh for file in sys.argv[1:] for mesh in load(file, shaderLight, light_dir=light_dir)])
    if len(sys.argv) < 2:
        viewer.add(Axis(shaderTexture))
        viewer.add(SkyBox(skyboxShader, "Textures/skybox/"))
        #viewer.add(ForestTerrain(position=(0,-1,0), shader=shaderLight, terrainTexture=grass,trunkTextures=trunk,leavesTextures=leaves, light_dir=light_dir))
        #viewer.add(Terrain(shader=shaderLight, texture=grass, light_dir=light_dir))
        #viewer.add(TexturedTree(shader=shaderLight, position=(1,0,0), leavesTextures=leaves, trunkTextures=trunk, light_dir=light_dir))
        viewer.add(LakeForestTerrain(shader=shaderLight, position = (5,2,-3), size=(50,200), light_dir=light_dir, terrainTexture=grass, waterTextures=water, leavesTextures=leaves, trunkTextures=trunk))
        print('Usage:\n\t%s [3dfile]*\n\n3dfile\t\t the filename of a model in'
              ' format supported by assimp.' % (sys.argv[0],))

    # start rendering loop
    viewer.run()


if __name__ == '__main__':
    main()  # main function keeps variables locally scoped
