#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
in vec3 tex_coord;
in vec3 position;
in vec3 normal;

out vec2 frag_tex_coords;

out vec3 w_position, w_normal;   // in world coordinates
out vec3 normalized_pos;

void main() {
    w_normal = (model * vec4(normal, 0)).xyz;
    w_position =  (model * vec4(position, 1)).xyz;

    vec4 tmp_pos =(model * vec4(position, 1));
    normalized_pos = tmp_pos.xyz / tmp_pos.w;

    gl_Position = projection * view * model * vec4(position, 1);
    frag_tex_coords = tex_coord.xy;
}
