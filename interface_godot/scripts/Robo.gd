extends Node3D
## Robô visual. Recebe a pose (x, y, theta) vinda da ponte e se posiciona na cena.
##
## Modelo: se existir `models/miniRobot.glb` (importado), ele SUBSTITUI a cápsula
## placeholder automaticamente. Enquanto o .glb não estiver no projeto, continua
## a cápsula azul — assim a cena nunca quebra.
##
## A pose do ROS é planar (metros). Os parâmetros abaixo alinham/escalam essa
## pose ao modelo da casa (frames independentes entre ROS e Godot).

@export var escala: float = 1.0            # metros do ROS -> unidades do Godot
@export var altura: float = 0.45           # altura do corpo acima do chão
@export var inverter_z: bool = true        # mapeia Y(ROS) -> -Z(Godot)
@export var offset: Vector3 = Vector3.ZERO # deslocamento para alinhar à casa
@export var offset_theta_graus: float = 0.0

@export_group("Modelo externo (novo robô)")
@export var modelo_path: String = "res://models/miniRobot.glb"
# miniRobot.glb nasce com ~4.74 m (gigante). 0.28 o deixa com ~1.3 m (altura de
# um assistente de pé) — bem visível no ambiente. Afine no Inspector.
@export var modelo_escala: float = 0.28                # ajuste o tamanho aqui
# Alinha a frente do modelo com a direção de movimento (+X, onde o theta aponta).
# A cara do modelo nasce apontando +Z (convenção do export Blender->glTF), então
# +90° em Y a traz para +X. Se ainda ficar errado: 270/-90 = costas pra frente;
# 0 ou 180 = de lado.
@export var modelo_rotacao_graus: Vector3 = Vector3(0.0, 90.0, 0.0)
# desce/levanta o modelo p/ os "pés" encostarem no chão (pivô do .glb não está nos pés).
@export var modelo_offset: Vector3 = Vector3(0.0, 0.11, 0.0)

var _mat: ShaderMaterial
var _luz_emergencia: OmniLight3D
var _em_emergencia: bool = false
var _t: float = 0.0

func _ready() -> void:
	_carregar_modelo_externo()

	# material da cápsula (só usado se o modelo externo não estiver presente)
	var corpo := get_node_or_null("Corpo")
	if corpo and corpo is MeshInstance3D:
		var m = corpo.get_active_material(0)
		if m is ShaderMaterial:
			_mat = m

	# luz de emergência: pulsa vermelho e funciona com QUALQUER modelo
	_luz_emergencia = OmniLight3D.new()
	_luz_emergencia.light_color = Color(1.0, 0.12, 0.06)
	_luz_emergencia.omni_range = 4.0
	_luz_emergencia.light_energy = 0.0
	_luz_emergencia.position = Vector3(0, 0.6, 0)
	add_child(_luz_emergencia)

func _carregar_modelo_externo() -> void:
	if modelo_path == "" or not ResourceLoader.exists(modelo_path):
		return  # ainda sem o .glb: mantém a cápsula placeholder
	var cena = load(modelo_path)
	if cena == null:
		push_warning("[Robo] não consegui carregar o modelo: " + modelo_path)
		return
	var inst = cena.instantiate()
	inst.name = "Modelo"
	inst.scale = Vector3.ONE * modelo_escala
	inst.rotation = Vector3(
		deg_to_rad(modelo_rotacao_graus.x),
		deg_to_rad(modelo_rotacao_graus.y),
		deg_to_rad(modelo_rotacao_graus.z))
	inst.position = modelo_offset
	add_child(inst)
	# esconde a cápsula/placeholder
	for nome in ["Corpo", "Frente"]:
		var c = get_node_or_null(nome)
		if c:
			c.visible = false
	print("[Robo] modelo externo carregado: ", modelo_path)

func aplicar_pose(x: float, y: float, theta: float) -> void:
	var z := (-y if inverter_z else y)
	position = Vector3(x * escala, altura, z * escala) + offset
	rotation.y = theta + deg_to_rad(offset_theta_graus)

func definir_emergencia(ativo: bool) -> void:
	_em_emergencia = ativo
	if _mat:
		_mat.set_shader_parameter("emergencia", 1.0 if ativo else 0.0)
	if not ativo and _luz_emergencia:
		_luz_emergencia.light_energy = 0.0

func _process(delta: float) -> void:
	if _em_emergencia and _luz_emergencia:
		_t += delta
		# pulso suave entre ~1 e ~5 de energia
		_luz_emergencia.light_energy = 3.0 + 2.0 * sin(_t * 9.0)
