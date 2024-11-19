#version 330

// PBR using the Cook-Torrance microfacet model
// Trowbridge-Reitz GGX normal distribution function, 1975
// the term GGX means “ground glass unknown", it is derived from the scattering of glass (volume shading)
//  by Brucee Walter (Microfacet Models for Refraction through Rough Surfaces)

struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
};

out vec4 FragColor;

in VS_OUT {
    vec3 FragPos;
    vec3 Normal;
    vec2 TexCoords;
} fs_in;

uniform sampler2D Texture;
uniform sampler2D AOTexture;
uniform PointLight pointLights[3];

uniform vec3 lightWeight;
uniform vec4 ambientLight;
uniform vec3 viewPos;
uniform bool blinn;
uniform float AOMult = 1.0;

const float PI = 3.14159265359;

// Trowbridge-Reitz GGX, original is without squaring twice the roughness
// input N = normal, H = halfway, roughness (0 = smooth)

float DistributionGGX(vec3 N, vec3 H, float roughness)
{
	float a      = roughness*roughness;
	float a2     = a * a;
	float NdotH  = max(dot(N, H), 0.0);
	float NdotH2 = NdotH*NdotH;
        
	float nom    = a2;
	float denom  = (NdotH2 * (a2 - 1.0) + 1.0);
	denom        = PI * denom * denom;
        
	return nom / denom;
}

// smith-shadowing model for microfacet shadows, the Schlick-Beckmann approximation is included not
// to calculate the roughness twice. 
// input N = normal, V = view, L= light, roughness (0 = smooth)

float GeometrySmith(vec3 N, vec3 V, vec3 L, float roughness)
{
	float NdotV = max(dot(N, V), 0.0);
	float NdotL = max(dot(N, L), 0.0);

	// SchlickGGX for view direction   
	float r = roughness + 1.0;
    	float k = (r*r) / 8.0;			// original is without squaring
	float ggx1 = NdotV / (NdotV * (1.0 - k) + k);

	// SchlickGGX for light direction   
	float ggx2 = NdotL / (NdotL * (1.0 - k) + k);

	return ggx1 * ggx2;
}

// Fresnel-Schlick Approximation (simplifying the Fresnel equoations)

vec3 fresnelSchlick(float cosTheta, vec3 F0)
{
	return F0 + (1.0 - F0) * pow(clamp(1.0 - cosTheta, 0.0, 1.0), 5.0);
}


void main()
{
	vec3 color = texture(Texture, fs_in.TexCoords).rgb;
	float ao = texture(AOTexture, fs_in.TexCoords).r;
	float transp = texture(Texture, fs_in.TexCoords).a;
	if (transp < 0.01) discard;

	// ambient
	vec3 ambient = ambientLight[3] * color * vec3(ambientLight);

	vec3 normal = normalize(fs_in.Normal);
	vec3 diffuse = vec3(0.0, 0.0, 0.0);
	vec3 specular = vec3(0.0, 0.0, 0.0);
	vec3 viewDir = normalize(viewPos - fs_in.FragPos);
	vec3 specw = vec3(lightWeight[0]);

	for (int i = 0; i < 3; i++) {
		if (pointLights[i].intensity > 0.01) {
			// diffuse
			vec3 position = pointLights[i].position;
			vec3 lightDir = normalize(position - fs_in.FragPos);
			float d = length(position - fs_in.FragPos);
			float attenuation = pointLights[i].intensity / (d * d);
			// TODO d not 0
			float l = d / pointLights[i].intensity;
			float diff = max(dot(lightDir, normal), 0.0) /l;
			diffuse += diff * pointLights[i].color * color;

			// specular
			float spec = 0.0;
			if(blinn) {
				vec3 halfwayDir = normalize(lightDir + viewDir);  
				spec = pow(max(dot(normal, halfwayDir), 0.0), lightWeight[1]) / l;
			} else {
				vec3 reflectDir = reflect(-lightDir, normal);
				spec = pow(max(dot(viewDir, reflectDir), 0.0), lightWeight[1]) / l;
			}
			specular += specw * pointLights[i].color * spec;
		}
	}
	color = (ambient + diffuse + specular) * ao * AOMult;
	//color = color / (color + vec3(1.0));
    	//color = pow(color, vec3(1.0/2.2));  
   
	FragColor = vec4(color, transp);
}

