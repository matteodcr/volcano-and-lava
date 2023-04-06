#!/usr/bin/env python3
"""
Python OpenGL practical application.
"""

# External, non built-in modules
import OpenGL.GL as GL
import numpy as np  # all matrix manipulations & OpenGL args
import glfw  # lean window system wrapper for OpenGL

from core import Shader, Mesh, Viewer, Node, load
from skybox import SkyBox
from textures import TexturedDuck, LakeForestTerrain, TexturedVolcano
from texture import Texture

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

    # Shaders
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
    lava = Texture("Textures/lava.jpg")
    volcano_tex_file = "Objects/volcano/volcano_texture.png"
    duck_tex_file = "Objects/duck/10602_Rubber_Duck_v1_diffuse.jpg"

    light_dir = (1, -1, 1)

    # Volcano
    viewer.add(TexturedVolcano(shaderTexture, light_dir, volcano_tex_file, lava))
    # Duck
    viewer.add(TexturedDuck(shaderTexture, light_dir, duck_tex_file))
    # Skybox
    viewer.add(SkyBox(skyboxShader, "Textures/skybox/"))
    # Terrain with node (Trees, Lakes, ...)
    viewer.add(LakeForestTerrain(shaderLight, shaderTexture, grass, water, leaves, trunk, leaf, viewer, light_dir))

    print("====Controls====\nLeft-click: rotate camera\nRight-click: move camera\nMouse wheel: Zoom/Dezoom\nZ: Show vertices\nSpace: Reset time to 0\n")
    print("→ ← ↑ ↓: Translate view\n")

    # start rendering loop
    viewer.run()


if __name__ == '__main__':
    main()  # main function keeps variables locally scoped
