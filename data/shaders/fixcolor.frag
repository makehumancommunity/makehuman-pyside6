#version 330

in VS_OUT {
    vec3 FragPos;
    vec3 Color;
} fs_in;

const float transp = 0.4;

void main()
{
	gl_FragColor =  vec4(fs_in.Color, transp);
}

