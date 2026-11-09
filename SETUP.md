# SETUP do Ambiente — Héstia

> Princípio nº 1: **o ambiente da sala é a fonte da verdade.** A avaliação
> acontece lá. Reproduza em casa o que roda na sala, não o contrário.
> Ambiente-alvo: **Ubuntu 22.04 + ROS 2 Humble** (nativo ou WSL2).

---

## 0. Capturar o ambiente da sala (fazer isto ANTES de montar em casa)

Rode numa máquina da sala que já funciona e **commite as saídas** no repo:

```bash
lsb_release -a
printenv | grep -i ros
ros2 doctor --report > ambiente_sala.txt
dpkg -l 'ros-humble-*' > apt_ros_sala.txt
# dentro da venv da sala:
pip freeze > requirements_sala.txt
```

Se a lista de pacotes da sala divergir do passo 1 abaixo, **a sala manda**.

---

## 1. Pacotes do sistema (APT) — o núcleo do ROS

Estes NÃO são pip. É aqui que mora o inferno de dependência que o Docker
resolveria; sem Docker, a disciplina de reproduzir esta lista é o que garante
paridade entre casa e sala.

```bash
sudo apt update
sudo apt install -y \
  ros-humble-desktop \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-turtlebot3 \
  ros-humble-turtlebot3-simulations \
  python3-colcon-common-extensions \
  python3-rosdep \
  nmap
```

> `ros-humble-turtlebot3-simulations` puxa o Gazebo e os mundos como
> dependência. **Confirme qual Gazebo a sala usa** (Classic vs mais novo) e
> iguale — se divergir, o `turtlebot3_house` pode não abrir igual.

## 2. Variáveis de ambiente

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc   # confirme o modelo usado na sala
source ~/.bashrc
```

## 3. rosdep (uma vez por máquina)

```bash
sudo rosdep init      # só na primeira vez da máquina; ignore se já inicializado
rosdep update
```

## 4. venv — a pegadinha que quebra tudo

`rclpy` vem do apt (Python do sistema), NÃO do pip. Uma venv isolada não
enxerga o `rclpy` e o `import rclpy` falha. Por isso, para rodar nós ROS de
dentro de uma venv, ela PRECISA ver os pacotes do sistema:

```bash
cd hestia
python3 -m venv --system-site-packages .venv    # <-- a flag é obrigatória p/ ROS
source .venv/bin/activate
pip install -r requirements.txt
```

> Se a venv da sala NÃO tem `--system-site-packages`, então lá vocês
> provavelmente rodam os nós ROS fora da venv (usando o Python do sistema) e
> usam a venv só para a ponte. Descubra qual é o caso e padronize no grupo.
>
> Alternativa mais limpa para a **ponte**: como o FastAPI não precisa de ROS,
> a ponte pode viver numa venv separada e comum (sem a flag), isolada do ROS.

## 5. Build do workspace ROS

```bash
cd hestia/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

> O pacote precisa de `src/hestia_robot/setup.cfg` (com `script_dir` /
> `install_scripts` apontando para `lib/hestia_robot`). Sem ele, o setuptools
> novo instala os executáveis em `bin/` e o `ros2 run hestia_robot ...` não os
> encontra. Esse arquivo já está no repo.

## 6. Verificação (o ambiente está OK se tudo isto passar)

```bash
ros2 doctor                          # sem erros graves
ros2 pkg list | grep nav2            # lista pacotes nav2
ros2 pkg list | grep slam_toolbox    # aparece
# abre o Gazebo com a casa (confirme o nome exato do launch com TAB):
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
```

Se o Gazebo abrir a casa e o robô, o ambiente da Semana 1 está fechado.

---

## Padronização do grupo (escrever e todos seguirem)

- Distro: **ROS 2 Humble**. Ninguém usa Foxy/Jazzy.
- SO: Ubuntu 22.04 nativo OU WSL2 com Ubuntu 22.04.
- Ambiente reproduzido a partir de `apt_ros_sala.txt` + `requirements.txt`.
- venv: definir se é `--system-site-packages` (para ROS) e registrar aqui.
