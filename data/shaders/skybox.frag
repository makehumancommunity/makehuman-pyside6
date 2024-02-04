#version 330 core
in vec3 TexCoords;
out vec4 color;

uniform samplerCube skybox;

void main()
{
	color = texture(skybox, TexCoords).bgra;
	//color = vec4(0.2,0.2,0.8, 1.0);
}
