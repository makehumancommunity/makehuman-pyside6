#version 330 core
layout (location = 0) in vec3 position;
out vec3 TexCoords;

uniform mat4 uModelMatrix;

void main()
{
    vec4 pos = uModelMatrix * vec4(position, 1.0) - uModelMatrix[3];
    gl_Position = pos.xyww;
    TexCoords = position;
}
