extends Node3D
## Nó raiz da interface. Faz polling em GET /status na ponte FastAPI (pose +
## atividade) e repassa ao robô 3D. Também é o "painel do cuidador": autentica na
## ponte (/token) e envia pedidos (/pedido) quando o operador clica nos botões.
## Todo o visual do HUD é estilizado aqui em _ready (não depende de editar a cena).

@export var url_base: String = "http://127.0.0.1:8000"
@export var intervalo: float = 0.2            # segundos entre consultas de status
@export var usuario: String = "operador"      # credencial da demo (bate com o servidor)
@export var senha: String = "hestia2026"

var _http: HTTPRequest
var _robo: Node
var _status_label: Label
var _feedback: Label
var _banner: PanelContainer
var _ocupado: bool = false
var _conectado: bool = false

var _token: String = ""
var _pendentes: Array = []
var _tb: float = 0.0

# câmeras: 0=visão geral (fixa), 1=3ª pessoa (segue o robô), 2=1ª pessoa (olhos)
var _cam_geral: Camera3D
var _cam_robo: Camera3D
var _cam3: Camera3D
var _btn_cam: Button
var _modos: Array = ["Visão geral", "3ª pessoa", "1ª pessoa"]
var _modo: int = 0

func _ready() -> void:
	_robo = get_node_or_null("Robo")
	_status_label = get_node_or_null("HUD/Controles/VB/Status")
	_estilizar_hud()

	_http = HTTPRequest.new()
	add_child(_http)
	_http.request_completed.connect(_on_resposta)

	var t := Timer.new()
	t.wait_time = intervalo
	t.autostart = true
	add_child(t)
	t.timeout.connect(_poll)

	_ligar_botao("HUD/Controles/VB/BtnAgua", "agua", "PEDIDO_COMUM", 5.0, -1.9)
	_ligar_botao("HUD/Controles/VB/BtnQueda", "queda", "EMERGENCIA", -7.9, 11.45)
	_ligar_botao("HUD/Controles/VB/BtnSala", "ir_sala", "PEDIDO_COMUM", -7.9, -1.8)

	_setup_cameras()
	_autenticar()
	print("[Ponte] Interface Hestia iniciada. Lendo ", url_base, "/status")

# ---------------- visual do HUD (estilização por código) ----------------
func _sb(cor: Color, raio: int = 10, margem: float = 12.0) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = cor
	s.set_corner_radius_all(raio)
	s.set_content_margin_all(margem)
	return s

func _estilo_botao(caminho: String, cor: Color, cor_hover: Color) -> void:
	var b := get_node_or_null(caminho)
	if b != null:
		_estilo_botao_node(b, cor, cor_hover)

func _estilo_botao_node(b, cor: Color, cor_hover: Color) -> void:
	b.add_theme_stylebox_override("normal", _sb(cor, 10, 10.0))
	b.add_theme_stylebox_override("hover", _sb(cor_hover, 10, 10.0))
	b.add_theme_stylebox_override("pressed", _sb(cor.darkened(0.18), 10, 10.0))
	b.add_theme_stylebox_override("focus", _sb(cor, 10, 10.0))
	b.add_theme_color_override("font_color", Color(1, 1, 1))
	b.add_theme_color_override("font_hover_color", Color(1, 1, 1))
	b.add_theme_font_size_override("font_size", 16)

# ---------------- câmeras (visão geral / 3ª pessoa / 1ª pessoa) ----------------
func _setup_cameras() -> void:
	_cam_geral = get_node_or_null("CameraVisao")
	_cam_robo = get_node_or_null("Robo/CamRobo")
	if _robo:
		_cam3 = Camera3D.new()
		_cam3.name = "CamTerceira"
		_cam3.fov = 60.0
		_cam3.current = false
		_robo.add_child(_cam3)
	var vb := get_node_or_null("HUD/Controles/VB")
	if vb:
		_btn_cam = Button.new()
		_btn_cam.name = "BtnCamera"
		_btn_cam.custom_minimum_size = Vector2(0, 38)
		vb.add_child(_btn_cam)
		if _feedback:
			vb.move_child(_btn_cam, _feedback.get_index())  # botão antes do feedback
		_estilo_botao_node(_btn_cam, Color(0.20, 0.22, 0.28), Color(0.29, 0.32, 0.40))
		_btn_cam.pressed.connect(_ciclar_camera)
	_aplicar_modo()

func _ciclar_camera() -> void:
	_modo = (_modo + 1) % _modos.size()
	_aplicar_modo()

func _aplicar_modo() -> void:
	match _modo:
		1:
			if _cam3:
				_atualizar_cam3()
				_cam3.current = true
		2:
			if _cam_robo:
				_cam_robo.current = true
		_:
			if _cam_geral:
				_cam_geral.current = true
	if _btn_cam:
		_btn_cam.text = "🎥  Câmera: " + str(_modos[_modo])

func _atualizar_cam3() -> void:
	# posiciona a câmera atrás e acima do robô, olhando para ele (chase cam)
	if _cam3 == null or _robo == null:
		return
	var fwd: Vector3 = _robo.global_transform.basis.x.normalized()  # frente = +X local
	var alvo: Vector3 = _robo.global_position + Vector3(0, 0.4, 0)
	_cam3.global_position = alvo - fwd * 3.5 + Vector3(0, 2.2, 0)
	_cam3.look_at(alvo, Vector3.UP)

func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_C:
		_ciclar_camera()

func _estilizar_hud() -> void:
	# card do painel
	var card := get_node_or_null("HUD/Controles")
	if card:
		var s := _sb(Color(0.07, 0.08, 0.11, 0.92), 14, 16.0)
		s.set_border_width_all(1)
		s.border_color = Color(1, 1, 1, 0.12)
		s.shadow_color = Color(0, 0, 0, 0.45)
		s.shadow_size = 10
		card.add_theme_stylebox_override("panel", s)
	# título
	var titulo := get_node_or_null("HUD/Controles/VB/Titulo")
	if titulo:
		titulo.text = "HÉSTIA · Painel do cuidador"
		titulo.add_theme_color_override("font_color", Color(0.40, 0.75, 1.0))
		titulo.add_theme_font_size_override("font_size", 18)
	if _status_label:
		_status_label.add_theme_font_size_override("font_size", 14)
	# botões (água=azul, queda=vermelho, sala=ardósia)
	_estilo_botao("HUD/Controles/VB/BtnAgua", Color(0.12, 0.45, 0.80), Color(0.18, 0.55, 0.92))
	_estilo_botao("HUD/Controles/VB/BtnQueda", Color(0.80, 0.14, 0.12), Color(0.93, 0.21, 0.17))
	_estilo_botao("HUD/Controles/VB/BtnSala", Color(0.22, 0.24, 0.30), Color(0.31, 0.34, 0.42))
	# textos dos botões (mais limpos)
	_texto_botao("HUD/Controles/VB/BtnAgua", "💧   Pedir água — cozinha")
	_texto_botao("HUD/Controles/VB/BtnQueda", "🚨   EMERGÊNCIA — queda")
	_texto_botao("HUD/Controles/VB/BtnSala", "🛋   Chamar à sala")
	# painel da câmera
	var cam := get_node_or_null("HUD/CamPanel")
	if cam:
		var sc := _sb(Color(0.05, 0.06, 0.09, 0.92), 12, 6.0)
		sc.set_border_width_all(1)
		sc.border_color = Color(0.40, 0.75, 1.0, 0.5)
		cam.add_theme_stylebox_override("panel", sc)
	var camlbl := get_node_or_null("HUD/CamPanel/CamLabel")
	if camlbl:
		camlbl.add_theme_color_override("font_color", Color(0.72, 0.86, 1.0))
		camlbl.add_theme_font_size_override("font_size", 13)
	# label de confirmação de pedido
	var vb := get_node_or_null("HUD/Controles/VB")
	if vb:
		_feedback = Label.new()
		_feedback.name = "Feedback"
		_feedback.add_theme_font_size_override("font_size", 13)
		_feedback.add_theme_color_override("font_color", Color(0.55, 0.95, 0.70))
		vb.add_child(_feedback)
	# banner de emergência (barra no topo), criado por código
	var hud := get_node_or_null("HUD")
	if hud:
		_banner = PanelContainer.new()
		_banner.name = "BannerEmergencia"
		hud.add_child(_banner)
		_banner.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
		_banner.offset_bottom = 60
		_banner.visible = false
		_banner.add_theme_stylebox_override("panel", _sb(Color(0.82, 0.08, 0.06, 0.97), 0, 12.0))
		var lbl := Label.new()
		lbl.text = "⚠   EMERGÊNCIA — ATENDENDO QUEDA"
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		lbl.add_theme_color_override("font_color", Color(1, 1, 1))
		lbl.add_theme_font_size_override("font_size", 22)
		_banner.add_child(lbl)

func _texto_botao(caminho: String, txt: String) -> void:
	var b := get_node_or_null(caminho)
	if b:
		b.text = txt

func _process(delta: float) -> void:
	if _banner and _banner.visible:
		_tb += delta
		_banner.modulate.a = 0.75 + 0.25 * sin(_tb * 6.0)
	if _modo == 1:
		_atualizar_cam3()  # mantém a 3ª pessoa seguindo o robô

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
		var emerg := atv.to_lower().contains("queda") or atv.to_lower().contains("emerg")
		if _robo:
			_robo.definir_emergencia(emerg)
		if _banner:
			_banner.visible = emerg

func _set_status(texto: String) -> void:
	if _status_label == null:
		return
	_status_label.text = "Status: " + texto
	var t := texto.to_lower()
	var cor := Color(0.70, 0.80, 0.90)
	if t.contains("queda") or t.contains("emerg"):
		cor = Color(1.0, 0.40, 0.35)
	elif t.contains("agua") or t.contains("água") or t.contains("atendendo"):
		cor = Color(1.0, 0.80, 0.30)
	elif t.contains("ronda") or t.contains("patrul"):
		cor = Color(0.50, 0.85, 1.0)
	_status_label.add_theme_color_override("font_color", cor)

# ---------------- painel do cuidador: autenticação + pedidos ----------------
func _ligar_botao(caminho: String, tipo: String, prio: String, x: float, y: float) -> void:
	var b := get_node_or_null(caminho)
	if b and b is Button:
		b.pressed.connect(func(): _pedir(tipo, prio, x, y))

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
		_pendentes.append(pedido)
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
			_mostrar_feedback("✓ pedido enviado: " + str(pedido.get("tipo", "")))
		elif code == 401:
			print("[Ponte] token expirado — reautenticando.")
			_token = ""
			_pendentes.append(pedido)
			_autenticar()
		else:
			print("[Ponte] pedido recusado (code=", code, ")")
			_mostrar_feedback("✗ falha ao enviar pedido")
		req.queue_free()
	)
	var cabec := ["Content-Type: application/json", "Authorization: Bearer " + _token]
	req.request(url_base + "/pedido", cabec, HTTPClient.METHOD_POST, JSON.stringify(pedido))

func _mostrar_feedback(txt: String) -> void:
	if _feedback == null:
		return
	_feedback.text = txt
	# limpa a mensagem depois de alguns segundos
	var tmr := get_tree().create_timer(2.5)
	tmr.timeout.connect(func():
		if _feedback:
			_feedback.text = ""
	)
