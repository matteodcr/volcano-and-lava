#version 330 core

// fragment position and normal of the fragment, in WORLD coordinates
in vec3 w_position, w_normal;
in vec3 normalized_pos;
uniform float gamma;
uniform float fog_offset;

uniform sampler2D diffuse_map;
in vec2 frag_tex_coords;

// light dir, in world coordinates
uniform vec3 light_dir;

// material properties
uniform vec3 k_a;
uniform float s;
// world camera position
uniform vec3 w_camera_position;
uniform vec3 skyColour;
const float density = 0.007;

out vec4 out_color;

void main() {
    // Compute all vectors, oriented outwards from the fragment
    vec3 n = normalize(w_normal);
    vec3 l = normalize(-light_dir);
    vec3 v = normalize(w_camera_position - w_position);
    vec3 r = reflect(-l, n);

    vec4 diffuse_color = texture(diffuse_map, frag_tex_coords).rgba * max(dot(n, l), 0);
    vec4 specular_color = texture(diffuse_map, frag_tex_coords).rgba * pow(max(dot(r, v), 0), s);

    float distance = distance(w_camera_position, normalized_pos);
    float visibility = (1/distance*density);
    visibility = clamp(visibility, 0.0,1.0);

    out_color = vec4(k_a, 1) + vec4(diffuse_color) + vec4(specular_color);

    out_color = mix( out_color, vec4(skyColour,1), clamp((1 - ((fog_offset - distance) / 50.0)), 0.0, 1.0));

    // Gamma correction
    out_color.xyz = pow(out_color.xyz, vec3(1.0/gamma));
    
}
