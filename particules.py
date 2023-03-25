from itertools import cycle
import OpenGL.GL as GL  # standard Python OpenGL wrapper
from PIL import Image  # load texture maps
import glfw
from matplotlib import pyplot as plt
import numpy as np  # all matrix manipulations & OpenGL args
from core import Mesh, Node, Texture
import random
from texture import Texture, Textured, calcNormals
from transform import Trackball, vec, quaternion, quaternion_from_euler
from animation import (KeyFrameControlNode)

class Particule(Textured):
    def __init__(self, viewer, shader, texture, normals, vertices, index, tex_coord, light_dir, position=(0, 0, 0), shinyness=2, scale=1):
        self.viewer = viewer
        self.shader = shader
        self.texture = texture
        self.normals = normals
        self.vertices = np.array(vertices, np.float32)*scale
        self.index = index
        self.tex_coord = tex_coord
        self.light_dir = light_dir
        self.position = np.array(position, np.float32)
        self.shinyness = shinyness
        self.scale = scale
        mesh = Mesh(shader, attributes=dict(position=self.vertices+self.position, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)
        super().__init__(mesh, diffuse_map=texture)
    
    def updateOrientation(self):
        rotationMatrix = self.viewer.trackball.matrix()
        matrix = rotationMatrix[:3, :3]
        vertices_ = np.zeros_like(self.vertices, np.float32)
        vertices_ = np.array([sous_tableau @ matrix for sous_tableau in self.vertices], np.float32)
        #(normals_, vertices_, index_) = calcNormals(vertices_, self.index)
        self.drawable.setAttributes(dict(position=vertices_, tex_coord=np.array(self.tex_coord), normal=self.normals))
    
    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        self.updateOrientation()
        return super().draw(primitives, **uniforms)

class leafParticle(Particule):
    def __init__(self, viewer, shader, light_dir, texture, position=(0,0,0), shinyness=2, scale=1) :
        vertices = [[-0.5,-0.5,0],[0.5,-0.5,0],[-0.5,0.5,0],[0.5,0.5,0]]
        index = [0,1,3,0,3,2]
        normals = [[0,0,1],[0,0,1],[0,0,1],[0,0,1]]
        tex_coord = [[0,1],[1,1],[0,0],[1,0]]
        super().__init__(viewer, shader, texture, normals, vertices, index, tex_coord, light_dir, position, shinyness, scale)

class FallingLeaf(KeyFrameControlNode):
    def __init__(self, viewer, shader, light_dir, height, texture, position=(0,0,0), shinyness=2, scale=1, repeat=False, animationShift=0):
        (x,z,y)=position
        trans_keys = {0: vec(x, z, y), 3: vec(x, z-height*0.9, y), 4: vec(x, z-height*0.98, y), 5: vec(x, z-height, y)}
        rot_keys = {0:quaternion(), 5:quaternion()}
        scale_keys = {0: 1, 5: 1}
        super().__init__(trans_keys, rot_keys, scale_keys, repeat=repeat, animationShift=animationShift)
        self.add(leafParticle(viewer, shader, light_dir, texture, (0,0,0), shinyness, scale))

class FallingLeaves(Node):
    def __init__(self, viewer, shader, light_dir, height, texture, position=(0,0,0), shinyness=2, ray=1):
        super().__init__()
        nbLeaves = random.randint(0, 2)
        for leave in range(nbLeaves):
            (x,z,y) = position
            theta = np.random.uniform(0, 2*np.pi)  # angle aléatoire
            s = np.random.uniform(0, ray/2)  # distance aléatoire dans le rayon
            x = x + s*np.cos(theta)  # nouvelle coordonnée x
            y = y + s*np.sin(theta)  # nouvelle coordonnée y

            animationShift = random.randint(0,9)
            self.add(FallingLeaf(viewer, shader, light_dir, height, texture, (x,z,y), repeat=True, animationShift=animationShift))
        