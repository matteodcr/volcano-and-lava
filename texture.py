from itertools import cycle
import OpenGL.GL as GL              # standard Python OpenGL wrapper
from PIL import Image               # load texture maps
import glfw
import numpy as np                 # all matrix manipulations & OpenGL args
from core import Mesh, Node, Texture
import random


# -------------- OpenGL Texture Wrapper ---------------------------------------
class Texture:
    """ Helper class to create and automatically destroy textures """
    def __init__(self, tex_file, wrap_mode=GL.GL_REPEAT,
                 mag_filter=GL.GL_LINEAR, min_filter=GL.GL_LINEAR_MIPMAP_LINEAR,
                 tex_type=GL.GL_TEXTURE_2D):
        self.glid = GL.glGenTextures(1)
        self.type = tex_type
        try:
            # imports image as a numpy array in exactly right format
            tex = Image.open(tex_file).convert('RGBA')
            GL.glBindTexture(tex_type, self.glid)
            GL.glTexImage2D(tex_type, 0, GL.GL_RGBA, tex.width, tex.height,
                            0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, tex.tobytes())
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_S, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_WRAP_T, wrap_mode)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MIN_FILTER, min_filter)
            GL.glTexParameteri(tex_type, GL.GL_TEXTURE_MAG_FILTER, mag_filter)
            GL.glGenerateMipmap(tex_type)
            print(f'Loaded texture {tex_file} ({tex.width}x{tex.height}'
                  f' wrap={str(wrap_mode).split()[0]}'
                  f' min={str(min_filter).split()[0]}'
                  f' mag={str(mag_filter).split()[0]})')
        except FileNotFoundError:
            print("ERROR: unable to load texture file %s" % tex_file)

    def __del__(self):  # delete GL texture from GPU when object dies
        GL.glDeleteTextures(self.glid)


# -------------- Textured mesh decorator --------------------------------------
class Textured(Node):
    """ Drawable mesh decorator that activates and binds OpenGL textures """
    def __init__(self, drawable, **textures):
        super().__init__()
        self.drawable = drawable
        self.textures = textures

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        for index, (name, texture) in enumerate(self.textures.items()):
            GL.glActiveTexture(GL.GL_TEXTURE0 + index)
            GL.glBindTexture(texture.type, texture.glid)
            uniforms[name] = index
        self.drawable.draw(primitives=primitives, **uniforms)





# -------------- Textured Objects ---------------------------------

class TexturedSphere(Textured):
    """ Procedural textured sphere """
    #avec l'aide de : http://www.songho.ca/opengl/gl_sphere.html
    def __init__(self, shader, texture, position=(0,0,0), r=1, stacks=10, sectors=10, light_dir=None, shinyness=2):
        # setup plane mesh to be textured
        vertices = ()
        normals = ()
        tex_coord = ()
        
        lengthInv = 1.0 / r
        sectorStep = 2 * np.pi / sectors
        stackStep = np.pi / stacks        

        for i in range(stacks+1):
            stackAngle = np.pi / 2 - i * stackStep
            xy = r * np.cos(stackAngle)
            z = r * np.sin(stackAngle)

            for j in range(sectors+1):
                sectorAngle = j * sectorStep
                # vertex position (x, y, z)
                x = xy * np.cos(sectorAngle)
                y = xy * np.sin(sectorAngle)
                vertices = vertices+((x,y,z),)
                tex_coord += ((i/stacks, j/sectors),)
                #normalized vertex normal (nx, ny, nz)
                nx = x * lengthInv
                ny = y * lengthInv
                nz = z * lengthInv
                normals = normals+((nx,ny,nz),)
        scaled = np.array(vertices, np.float32)+np.array(position, np.float32)
        
        indices = ()
        for i in range(stacks):
            k1 = i * (sectors + 1)
            k2 = k1 + sectors + 1
            for j in range(sectors):
                
                # 2 triangles per sector excluding first and last stacks
                if(i != 0) :
                    indices = indices+((k1, k2, k1+1),)

                if(i != (stacks-1)):
                    indices = indices+((k1+1, k2, k2+1),)
                
                k1 = k1+1
                k2 = k2+1
        indices = np.array(indices, np.uint32)
        mesh = Mesh(shader, attributes=dict(position=scaled, tex_coord=np.array(tex_coord), normal=np.array(normals)), index=indices, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)

class Terrain(Textured):
    """ Procedural textured terrain """
    def __init__(self, shader, texture, size=(100,100), position=(0,0,0), light_dir=None, shinyness=2):
        (posx,posy,posz)=position
        (x,y)=size
        self.heatMap = np.random.random(size)
        # setup plane mesh to be textured
        base_coords = ()
        tex_coord = ()
        for i in range(x):
            for j in range(y):
                base_coords = base_coords+((i-x/2+posx, j-y/2+posy, posz+self.heatMap[i][j]/2),) 
                tex_coord += ((i%2, j%2),)
        scaled = np.array(base_coords, np.float32)
        
        indices = ()
        normals = np.zeros_like(scaled)
        for k in range(x, x*y):
            if(k+1<len(base_coords)):
                indices = indices+(k, k+1, k+1-x, k, k+1-x, k-x)
                
                # Calculate triangle normal
                v1, v2, v3 = scaled[k-x], scaled[k+1], scaled[k+1-x]
                tri_normal = np.cross(v2 - v1, v3 - v1)
                # Add triangle normal to vertex normals
                normals[k-x] += tri_normal
                normals[k+1] += tri_normal
                normals[k+1-x] += tri_normal
        
        # Normalize vertex normals
        normals = np.array([np.divide(n, np.sqrt(np.sum(n ** 2))) for n in normals])
        
        print(normals)
        
        indices = np.array(indices, np.uint32)
        mesh = Mesh(shader, attributes=dict(position=scaled, tex_coord=np.array(tex_coord), normal=normals), index=indices, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)

class TexturedPlane(Textured):
    """ Simple first textured object """
    def __init__(self, shader, texture, position=(0,0,0), light_dir=None, shinyness=2):
        (posx,posy,posz) = position
        # setup plane mesh to be textured
        base_coords = ((-1+posx, -1+posy, posz), (1+posx, -1+posy, posz), (1+posx, 1+posy, posz), (-1+posx, 1+posy, posz))
        tex_coord=((0,0),(1,0),(1,1),(0,1))
        scaled = 100 * np.array(base_coords, np.float32)
        indices = np.array((0, 1, 2, 0, 2, 3), np.uint32)
        normals=np.array(((0,0,1), (0,0,1), (0,0,1), (0,0,1)))
        mesh = Mesh(shader, attributes=dict(position=scaled, tex_coord=np.array(tex_coord), normal=normals), index=indices, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)
class TexturedCylinder(Textured):
    """ Simple first textured object """
    def __init__(self, shader, texture, height=1, divisions=50, r=0.5, position=(0,0,0), light_dir=None, shinyness=2):        
        self.height = height
        self.divisions = divisions
        self.ray = r

        # setup plane mesh to be textured
        vertices = ()
        tex_coord = ()
        normals = ()
        vertices = vertices + ((0, 0, self.height/2),)
        tex_coord += ((0,0),)
        normals += ((0, 0, 1),)
        tex_i=0
        for x in np.arange(0, 2*np.pi, 2*np.pi/self.divisions):
            vertices = vertices + ((self.ray*np.cos(x), self.ray*np.sin(x), self.height/2),)
            tex_coord += ((tex_i/divisions, 0),)
            normals += ((np.cos(x), np.sin(x), 0),)
            tex_i+=1
        vertices = vertices + ((0, 0, -self.height/2),)
        tex_coord += ((1,1),)
        normals += ((0, 0, -1),)
        tex_i=0
        for x in np.arange(0, 2*np.pi, 2*np.pi/self.divisions):
            vertices = vertices + ((self.ray*np.cos(x), self.ray*np.sin(x), -self.height/2),)
            tex_coord += ((tex_i/divisions, 1),)
            normals += ((np.cos(x), np.sin(x), 0),)
            tex_i+=1
        scaled = np.array(vertices, np.float32)+np.array(position, np.float32)
        
        index = ()
        #top face
        for x in range(1, self.divisions, 1):
            index = index + (0,x,x+1)
        index = index + (0,self.divisions,1)
        #bottom face
        for x in range(1, self.divisions, 1):
            index = index + (self.divisions+1,self.divisions+x+2,self.divisions+x+1)
        index = index + (self.divisions+1, self.divisions+2,self.divisions*2+1)
        #side
        for x in range(1, self.divisions, 1):
            index = index + (x,self.divisions+x+1,x+1,x+1,self.divisions+x+1,self.divisions+x+2)
        index = index + (self.divisions,self.divisions*2+1,1,1,self.divisions*2+1,self.divisions+2)
        indices = np.array(index, np.uint32)
        
        mesh = Mesh(shader, attributes=dict(position=scaled, tex_coord=np.array(tex_coord), normal=np.array(normals)), index=indices, s=shinyness, light_dir=light_dir)

        # setup & upload texture to GPU, bind it to shader name 'diffuse_map'
        super().__init__(mesh, diffuse_map=texture)

class TexturedTree(Node):
    def __init__(self, shader, position, leavesTextures, trunkTextures, light_dir=None):
        super().__init__()
        random.seed()
        
        (x,y,z) = position
        self.position = position
        trunk_height = 5+random.random()
        main_leaves_size = 2+random.random()
        
        self.add(TexturedCylinder(shader, position=(x,y,z+trunk_height/2), height=trunk_height, texture=trunkTextures, light_dir=light_dir))
        self.add(TexturedSphere(shader, position=(x,y,z+trunk_height), r=main_leaves_size, texture=leavesTextures, light_dir=light_dir))
        
        for i in range(random.randint(0, 3)):
            x_=x + (random.randint(0,1)*2-1)*random.random()*main_leaves_size
            y_=y + (random.randint(0,1)*2-1)*random.random()*(main_leaves_size-np.abs(x_-x))
            z_=z + (random.randint(0,1)*2-1)*(main_leaves_size-np.abs(x_-x)-np.abs(y_-y))
            self.add(TexturedSphere(shader, position=(x_,y_,z_+trunk_height), r=random.random(), texture=leavesTextures, light_dir=light_dir))
        
class ForestTerrain(Node):
    def __init__(self, shader, terrainTexture, trunkTextures, leavesTextures, size=(100,100), position=(0,0,0), light_dir=None ):
        super().__init__()
        self.add(Terrain(shader=shader, size=size, texture=terrainTexture, position=position, light_dir=light_dir))
        (length, width) = size
        (posx,posy,posz) = position
        trees = random.randint(0,(length/10)*(width/10))
        for t in range(trees):
            self.add(TexturedTree(shader=shader, position=(posx-length/2+length*random.random(),posy-width/2+width*random.random(),posz), trunkTextures=trunkTextures, leavesTextures=leavesTextures, light_dir=light_dir))