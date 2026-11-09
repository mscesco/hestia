# Ambiente pronto — o que foi instalado e como rodar (Windows 11)

> Este arquivo documenta o ambiente que **foi montado e testado** nesta máquina
> (Windows 11 + WSL2). Onde o processo divergiu de `INSTALL_WSL2.md` / `SETUP.md`,
> está anotado em **Diferenças** no fim. As três camadas (ponte, ROS, Godot)
> foram validadas de ponta a ponta.

## Estado verificado

| Camada | Como está | Verificação feita |
|---|---|---|
| **Ponte FastAPI** | roda no Windows, venv em `ponte/.venv` | `GET /status`, `POST /pose`, `POST /token` respondem |
| **Godot 4.7.2** | instalado (winget) + projeto criado em `interface_godot/` | cena abre e conecta na ponte (`[Ponte] conectado.`) |
| **ROS 2 Humble** | WSL2, distro `Ubuntu-22.04`, usuário `lauri` | 398 pacotes; nav2/slam/amcl/turtlebot3/gazebo OK |
| **Workspace `hestia_robot`** | buildado com `colcon` | `ros2 run hestia_robot gerenciador_chamados` e `no_ponte` resolvem |

Caminhos úteis:
- Godot: `C:\Users\lauri\AppData\Local\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_win64.exe` (ou só `godot` num terminal novo).
- WSL vê o projeto em `/mnt/c/Users/lauri/Downloads/hestia`.

---

## Como rodar

### 1. Ponte (FastAPI) — terminal PowerShell no Windows
```powershell
cd C:\Users\lauri\Downloads\hestia\ponte
.\.venv\Scripts\python.exe -m uvicorn servidor:app --host 127.0.0.1 --port 8000
# testar: Invoke-RestMethod http://127.0.0.1:8000/status
```

### 2. Interface Godot — Windows
```powershell
# abrir no editor:
godot --path C:\Users\lauri\Downloads\hestia\interface_godot -e
# ou só rodar a cena (precisa da ponte do passo 1 no ar):
godot --path C:\Users\lauri\Downloads\hestia\interface_godot
```
O robô (cápsula azul) lê `GET /status` em polling e se move conforme a pose.
Parâmetros de alinhamento (escala, offset, inverter_z, offset_theta) estão
expostos no nó **Robo** do inspector — ajuste para casar a pose do ROS com a
sua casa. O shader do robô pulsa em vermelho quando a atividade contém
"queda"/"emergência".

### 3. ROS 2 — terminais no WSL (`wsl` ou "Ubuntu 22.04" no menu Iniciar)
```bash
# cada terminal novo ja carrega o ROS (esta no ~/.bashrc). Para usar o pacote:
cd /mnt/c/Users/lauri/Downloads/hestia/ros2_ws
source install/setup.bash

# robotica (Gazebo + Nav2 + AMCL + RViz) — da a pose inicial no RViz (2D Pose Estimate):
ros2 launch hestia_robot localizacao.launch.py

# chamados + preempcao (outro terminal):
ros2 run hestia_robot gerenciador_chamados

# ponte ROS->FastAPI (outro terminal, com a ponte do passo 1 no ar):
ros2 run hestia_robot no_ponte
```

> O workspace foi buildado em `/mnt/c/...` (disco do Windows). Funciona, mas é
> mais lento que no disco do Linux. Se quiser velocidade, copie `ros2_ws` para
> `~/` dentro do WSL e builde lá.

---

## Diferenças em relação aos guias originais (o que mudou e por quê)

1. **WSL instalado de forma não-interativa.** Em vez de `wsl --install -d Ubuntu-22.04`
   (que abre a tela de criar usuário), usei `wsl --install -d Ubuntu-22.04 --no-launch`,
   instalei o ROS como `root` e criei o usuário `lauri` por script. A distro já
   existente `docker-desktop` foi mantida intacta.
   - Usuário Linux: **`lauri`** / senha provisória **`hestia`** → troque com `passwd`.

2. **`uvicorn[standard]` falha no Python 3.15.** O extra `[standard]` puxa `pyyaml`,
   que ainda não tem wheel para o 3.15 e tenta compilar (exige MSVC). Solução:
   instalar **`uvicorn`** puro. O servidor roda igual (sem `--reload`, que
   dependeria do `watchfiles` do extra). Ver `ponte/requirements.txt`.

3. **`python-jose` não é necessário.** O `servidor.py` implementa o JWT HS256 na
   mão (hmac/hashlib/base64), então a ponte sobe sem `python-jose`/`cryptography`.

4. **Faltava `setup.cfg` no pacote ROS.** Sem ele, o `colcon build` com setuptools
   novo instala os executáveis em `install/.../bin/` em vez de
   `install/.../lib/hestia_robot/`, e o `ros2 run` não os acha. Foi adicionado
   `ros2_ws/src/hestia_robot/setup.cfg` com `script_dir`/`install_scripts`.

5. **Projeto Godot criado (não existia).** O `.blend` (`ExpoProjectHouse.blend`,
   só a casa — sem robô) foi exportado para `interface_godot/models/casa.glb` e o
   projeto Godot foi montado com a casa, luz em tempo real, câmera de visão geral,
   câmera "pelos olhos do robô" e o robô como nó movido pela ponte, com shader
   autoral (`shaders/robo.gdshader`).
