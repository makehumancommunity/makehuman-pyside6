#version 330

layout (location = 0) in vec4 aPos;
layout (location = 1) in vec4 aNormal;
layout (location = 2) in vec2 aTexCoords;

struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
    int type;
};

uniform mat4 uMvpMatrix;
uniform mat4 uModelMatrix;
uniform mat4 uNormalMatrix;
uniform mat4 uProjectionViewMatrix;
uniform vec3 viewPos;

uniform PointLight pointLights[3];

out VS_OUT {
	vec3 Normal;
	vec2 texCoord;
	mat4 projection;
	mat4 model;
	vec3 lightPos;
	vec3 camPos;
} vs_out;

void main()
{
	vs_out.camPos = viewPos;
	vs_out.projection = uProjectionViewMatrix;
	vs_out.lightPos = pointLights[0].position;
	vs_out.texCoord = aTexCoords;
	vs_out.model = uModelMatrix;
	vs_out.Normal = vec3(aNormal);
	gl_Position = uMvpMatrix *  aPos;
}

