extends Node3D
## Robô visual. Recebe a pose (x, y, theta) vinda da ponte e se posiciona na cena.
## A pose do ROS é planar (metros). Os parâmetros abaixo permitem alinhar/escalar
## essa pose ao modelo da casa, já que o mapa do ROS e a casa do Blender são
## sistemas de coordenadas independentes.

@export var escala: float = 1.0            # metros do ROS -> unidades do Godot
@export var altura: float = 0.45           # altura fixa do corpo acima do chão
@export var inverter_z: bool = true        # mapeia Y(ROS) -> -Z(Godot)
@export var offset: Vector3 = Vector3.ZERO # deslocamento para alinhar à casa
@export var offset_theta_graus: float = 0.0

var _mat: ShaderMaterial

func _ready() -> void:
	var corpo := get_node_or_null("Corpo")
	if corpo and corpo is MeshInstance3D:
		var m = corpo.get_active_material(0)
		if m is ShaderMaterial:
			_mat = m

func aplicar_pose(x: float, y: float, theta: float) -> void:
	var z := (-y if inverter_z else y)
	position = Vector3(x * escala, altura, z * escala) + offset
	rotation.y = theta + deg_to_rad(offset_theta_graus)

func definir_emergencia(ativo: bool) -> void:
	if _mat:
		_mat.set_shader_parameter("emergencia", 1.0 if ativo else 0.0)
