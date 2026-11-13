extends Node3D
## Nó raiz da interface. Faz polling em GET /status na ponte FastAPI (pose +
## atividade) e repassa ao robô 3D. Também é o "painel do cuidador": autentica na
## ponte (/token) e envia pedidos (/pedido) quando o operador clica nos botões.

@export var url_base: String = "http://127.0.0.1:8000"
@export var intervalo: float = 0.2            # segundos entre consultas de status
@export var usuario: String = "operador"      # credencial da demo (bate com o servidor)
@export var senha: String = "hestia2026"

var _http: HTTPRequest                         # polling de /status
var _robo: Node
var _status_label: Label
var _ocupado: bool = false
var _conectado: bool = false

var _token: String = ""
var _pendentes: Array = []                     # pedidos aguardando token

func _ready() -> void:
	_robo = get_node_or_null("Robo")
	_status_label = get_node_or_null("HUD/Controles/VB/Status")

	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_resposta)

	var t := Timer.new()
	t.wait_time = intervalo
	t.autostart = true
	add_child(t)
	t.timeout.connect(_poll)

	# Botões do painel do cuidador (conectados por código p/ não depender do .tscn)
	_ligar_botao("HUD/Controles/VB/BtnAgua", "agua", "PEDIDO_COMUM", 5.0, -1.9)
	_ligar_botao("HUD/Controles/VB/BtnQueda", "queda", "EMERGENCIA", -7.9, 11.45)
	_ligar_botao("HUD/Controles/VB/BtnSala", "ir_sala", "PEDIDO_COMUM", -7.9, -1.8)

	_autenticar()
	print("[Ponte] Interface Hestia iniciada. Lendo ", url_base, "/status")

func _ligar_botao(caminho: String, tipo: String, prio: String, x: float, y: float) -> void:
	var b := get_node_or_null(caminho)
	if b and b is Button:
		b.pressed.connect(func(): _pedir(tipo, prio, x, y))

# ---------------- polling de status (pose + atividade) ----------------
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
		_set_status("sem conexão com a ponte")
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
	if dados.has("atividade"):
		var atv := str(dados["atividade"])
		_set_status(atv)
		if _robo:
			var a := atv.to_lower()
			_robo.definir_emergencia(a.contains("queda") or a.contains("emerg"))

func _set_status(texto: String) -> void:
	if _status_label:
		_status_label.text = "Status: " + texto

# ---------------- painel do cuidador: autenticação + pedidos ----------------
func _autenticar() -> void:
	var req := HTTPRequest.new()
	add_child(req)
	req.request_completed.connect(func(_r, code, _h, body):
		if code == 200:
			var d = JSON.parse_string(body.get_string_from_utf8())
			if typeof(d) == TYPE_DICTIONARY and d.has("access_token"):
				_token = str(d["access_token"])
				print("[Ponte] autenticado no painel do cuidador.")
				_drenar_pendentes()
		else:
			print("[Ponte] falha ao autenticar (code=", code, ")")
		req.queue_free()
	)
	var corpo := JSON.stringify({"usuario": usuario, "senha": senha})
	req.request(url_base + "/token", ["Content-Type: application/json"], HTTPClient.METHOD_POST, corpo)

func _pedir(tipo: String, prioridade: String, x: float, y: float) -> void:
	var pedido := {"tipo": tipo, "prioridade": prioridade, "x": x, "y": y}
	if _token == "":
		_pendentes.append(pedido)   # ainda sem token: envia assim que autenticar
		_autenticar()
		return
	_enviar_pedido(pedido)

func _drenar_pendentes() -> void:
	for pedido in _pendentes:
		_enviar_pedido(pedido)
	_pendentes.clear()

func _enviar_pedido(pedido: Dictionary) -> void:
	var req := HTTPRequest.new()
	add_child(req)
	req.request_completed.connect(func(_r, code, _h, _body):
		if code == 200:
			print("[Ponte] pedido enviado: ", pedido)
		elif code == 401:
			print("[Ponte] token expirado — reautenticando.")
			_token = ""
			_pendentes.append(pedido)
			_autenticar()
		else:
			print("[Ponte] pedido recusado (code=", code, ")")
		req.queue_free()
	)
	var cabec := ["Content-Type: application/json", "Authorization: Bearer " + _token]
	req.request(url_base + "/pedido", cabec, HTTPClient.METHOD_POST, JSON.stringify(pedido))
