#version 330 core

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
in vec3 tex_coord;
in vec3 position;

out vec2 frag_tex_coord;
out vec3 normalized_pos;

void main() {
    frag_tex_coord = tex_coord.xy;
    vec4 tmp_pos =(model * vec4(position, 1));
    normalized_pos = tmp_pos.xyz / tmp_pos.w;
    gl_Position = projection * view * model * vec4(position, 1);
}
