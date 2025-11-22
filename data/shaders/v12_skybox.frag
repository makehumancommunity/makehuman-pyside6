#version 120

varying vec3 TexCoords;

uniform samplerCube skybox;

void main()
{
	gl_FragColor = textureCube(skybox, TexCoords).bgra;
}
