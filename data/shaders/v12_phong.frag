#version 120

struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
    int type;
};

varying vec3 vFragPos;
varying vec3 vNormal;
varying vec2 vTexCoords;

uniform sampler2D Texture;
uniform sampler2D AOTexture;
uniform PointLight pointLights[3];

uniform vec3 lightWeight;
uniform vec4 ambientLight;
uniform vec3 viewPos;
uniform bool blinn;
uniform float AOMult;

void main()
{
	vec3 color = texture2D(Texture, vTexCoords).rgb;
	float transp = texture2D(Texture, vTexCoords).a;
	if (transp < 0.01) discard;

	float ao = texture2D(AOTexture, vTexCoords).r;

	// ambient
	vec3 ambient = ambientLight[3] * color * vec3(ambientLight);

	// diffuse
	vec3 normal = normalize(vNormal);
	vec3 diffuse = vec3(0.0, 0.0, 0.0);
	vec3 specular = vec3(0.0, 0.0, 0.0);
	vec3 viewDir = normalize(viewPos - vFragPos);
	vec3 specw = vec3(lightWeight[0]);

	for (int i = 0; i < 3; i++) {
		if (pointLights[i].intensity > 0.01) {
			// diffuse
			vec3 position = pointLights[i].position;
			vec3 L = vec3(0.0);
			float diff = 0.0;
			float l = length(position - vFragPos) / pointLights[i].intensity;
			if (pointLights[i].type == 0) {
				L = normalize(position - vFragPos);
				diff = max(dot(L, normal), 0.0) /l;
			} else {
				L = normalize(position);
				diff = clamp(dot(L, normal), 0.0, 1.0) / 2.0;
			}
			diffuse += diff * pointLights[i].color * color;

			// specular
			float spec = 0.0;
			if(blinn) {
				vec3 halfwayDir = normalize(L + viewDir);
				spec = pow(max(dot(normal, halfwayDir), 0.0), lightWeight[1]) / l;
			} else {
				vec3 reflectDir = reflect(-L, normal);
				spec = pow(max(dot(viewDir, reflectDir), 0.0), lightWeight[1]) / l;
			}
			specular += specw * pointLights[i].color * spec;
		}
	}

	gl_FragColor = vec4((ambient + diffuse + specular) * ao * AOMult, transp);
}

