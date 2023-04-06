#!/usr/bin/env python3
"""
Python OpenGL practical application.
"""

import sys  # for system arguments

# External, non built-in modules
import OpenGL.GL as GL
from animation import KeyFrameControlNode, Skinned  # standard Python OpenGL wrapper
import numpy as np  # all matrix manipulations & OpenGL args
import glfw  # lean window system wrapper for OpenGL

from core import Shader, Mesh, Viewer, Node, load
from skybox import SkyBox
from transform import sincos, translate, identity, rotate, scale, vec, quaternion, quaternion_from_euler
from textures import Terrain, TexturedDuck, TexturedSphere, TexturedCylinder, TexturedPlane, TexturedTree, ForestTerrain, \
    LakeForestTerrain, TexturedVolcano
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


# -------------- Deformable Cylinder Mesh  ------------------------------------
class SkinnedCylinder(KeyFrameControlNode):
    """ Deformable cylinder """
    def __init__(self, shader, sections=11, quarters=20):

        # this "arm" node and its transform serves as control node for bone 0
        # we give it the default identity keyframe transform, doesn't move
        super().__init__({0: (0, 0, 0), 1: (0, 0, 0)}, {0: quaternion(), 1: quaternion()}, {0: 1, 1: 1})

        # we add a son "forearm" node with animated rotation for the second
        # part of the cylinder
        self.add(KeyFrameControlNode(
            {0: (0, 0, 0), 1: (0, 0, 0)},
            {0: quaternion(), 2: quaternion_from_euler(90), 4: quaternion()},
            {0: 1, 1: 1}))

        # there are two bones in this animation corresponding to above noes
        bone_nodes = [self, self.children[0]]

        # these bones have no particular offset transform
        bone_offsets = [identity(), identity()]

        # vertices, per vertex bone_ids and weights
        vertices, faces, bone_id, bone_weights = [], [], [], []
        for x_c in range(sections+1):
            for angle in range(quarters):
                # compute vertex coordinates sampled on a cylinder
                z_c, y_c = sincos(360 * angle / quarters)
                vertices.append((x_c - sections/2, y_c, z_c))

                # the index of the 4 prominent bones influencing this vertex.
                # since in this example there are only 2 bones, every vertex
                # is influenced by the two only bones 0 and 1
                bone_id.append((0, 1, 0, 0))

                # per-vertex weights for the 4 most influential bones given in
                # a vec4 vertex attribute. Not using indices 2 & 3 => 0 weight
                # vertex weight is currently a hard transition in the middle
                # of the cylinder
                # TODO: modify weights here for TP7 exercise 2
                weight = 1 if x_c <= sections/2 else 0
                bone_weights.append((weight, 1 - weight, 0, 0))

        # face indices
        faces = []
        for x_c in range(sections):
            for angle in range(quarters):

                # indices of the 4 vertices of the current quad, % helps
                # wrapping to finish the circle sections
                ir0c0 = x_c * quarters + angle
                ir1c0 = (x_c + 1) * quarters + angle
                ir0c1 = x_c * quarters + (angle + 1) % quarters
                ir1c1 = (x_c + 1) * quarters + (angle + 1) % quarters

                # add the 2 corresponding triangles per quad on the cylinder
                faces.extend([(ir0c0, ir0c1, ir1c1), (ir0c0, ir1c1, ir1c0)])

        # the skinned mesh itself. it doesn't matter where in the hierarchy
        # this is added as long as it has the proper bone_node table
        attributes = dict(position=vertices, normal=bone_weights,
                          bone_ids=bone_id, bone_weights=bone_weights)
        mesh = Mesh(shader, attributes=attributes, index=faces)
        self.add(Skinned(mesh, bone_nodes, bone_offsets))

# -------------- main program and scene setup --------------------------------
def main():
    """ create a window, add scene objects, then run rendering loop """
    viewer = Viewer()

    # default color shader
    # shader = Shader("Shaders/color.vert", "Shaders/color.frag")
    shaderTexture = Shader("Shaders/texture.vert", "Shaders/texture.frag")
    shaderLight = Shader("Shaders/phong.vert", "Shaders/phong.frag")
    skyboxShader = Shader("Shaders/skybox.vert", "Shaders/skybox.frag")
    skinningShader = Shader("Shaders/skinning.vert", "Shaders/color.frag")
    # shaderNormals = Shader("Shaders/normalviz.vert", "Shaders/normalviz.frag", "Shaders/normalviz.geom")

    # Textures
    trunk = Texture("Textures/tronc.jpg")
    leaves = Texture("Textures/leaves.jpg")
    leaf = Texture("Textures/leaf.png")
    grass = Texture("Textures/grass.png")
    water = Texture("Textures/water.jpg")
    lava_tex_file = Texture("Textures/lava.jpg")
    volcano_tex_file = "Objects/volcano/volcano_texture.png"
    duck_tex_file = "Objects/duck/10602_Rubber_Duck_v1_diffuse.jpg"

    light_dir = (1, -1, 1)

    # Volcano
    viewer.add(TexturedVolcano(shaderTexture, light_dir, volcano_tex_file, lava_tex_file))
    # Duck
    viewer.add(TexturedDuck(shaderTexture, light_dir, duck_tex_file))

    print("====Controls====\nLeft-click: rotate camera\nRight-click: move camera\nMouse wheel: Zoom/Dezoom\nZ: Show vertices\nSpace: Reset time to 0\n")
    print("→ ← ↑ ↓: Translate view\n")

    # Skybox
    viewer.add(SkyBox(skyboxShader, "Textures/skybox/"))
    # Terrain with node (Trees, Lakes, ...)
    viewer.add(LakeForestTerrain(shaderLight, shaderTexture, grass, water, leaves, trunk, leaf, viewer, light_dir))

    # start rendering loop
    viewer.run()


if __name__ == '__main__':
    main()  # main function keeps variables locally scoped
