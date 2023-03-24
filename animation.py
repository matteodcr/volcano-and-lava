# Python built-in modules
from bisect import bisect_left      # search sorted keyframe lists

# External, non built-in modules
import OpenGL.GL as GL              # standard Python OpenGL wrapper
import glfw                         # lean window system wrapper for OpenGL
import numpy as np                  # all matrix manipulations & OpenGL args

from core import Node
from transform import (lerp, quaternion_slerp, quaternion_matrix, vec,
                       identity)


# -------------- Keyframing Utilities TP6 ------------------------------------
class KeyFrames:
    """ Stores keyframe pairs for any value type with interpolation_function"""
    def __init__(self, time_value_pairs, interpolation_function=lerp):
        if isinstance(time_value_pairs, dict):  # convert to list of pairs
            time_value_pairs = time_value_pairs.items()
        keyframes = sorted(((key[0], key[1]) for key in time_value_pairs))
        self.times, self.values = zip(*keyframes)  # pairs list -> 2 lists
        self.interpolate = interpolation_function

    def value(self, time):
        """ Computes interpolated value from keyframes, for a given time """

        # 1. ensure time is within bounds else return boundary keyframe
        time = max(min(time, self.times[-1]), self.times[0])

        # 2. search for closest index entry in self.times, using bisect_left
        closest_index = bisect_left(self.times, time)
        
        fraction = (time - self.times[closest_index-1])/(self.times[closest_index]-self.times[closest_index-1])

        # 3. using the retrieved index, interpolate between the two neighboring
        # values in self.values, using the stored self.interpolate function
        return self.interpolate(self.values[closest_index-1], self.values[closest_index], fraction)


class TransformKeyFrames:
    """ KeyFrames-like object dedicated to 3D transforms """
    def __init__(self, translate_keys, rotate_keys, scale_keys):
        """ stores 3 keyframe sets for translation, rotation, scale """
        self.translation = KeyFrames(translate_keys)
        self.scale = KeyFrames(scale_keys)
        
        if isinstance(rotate_keys, dict):  # convert to list of pairs
            rotate_keys = rotate_keys.items()
        keyframes = sorted(((key[0], key[1]) for key in rotate_keys))
        self.rotation_times, self.rotation_values = zip(*keyframes)  # pairs list -> 2 lists

    def value(self, time):
        """ Compute each component's interpolation and compose TRS matrix """
        # 1. ensure time is within bounds else return boundary keyframe
        min_time = max(self.translation.times[0], max(self.scale.times[0], self.rotation_times[0]))
        max_time = min(self.translation.times[-1], min(self.scale.times[-1], self.rotation_times[-1]))
        time = min(max(time, min_time), max_time)
        
        # 2. search for closest index entry in self.times, using bisect_left
        closest_index = bisect_left(self.rotation_times, time)
        fraction = (time - self.rotation_times[closest_index-1])/(self.rotation_times[closest_index]-self.rotation_times[closest_index-1])
        
        T = self.translation.value(time)
        S = self.scale.value(time)
        R = quaternion_slerp(self.rotation_values[closest_index-1], self.rotation_values[closest_index], fraction)
        R = quaternion_matrix(R)
        R = R*S
        for i in range(3):
            R[i][3]= T[i]
        R[3][3]=1
        
        return R


class KeyFrameControlNode(Node):
    """ Place node with transform keys above a controlled subtree """
    def __init__(self, trans_keys, rot_keys, scale_keys, transform=identity()):
        super().__init__(transform=transform)
        self.keyframes = TransformKeyFrames(trans_keys, rot_keys, scale_keys)

    def draw(self, primitives=GL.GL_TRIANGLES, **uniforms):
        """ When redraw requested, interpolate our node transform from keys """
        self.transform = self.keyframes.value(glfw.get_time())
        super().draw(primitives=primitives, **uniforms)


# -------------- Linear Blend Skinning : TP7 ---------------------------------
class Skinned:
    """ Skinned mesh decorator, passes bone world transforms to shader """
    def __init__(self, mesh, bone_nodes, bone_offsets):
        self.mesh = mesh

        # store skinning data
        self.bone_nodes = bone_nodes
        self.bone_offsets = np.array(bone_offsets, np.float32)

    def draw(self, **uniforms):
        world_transforms = [node.world_transform for node in self.bone_nodes]
        uniforms['bone_matrix'] = world_transforms @ self.bone_offsets
        self.mesh.draw(**uniforms)
