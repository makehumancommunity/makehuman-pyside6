#version 330

struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
    int type;
};

out vec4 FragColor;

in VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoords;
} fs_in;

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


void main (void)
{
	// Texture color
	vec3 color = texture(Texture, fs_in.TexCoords).rgb;
	float transp = texture(Texture, fs_in.TexCoords).a;

	// Silhouette Color:
	vec3 silhouetteColor = vec3(0.0, 0.0, 0.0);

	vec3 Normal = normalize(fs_in.Normal);
	vec3 viewDir = normalize(viewPos-fs_in.FragPos);
        vec3 diffuse = vec3(0.0, 0.0, 0.0);
        vec3 specular = vec3(0.0, 0.0, 0.0);

	vec3 ambient = ambientLight[3] * color * vec3(ambientLight);

	for (int i = 0; i < 3; i++) {
		if (pointLights[i].intensity > 0.01) {

			vec3 lightPos = pointLights[i].position;
			vec3 LightVert = normalize(lightPos - fs_in.FragPos);
			vec3 EyeLight = normalize(LightVert + viewDir);

			// Simple Silhouette
			float sil = max(dot(Normal, EyeLight), 0.0);
			if (sil >= silhouetteThreshold) {
				float diff = 0.0;
				if (pointLights[i].type == 0) {
					float l = length(lightPos - fs_in.FragPos) / pointLights[i].intensity;
					diff = max(dot(Normal, LightVert), 0.0) / l;
                        	} else {
                                	vec3 L = normalize(lightPos);
                                	diff = clamp(dot(L, Normal), 0.0, 1.0) / 2.0;
                        	}

				// Diffuse part
				diff = diffuseIntensity * smoothstep(diffuse_th-0.01, diffuse_th, diff);
				diffuse += diff * pointLights[i].color  * pointLights[i].intensity * color;

				// Specular part
				float spec = pow(max(dot(Normal, EyeLight), 0.0), shininess);
				spec = specularIntensity * smoothstep(specular_th-0.01, specular_th, spec);
				specular += diff * pointLights[i].color * color;
			}
		}
	}
	FragColor = vec4(ambient + diffuse + specular, transp);
}

