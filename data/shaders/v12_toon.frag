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
uniform PointLight pointLights[3];
uniform vec4 ambientLight;
uniform vec3 viewPos;

uniform float silhouetteThreshold = 0.2;
uniform float shininess = 20.0;
uniform float specularIntensity = 0.2;
uniform float diffuseIntensity = 0.4;
uniform float specular_th = 0.3;
uniform float diffuse_th = 0.5;

void main(void)
{
	// Texture color
	vec3 color = texture2D(Texture, vTexCoords).rgb;
	float transp = texture2D(Texture, vTexCoords).a;

	// Silhouette Color:
	vec3 silhouetteColor = vec3(0.0, 0.0, 0.0);

	vec3 Normal = normalize(vNormal);
	vec3 viewDir = normalize(viewPos - vFragPos);
	vec3 diffuse = vec3(0.0, 0.0, 0.0);
	vec3 specular = vec3(0.0, 0.0, 0.0);

	vec3 ambient = ambientLight[3] * color * vec3(ambientLight);

	for (int i = 0; i < 3; i++) {
		if (pointLights[i].intensity > 0.01) {

			vec3 lightPos = pointLights[i].position;
			vec3 LightVert = normalize(lightPos - vFragPos);
			vec3 EyeLight = normalize(LightVert + viewDir);

			// Simple Silhouette
			float sil = max(dot(Normal, EyeLight), 0.0);
			if (sil >= silhouetteThreshold) {
				float diff = 0.0;
				if (pointLights[i].type == 0) {
					float l = length(lightPos - vFragPos) / pointLights[i].intensity;
					diff = max(dot(Normal, LightVert), 0.0) / l;
                        	} else {
                                	vec3 L = normalize(lightPos);
                                	diff = clamp(dot(L, Normal), 0.0, 1.0) / 2.0;
                        	}

				// Diffuse part
				diff = diffuseIntensity * smoothstep(diffuse_th-0.01, diffuse_th, diff);
				diffuse += diff * pointLights[i].color * pointLights[i].intensity * color;

				// Specular part
				float spec = pow(max(dot(Normal, EyeLight), 0.0), shininess);
				spec = specularIntensity * smoothstep(specular_th-0.01, specular_th, spec);
				specular += diff * pointLights[i].color * color;
			}
		}
	}
	gl_FragColor = vec4(ambient + diffuse + specular, transp);
}

