#version 330

const vec3 lightColor = vec3(0.8, 0.8, 0.8);
const vec3 lightPosition = vec3(5.0, 7.0, 2.0);
const vec3 ambientLight = vec3(0.3, 0.3, 0.3);

uniform sampler2D uSampler;

in vec3 vPosition;
in vec3 vNormal;
in vec2 vTexCoord;

void main()
{
	vec4 color = texture2D(uSampler, vTexCoord);
	vec3 normal = normalize(vNormal);
	vec3 lightDirection = normalize(lightPosition - vPosition);
	float nDotL = max(dot(lightDirection, normal), 0.0);
	vec3 diffuse = lightColor * color.rgb * nDotL;
	vec3 ambient = ambientLight * color.rgb;
	gl_FragColor = vec4(diffuse + ambient, color.a);
}

