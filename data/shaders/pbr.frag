#version 330

// PBR using the Cook-Torrance microfacet model
// Trowbridge-Reitz GGX normal distribution function, 1975
// the term GGX means “ground glass unknown", it is derived from the scattering of glass (volume shading)
//  by Bruce Walter (Microfacet Models for Refraction through Rough Surfaces)

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
const float min_roughness = 0.04;

// calculation of normals
//
vec3 EvalNormal()
{
	vec3 pos_dx = dFdx(fs_in.FragPos);
	vec3 pos_dy = dFdy(fs_in.FragPos);
	vec3 tex_dx = dFdx(vec3(fs_in.TexCoords, 0.0));
	vec3 tex_dy = dFdy(vec3(fs_in.TexCoords, 0.0));
	vec3 t = (tex_dy.t * pos_dx - tex_dx.t * pos_dy) / (tex_dx.s * tex_dy.t - tex_dy.s * tex_dx.t);

	vec3 ng = cross(pos_dx, pos_dy);

	t = normalize(t - ng * dot(ng, t));
	vec3 b = normalize(cross(ng, t));
	mat3 tbn_n = mat3(t, b, ng);

	vec3 no = texture(NOTexture, fs_in.TexCoords).rgb;
	no = normalize(tbn_n * ((2.0 * no - 1.0) * vec3(1.0, 1.0, 1.0)));
	return no;

}

// Trowbridge-Reitz GGX, original is without squaring twice the roughness
// input N = normal, H = halfway, roughness (0 = smooth)

float DistributionGGX(vec3 N, vec3 H, float roughness)
{
	float a      = roughness*roughness;
	float a2     = a * a;
	float NdotH  = clamp(dot(N, H), 0.0, 1.0);
	float NdotH2 = NdotH*NdotH;
        
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


// bidirectional reflectance distribution function

vec3 brdf(vec3 n, vec3 V, vec3 L, float rough, vec3 F0, vec3 c_diff, vec3 radiance)
{
        vec3 H = normalize(L+V);
        float nl = clamp(dot(n, L), 0.001, 1.0);        // computed only once, used in Smith
        float nv = clamp(abs(dot(n, V)), 0.001, 1.0);   // and also inside brdf

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
	vec4 basecolor = texture(Texture, fs_in.TexCoords);
	float transp = basecolor.a;
	if (transp < 0.01) discard;

	vec3 color = basecolor.rgb;

	float ao = texture(AOTexture, fs_in.TexCoords).r;
	vec2  mr = texture(MRTexture, fs_in.TexCoords).rg;
	vec3  em = texture(EMTexture, fs_in.TexCoords).rgb;

	float metallic  = clamp(1.0 - (mr.g * MeMult), 0.0, 1.0);
	float roughness = clamp(mr.r * RoMult, min_roughness, 1.0);

	vec3 F0 = mix(vec3(min_roughness), color, metallic);

	vec3 c_diff = mix(vec3(0.0), color * (1 - min_roughness), 1.0 - metallic);


	// reflectance equation
	vec3 outcolor = vec3(0.0);
	vec3 normal = normalize(fs_in.Normal);
	if (NoMult > 0) {
		normal = mix(normal, EvalNormal(), NoMult * 0.1);
	}
	vec3 viewDir = normalize(viewPos - fs_in.FragPos);

	for (int i = 0; i < 3; i++) {
		if (pointLights[i].intensity > 0.01) {
			vec3 lightpos = pointLights[i].position;
			float attenuation = 0.0;
			vec3 L = vec3(0.0);
			if (pointLights[i].type == 0) {
				// calculate per-light radiance (point-Light)
        			L = normalize(lightpos - fs_in.FragPos);
        			float distance    = length(lightpos - fs_in.FragPos);
        			// since light is lm/sr, us a factor
        			attenuation = (pointLights[i].intensity * 50.0) / (distance * distance);
			} else {
				L = normalize(lightpos);
        			attenuation = pointLights[i].intensity / 4.0;
			}
        		vec3 radiance     = pointLights[i].color * attenuation;

			outcolor += brdf(normal, viewDir, L, roughness, F0, c_diff, radiance);
		}
	}
	vec3 ambient = ambientLight[3] * color * vec3(ambientLight) * ao * AOMult;
	color = ambient + outcolor;

	// emissive map
	color.xyz += EmMult * em;

	// cubemap
	if (useSky) {
		vec3 r = reflect(fs_in.FragPos, normalize(fs_in.Normal));
		color.xyz += color.xyz * vec3(texture(skybox, r)) * metallic;
	}

	FragColor = vec4(clamp(color, 0.0, 1.0), transp);
}

