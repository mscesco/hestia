extends Node3D
## Nó raiz da interface. Faz polling em GET /status na ponte FastAPI e repassa
## a pose e o estado de emergência para o nó do robô.

@export var url_base: String = "http://127.0.0.1:8000"
@export var intervalo: float = 0.2  # segundos entre consultas

var _http: HTTPRequest
var _robo: Node
var _ocupado: bool = false
var _conectado: bool = false

func _ready() -> void:
	_robo = get_node_or_null("Robo")
	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_resposta)

	var t := Timer.new()
	t.wait_time = intervalo
	t.autostart = true
	add_child(t)
	t.timeout.connect(_poll)
	print("[Ponte] Interface Hestia iniciada. Lendo ", url_base, "/status")

func _poll() -> void:
	if _ocupado:
		return
	_ocupado = true
	var err := _http.request(url_base + "/status")
	if err != OK:
		_ocupado = false

func _on_resposta(_result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_ocupado = false
	if code != 200:
		if _conectado:
			print("[Ponte] sem resposta da ponte (code=", code, ")")
			_conectado = false
		return
	if not _conectado:
		print("[Ponte] conectado.")
		_conectado = true

	var dados = JSON.parse_string(body.get_string_from_utf8())
	if typeof(dados) != TYPE_DICTIONARY:
		return
	if _robo and dados.has("pose"):
		var p = dados["pose"]
		_robo.aplicar_pose(float(p.get("x", 0.0)), float(p.get("y", 0.0)), float(p.get("theta", 0.0)))
	if _robo and dados.has("atividade"):
		var atv := str(dados["atividade"]).to_lower()
		_robo.definir_emergencia(atv.contains("queda") or atv.contains("emerg"))
