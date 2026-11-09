// Shader autoral do robô Héstia.
// - Cor base metálica com realce de borda (fresnel) que reage à luz em tempo real.
// - Quando `emergencia` = 1.0, pulsa em vermelho (destaque de chamado de queda).
shader_type spatial;

uniform vec3 cor_base : source_color = vec3(0.12, 0.55, 0.9);
uniform vec3 cor_emergencia : source_color = vec3(1.0, 0.12, 0.08);
uniform float emergencia : hint_range(0.0, 1.0) = 0.0;
uniform float forca_rim : hint_range(0.0, 3.0) = 1.0;

void fragment() {
	float pulso = 0.5 + 0.5 * sin(TIME * 6.0);
	float emg = clamp(emergencia, 0.0, 1.0);
	vec3 cor = mix(cor_base, cor_emergencia, emg * pulso);

	ALBEDO = cor;
	METALLIC = 0.25;
	ROUGHNESS = 0.4;

	// realce de borda dependente do ângulo de visão (volume sob luz real)
	float fresnel = pow(1.0 - clamp(dot(normalize(NORMAL), normalize(VIEW)), 0.0, 1.0), 3.0);
	EMISSION = cor * fresnel * forca_rim * (0.3 + emg * pulso * 1.5);
}
