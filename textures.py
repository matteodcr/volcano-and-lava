from animation import KeyFrameControlNode
from texture import Texture, Textured, calcNormals

from itertools import cycle
import OpenGL.GL as GL  # standard Python OpenGL wrapper
from PIL import Image  # load texture maps
import glfw
from matplotlib import pyplot as plt
import numpy as np  # all matrix manipulations & OpenGL args
from core import Mesh, Node, Texture, load
import random
from particules import FallingLeaves
from transform import quaternion, quaternion_from_euler, vec


class TexturedSphere(Textured):
    """ Procedural textured sphere """

    # avec l'aide de : http://www.songho.ca/opengl/gl_sphere.html
    def __init__(self, shader, texture, position=(0, 0, 0), r=1, stacks=10, sectors=10, light_dir=None, shinyness=2):
        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()

        lengthInv = 1.0 / r
        sectorStep = 2 * np.pi / sectors
        stackStep = np.pi / stacks

        for i in range(stacks + 1):
            stackAngle = np.pi / 2 - i * stackStep
            xy = r * np.cos(stackAngle)
            z = r * np.sin(stackAngle)

            for j in range(sectors + 1):
                sectorAngle = j * sectorStep
                # vertex position (x, y, z)
                x = xy * np.cos(sectorAngle)
                y = xy * np.sin(sectorAngle)
                vertices = vertices + ((x, z, y),)
                tex_coord += ((i / stacks, j / sectors),)
        vertices = np.array(vertices, np.float32) + np.array(position, np.float32)

        index = ()
        for i in range(stacks):
            k1 = i * (sectors + 1)
            k2 = k1 + sectors + 1
            for j in range(sectors):

                # 2 triangles per sector excluding first and last stacks
                if (i != 0):
                    index = index + (k1, k1 + 1, k2)

                if (i != (stacks - 1)):
                    index = index + (k1 + 1, k2 + 1, k2)

                k1 = k1 + 1
                k2 = k2 + 1

        (normals, vertices, index) = calcNormals(vertices, index)
        self.vertices = vertices
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)


class Terrain(Textured):
    """ Procedural textured terrain """

    def __init__(self, shader, texture, size=(100, 100), position=(0, -1, 0), light_dir=None, shinyness=2):
        (x, y) = size
        self.heightMap = np.random.random(size)
        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()
        for i in range(x):
            for j in range(y):
                vertices = vertices + ((i - x / 2, self.heightMap[i][j] / 2, j - y / 2),)
                tex_coord += ((i % 2, j % 2),)
        vertices = np.array(vertices, np.float32) + np.array(position, np.float32)

        index = ()
        for k in range(y, x * y - 1):
            if ((k + 1) % y != 0):
                index = index + (k, k + 1 - y, k + 1, k, k - y, k + 1 - y)

        (normals, vertices, index) = calcNormals(vertices, index)
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)


class TexturedPlane(Textured):
    """ Simple first textured object """

    def __init__(self, shader, texture, position=(0, 0, 0), light_dir=None, shinyness=2, length=2, width=2):
        # setup plane mesh to be textured
        vertices = ((-length / 2, 0, -width / 2), (length / 2, 0, -width / 2), (length / 2, 0, width / 2),
                    (-length / 2, 0, width / 2))
        tex_coord = ((0, 0), (1, 0), (1, 1), (0, 1))
        vertices = np.array(vertices, np.float32) + np.array(position, np.float32)
        index = np.array((0, 2, 1, 0, 3, 2), np.uint32)
        (normals, vertices, index) = calcNormals(vertices, index)
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)


class TexturedCylinder(Textured):
    """ Simple first textured object """

    def __init__(self, shader, texture, height=1, divisions=50, r=0.5, position=(0, 0, 0), light_dir=None, shinyness=2):
        self.height = height
        self.divisions = divisions
        self.ray = r

        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()
        vertices = vertices + ((0, self.height / 2, 0),)
        tex_coord += ((0, 0),)
        tex_i = 0
        for x in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices = vertices + ((self.ray * np.cos(x), self.height / 2, self.ray * np.sin(x)),)
            tex_coord += ((tex_i / divisions, 0),)
            tex_i += 1
        vertices = vertices + ((0, -self.height / 2, 0),)
        tex_coord += ((1, 1),)
        tex_i = 0
        for x in np.arange(0, 2 * np.pi, 2 * np.pi / self.divisions):
            vertices = vertices + ((self.ray * np.cos(x), -self.height / 2, self.ray * np.sin(x)),)
            tex_coord += ((tex_i / divisions, 1),)
            tex_i += 1
        vertices = np.array(vertices, np.float32) + np.array(position, np.float32)

        index = ()
        # top face
        for x in range(1, self.divisions, 1):
            index = index + (0, x + 1, x)
        index = index + (0, 1, self.divisions)
        # bottom face
        for x in range(1, self.divisions, 1):
            index = index + (self.divisions + 1, self.divisions + x + 1, self.divisions + x + 2)
        index = index + (self.divisions + 1, self.divisions * 2 + 1, self.divisions + 2)
        # side
        for x in range(1, self.divisions, 1):
            index = index + (x, x + 1, self.divisions + x + 1, x + 1, self.divisions + x + 2, self.divisions + x + 1)
        index = index + (self.divisions, 1, self.divisions * 2 + 1, 1, self.divisions + 2, self.divisions * 2 + 1)

        (normals, vertices, index) = calcNormals(vertices, index)
        mesh = Mesh(shader, attributes=dict(position=vertices, tex_coord=np.array(tex_coord), normal=normals),
                    index=index, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)


class TexturedTree(Node):
    def __init__(self, shader, shaderLeaf, position, leavesTextures, trunkTextures, viewer, leafTexture,
                 light_dir=None):
        super().__init__()
        random.seed()

        (x, z, y) = position
        trunk_height = 5 + random.random()
        main_leaves_size = 2 + random.random()

        self.add(
            TexturedCylinder(shader, position=(x, z + trunk_height / 2, y), height=trunk_height, texture=trunkTextures,
                             light_dir=light_dir))
        mainLeaves = TexturedSphere(shader, position=(x, z + trunk_height, y), r=main_leaves_size,
                                    texture=leavesTextures,
                                    light_dir=light_dir)
        self.add(FallingLeaves(viewer, shaderLeaf, light_dir, trunk_height - 0.5, leafTexture, (x, z + trunk_height, y),
                               ray=main_leaves_size))
        self.add(mainLeaves)
        mainLeavesVertices = mainLeaves.vertices
        for i in range(random.randint(0, 3)):
            [x_, z_, y_] = mainLeavesVertices[random.randint(0, len(mainLeavesVertices) - 1)]
            r = random.random()
            self.add(
                TexturedSphere(shader, position=(x_, z_, y_), r=r, texture=leavesTextures,
                               light_dir=light_dir))
            self.add(FallingLeaves(viewer, shaderLeaf, light_dir, z_ - z - 0.5, leafTexture, (x_, z_, y_), ray=r))


class ForestTerrain(Node):
    def __init__(self, shader, shaderLeaf, terrainTexture, trunkTextures, leavesTextures, viewer, size=(100, 100),
                 position=(0, 0, 0),
                 light_dir=None):
        super().__init__()
        self.add(Terrain(shader=shader, size=size, texture=terrainTexture, position=position, light_dir=light_dir))
        (length, width) = size
        (posx, posz, posy) = position
        trees = random.randint(0, (length / 10) * (width / 10))
        for t in range(trees):
            self.add(TexturedTree(shader=shader, shaderLeaf=shaderLeaf, position=(
                posx - length / 2 + length * random.random(), posz, posy - width / 2 + width * random.random()),
                                  trunkTextures=trunkTextures, leavesTextures=leavesTextures, light_dir=light_dir,
                                  viewer=viewer))


class TexturedCube(Textured):
    def __init__(self, drawable, **textures):
        super().__init__(drawable, **textures)

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        GL.glDepthFunc(GL.GL_LEQUAL)
        for index, (name, texture) in enumerate(self.textures.items()):
            GL.glActiveTexture(GL.GL_TEXTURE0 + index)
            GL.glBindTexture(texture.type, texture.glid)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 36)
            GL.glBindVertexArray(0)
            uniforms[name] = index
        self.drawable.draw(primitives=primitives, **uniforms)
        GL.glDepthFunc(GL.GL_LESS)

def nerbyPoints(point):
    (x, y) = point
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


class TexturedPlaneWater(KeyFrameControlNode):
    def __init__(self, shader, light_dir, texture, position=(0, 0, 0), shinyness=2, scale=1,
                 repeat=True, animationShift=0, minx=0, maxx=1, miny=0, maxy=1):
        (x, z, y) = position
        trans_keys = {0: vec(x, y, z), 3: vec(x-0.1, y, z-0.1), 4: vec(x-0.2, y, z-0.2),
                      5: vec(x, y, z)}
        rot_keys = {0: quaternion(), 5: quaternion()}
        scale_keys = {0: 1, 5: 1}
        super().__init__(trans_keys, rot_keys, scale_keys, repeat=repeat, animationShift=animationShift)
        self.add((TexturedPlane(shader=shader, light_dir=light_dir, texture=texture, length=(maxx - minx) +0.4,
                                width=(maxy - miny)+0.4,
                                position=(-1 + x + minx + (maxx - minx) / 2, z, -1 + y + miny + (maxy - miny) / 2))))
        
class TexturedVolcano(KeyFrameControlNode):
    def __init__(self, shader, light_dir, texture, position=(0, 0, 0), repeat=False, animationShift=0):
        (x, z, y) = position
        trans_keys = {0: vec(0, 0, 0), 1: vec(0, 0, 0)}
        rot_keys = {0: quaternion_from_euler(0, 0, 0), 1: quaternion_from_euler(0, 0, 0)}
        scale_keys = {0: 6, 1: 6}
        super().__init__(trans_keys, rot_keys, scale_keys, repeat=repeat, animationShift=animationShift)
        self.add(*load('Objects/volcano/volcano.obj', shader, texture, light_dir=light_dir))

class TexturedDuck(KeyFrameControlNode):
    def __init__(self, shader, light_dir, texture, position=(0, 0, 0), repeat=True, animationShift=0):
        (x, z, y) = position
        trans_keys = {0: vec(2, 11, 0), 1: vec(1.5, 11, 1.5), 2: vec(0, 11, 2), 3: vec(-1.5, 11, 1.5), 4: vec(-2, 11, 0),
                           5: vec(-1.5, 11, -1.5), 6: vec(0, 11, -2), 7: vec(1.5, 11, -1.5), 8: vec(2, 11, 0)}
        rot_keys = {0: quaternion_from_euler(0, 0, 270), 1: quaternion_from_euler(0, -45, 270),
                        2: quaternion_from_euler(0, -90, 270), 3: quaternion_from_euler(0, -135, 270),
                        4: quaternion_from_euler(0, -180, 270), 5: quaternion_from_euler(0, -225, 270),
                        6: quaternion_from_euler(0, -270, 270), 7: quaternion_from_euler(0, -315, 270),
                        8: quaternion_from_euler(0, 0, 270)}
        scale_keys = {0: 0.3, 1: 0.3, 2: 0.3, 3: 0.3, 4: 0.3, 5: 0.3, 6: 0.3, 7: 0.3, 8: 0.3}
        super().__init__(trans_keys, rot_keys, scale_keys, repeat=repeat, animationShift=animationShift)
        self.add(*load('Objects/duck/10602_Rubber_Duck_v1_L3.obj', shader, texture, light_dir=light_dir))


class Lake(KeyFrameControlNode):
    def __init__(self, shader, terrainSize, waterTexture, light_dir, position=None, depth=4):
        (x, y) = terrainSize
        if position == None:
            (centerx, centery) = (random.randint(0, x), random.randint(0, y))
        else:
            (centerx, centery) = position
        self.depth = depth
        self.waterTexture = waterTexture
        self.shader = shader
        self.light_dir = light_dir
        # ------------ creating lake -----------------
        lakePoints = ()
        toProcess = [(centerx, centery)]
        expandchance = 50  # % of chance for each vertex to expand to one direction
        while len(toProcess) != 0:
            (x_, y_) = toProcess.pop(0)
            for element in nerbyPoints((x_, y_)):
                (a, b) = element
                if lakePoints.count(element) == 0 and toProcess.count(element) == 0:
                    if (a >= 1 and a < x - 1 and b >= 1 and b < y - 1):  # don't take vertices on the edges
                        if (random.randint(0, 100) < expandchance):
                            toProcess.append(element)
                            for e in nerbyPoints(element):  # traitement des pics résiduels
                                [e1, e2, e3, e4] = nerbyPoints(e)
                                if (lakePoints.count(e1) + lakePoints.count(e2) + lakePoints.count(
                                        e3) + lakePoints.count(e4)):
                                    lakePoints += (e,)
            lakePoints += ((x_, y_),)
        self.lakeDepths = lakePoints
        waterVertex = ()
        for element in lakePoints:
            (elx, ely) = element
            waterVertex += ((elx, ely),)
            for e in nerbyPoints(element):
                if lakePoints.count(e) == 0 and waterVertex.count(e) == 0:
                    (ex, ey) = e
                    waterVertex += ((ex, ey),)
        waterVertex = np.array(waterVertex, np.float32)
        self.lake = waterVertex
        minx = waterVertex[0][0]
        miny = waterVertex[0][1]
        maxx = waterVertex[0][0]
        maxy = waterVertex[0][1]
        for element in waterVertex:
            if (element[0] > maxx):
                maxx = element[0]
            if (element[0] < minx):
                minx = element[0]
            if (element[1] > maxy):
                maxy = element[1]
            if (element[1] < miny):
                miny = element[1]
        self.extremums = (minx - x / 2, maxx - x / 2, miny - y / 2, maxy - y / 2)

    def addTo(self, terrain):
        """Adds this lake to the given terrain and returns the water layer Texture"""
        for (x_, y_) in self.lakeDepths:
            terrain.heightMap[x_ - 1][y_ - 1] -= self.depth
        (minx, maxx, miny, maxy) = self.extremums
        (x, z, y) = terrain.position
        # Nouvelle classe
        return TexturedPlaneWater(shader=self.shader, light_dir=self.light_dir, texture=self.waterTexture, minx=minx,
                                  maxx=maxx, miny=miny, maxy=maxy)


class LakeTerrain(Textured):
    def __init__(self, shader, textureTerrain, textureWater, size=(100, 100), position=(0, -1, 0), light_dir=None,
                 shinyness=2, depth=4, heightmap=None, lakes=2):
        if (heightmap == None):
            self.heightMap = np.random.random(size)
        else:
            self.heightMap = heightmap
        self.position = position
        self.size = size
        self.textureWater = textureWater
        self.light_dir = light_dir
        self.depth = depth
        self.shader = shader
        self.shinyness = shinyness
        self.lakes = []
        self.waters = []
        for i in range(lakes):
            lake = Lake(self.shader, self.size, self.textureWater, self.light_dir, depth=self.depth)
            self.lakes.append(lake)
            self.waters.append(lake.addTo(self))

        # ------------------ creating terrain ------------------
        (x, y) = self.size
        vertices = np.zeros((x * y, 3), np.float32)
        tex_coord = np.zeros((x * y, 2), np.float32)
        for i in range(x):
            for j in range(y):
                vertices[y * i + j] = [i - x / 2, self.heightMap[i][j] * 0.8, j - y / 2]
                tex_coord[y * i + j] = [i % 2, j % 2]
        vertices = vertices + np.array(self.position, np.float32)
        index = np.zeros((6 * (x * y - 1 - y)), np.float32)
        i = 0
        for k in range(y, x * y - 1):
            if ((k + 1) % y != 0):
                index[i] = k
                index[i + 1] = k + 1 - y
                index[i + 2] = k + 1
                index[i + 3] = k
                index[i + 4] = k - y
                index[i + 5] = k + 1 - y
                i += 6
        (normals, vertices, index) = calcNormals(vertices, index)
        self.vertices = vertices
        mesh = Mesh(self.shader, attributes=dict(position=vertices, tex_coord=tex_coord, normal=normals),
                    index=index, s=self.shinyness, light_dir=self.light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=textureTerrain)

    def getRandomPointOnGrass(self):
        [x, z, y] = self.vertices[random.randint(0, len(self.vertices) - 1)]
        for i in range(len(self.lakes)):
            while self.contains(self.lakes[i].lake, [x, z, y]):
                [x, z, y] = self.vertices[random.randint(0, len(self.vertices) - 1)]
                i = 0
        return (x, z, y)

    def contains(self, coordLake, element):
        [a, b, c] = element
        for [x, y] in coordLake:
            if a == x and c == y:
                return True
        return False


class LakeForestTerrain(Node):
    def __init__(self, shader, shaderLeaf, terrainTexture, waterTextures, leavesTextures, trunkTextures, leafTexture,
                 viewer, light_dir, size=(100, 100), position=(0, 0, 0)):
        super().__init__()
        terrain = LakeTerrain(shader=shader, size=size, textureTerrain=terrainTexture, textureWater=waterTextures,
                              position=position, light_dir=light_dir)
        self.add(terrain)
        for water in terrain.waters:
            self.add(water)
        (length, width) = size
        trees = min(10, random.randint(0, (length / 10) * (width / 10)))
        for t in range(trees):
            self.add(TexturedTree(shader=shader, shaderLeaf=shaderLeaf, position=terrain.getRandomPointOnGrass(),
                                  trunkTextures=trunkTextures, leavesTextures=leavesTextures, light_dir=light_dir,
                                  viewer=viewer, leafTexture=leafTexture))
