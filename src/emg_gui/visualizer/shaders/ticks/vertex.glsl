#version 330 core

uniform mat4 P;

in vec2 vertex;

void main() {
    gl_Position = P * vec4(vertex, 0, 1);
}