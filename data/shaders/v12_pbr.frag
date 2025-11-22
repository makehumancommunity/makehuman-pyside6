#version 120

// PBR using the Cook-Torrance microfacet model
// Trowbridge-Reitz GGX normal distribution function, 1975
// the term GGX means "ground glass unknown", it is derived from the scattering of glass (volume shading)
// by Bruce Walter (Microfacet Models for Refraction through Rough Surfaces)

struct PointLight {
    vec3 position;
    vec3 color;
    float intensity;
    int type;
};

varying vec3 vFragPos;
varying vec3 vNormal;
varying vec2 vTexCoords;

uniform samplerCube skybox;
uniform sampler2D Texture;
uniform sampler2D AOTexture;
uniform sampler2D MRTexture;
uniform sampler2D EMTexture;
uniform sampler2D NOTexture;

uniform float AOMult;
uniform float RoMult;
uniform float MeMult;
uniform float EmMult;
uniform float NoMult;
uniform bool useSky;

uniform vec4 ambientLight;
uniform vec3 viewPos;

uniform PointLight pointLights[3];

const float PI = 3.14159265359;
const float min_roughness = 0.25;
const float glossiness = 0.1;

// calculation of normals
vec3 EvalNormal()
{
	// Note: dFdx/dFdy not available in GLSL 1.2, approximate with simplified normal calc
	// For now, just return the normal as-is
	return normalize(vNormal);
}

// Trowbridge-Reitz GGX, original is without squaring twice the roughness
// input N = normal, H = halfway, roughness (0 = smooth)
float DistributionGGX(vec3 N, vec3 H, float roughness)
{
	float a      = roughness * roughness;
	float a2     = a * a;
	float NdotH  = clamp(dot(N, H), 0.0, 1.0);
	float NdotH2 = NdotH * NdotH;
        
	float denom  = (NdotH2 * (a2 - 1.0) + 1.0);
        
	return a2 / (PI * denom * denom);
}

// smith-shadowing model for microfacet shadows, the Schlick-Beckmann approximation is included not
// to calculate the roughness twice. 
// input N = normal, V = view, L= light, roughness (0 = smooth)
float GeometrySmith(float NdotV, float NdotL, float roughness)
{
	// SchlickGGX for view direction   
	float r = roughness + 1.0;
    	float k = (r * r) / 8.0;
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

// bidirectional reflectance distribution function
vec3 brdf(vec3 n, vec3 V, vec3 L, float rough, vec3 F0, vec3 c_diff, vec3 radiance)
{
	vec3 H = normalize(L + V);
	float nl = clamp(dot(n, L), 0.001, 1.0);
	float nv = clamp(abs(dot(n, V)), 0.001, 1.0);

	// cook-torrance brdf
	float NDF = DistributionGGX(n, H, rough);
	float G   = GeometrySmith(nv, nl, rough);
	vec3 F    = fresnelSchlick(clamp(dot(H, V), 0.0, 1.0), F0);

	vec3 diffuse = (1.0 - F) * c_diff / PI;
	vec3 spec = F * G * NDF / (4.0 * nl * nv + 0.001);

	vec3 color = nl * radiance * (diffuse + spec);
	return color;
}

void main()
{
	// The metalness values are sampled from the B channel.
	// The roughness values are sampled from the G channel. Texture seems to be .bgr, so b becomes .r

	vec4 basecolor = texture2D(Texture, vTexCoords);
	float transp = basecolor.a;
	if (transp < 0.01) discard;

	vec3 color = basecolor.rgb;

	float ao = texture2D(AOTexture, vTexCoords).r;
	float metallic = texture2D(MRTexture, vTexCoords).b;
	float roughness = texture2D(MRTexture, vTexCoords).r + min_roughness;
	vec3  em = texture2D(EMTexture, vTexCoords).rgb;

	metallic  = clamp(metallic * (1.0 - MeMult), 0.0, 1.0);
	roughness = clamp(roughness * RoMult * (1.0 - min_roughness), min_roughness, 1.0);

	vec3 F0 = mix(vec3(min_roughness), color, metallic);

	vec3 c_diff = mix(vec3(0.0), color * (1.0 - min_roughness), 1.0 - metallic);

	// reflectance equation
	vec3 outcolor = vec3(0.0);
	vec3 normal = normalize(vNormal);
	if (NoMult > 0.0) {
		normal = mix(normal, EvalNormal(), NoMult * 0.04);
	}
	vec3 viewDir = normalize(viewPos - vFragPos);

	for (int i = 0; i < 3; i++) {
		if (pointLights[i].intensity > 0.01) {
			vec3 lightpos = pointLights[i].position;
			float attenuation = 0.0;
			vec3 L = vec3(0.0);
			if (pointLights[i].type == 0) {
				// calculate per-light radiance (point-Light)
        			L = normalize(lightpos - vFragPos);
        			float distance = length(lightpos - vFragPos);
        			// since light is lm/sr, use a factor
        			attenuation = (pointLights[i].intensity * 50.0) / (distance * distance);
			} else {
				L = normalize(lightpos);
        			attenuation = pointLights[i].intensity / 4.0;
			}
        		vec3 radiance = pointLights[i].color * attenuation;

			outcolor += brdf(normal, viewDir, L, roughness, F0, c_diff, radiance);
		}
	}

	vec3 ambient = ambientLight[3] * vec3(ambientLight) * ao * AOMult;

	// cubemap, create some reflection in case of metal
	if (useSky) {
		vec3 r = reflect(-vFragPos, viewDir);
		ambient = ambient * color * (1.0 - metallic * glossiness);
		outcolor.rgb = mix(outcolor.rgb, vec3(textureCube(skybox, r).bgr), metallic * glossiness);
		color = ambient + outcolor;
	} else {
		color = ambient * color + outcolor;
	}

	// emissive map
	color.rgb += EmMult * em;

	gl_FragColor = vec4(clamp(color, 0.0, 1.0), transp);
}
