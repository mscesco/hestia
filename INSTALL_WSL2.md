# INSTALAÇÃO — ROS 2 Humble no Windows (via WSL2), do zero

Guia para quem nunca mexeu com isso. Leia na ordem. Cada bloco cinza é um
comando: cole no terminal e aperte Enter. Não pule etapas.

> **O que estamos montando e por quê.** O ROS 2 (o "cérebro" do robô do NEXUS)
> só roda bem no Linux (Ubuntu). Seu PC é Windows. O **WSL2** é um recurso do
> próprio Windows que roda um Ubuntu de verdade dentro dele, sem apagar seu
> Windows nem precisar de outro PC. É por isso que não usamos Docker: o WSL2 já
> te dá o Linux que o ROS precisa.

---

## ETAPA 1 — Instalar o Ubuntu 22.04 dentro do Windows (WSL2)

1. No Windows, abra o **PowerShell como Administrador** (clique com o botão
   direito no menu Iniciar → "Terminal (Admin)" ou "PowerShell (Admin)").

2. Instale o Ubuntu **22.04** (essa versão é obrigatória — o ROS Humble não vai
   com a 24.04):

   ```powershell
   wsl --install -d Ubuntu-22.04
   ```

3. Reinicie o PC se ele pedir. Ao abrir o Ubuntu pela primeira vez, ele pede
   para criar um **usuário e senha do Linux** (não é a senha do Windows —
   escolha uma e anote; a senha não aparece na tela enquanto você digita, isso
   é normal).

4. Confirme que é a versão certa. Dentro do terminal do Ubuntu:

   ```bash
   lsb_release -a
   ```

   Tem que aparecer **22.04** (Jammy). Se aparecer 24.04, pare e me avise —
   instalou a distro errada.

> **Sobre a tela do Gazebo:** o WSL2 no Windows 11 (e Windows 10 atualizado) já
> abre janelas gráficas do Linux sozinho (recurso chamado WSLg). Se mais adiante
> o Gazebo não abrir, tem uma dica de correção no fim deste guia.

---

## ETAPA 2 — Preparar o Ubuntu

Todos os comandos daqui em diante são **dentro do terminal do Ubuntu**.

1. Atualizar a lista de programas (o `apt` é o instalador de programas do
   Ubuntu, como uma "loja de apps" por linha de comando):

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

   `sudo` = "faça como administrador"; ele vai pedir a sua senha do Linux.

2. Configurar o idioma do sistema para UTF-8 (evita erros chatos depois):

   ```bash
   sudo apt install -y locales
   sudo locale-gen en_US en_US.UTF-8
   sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
   export LANG=en_US.UTF-8
   ```

3. Habilitar o repositório "universe" e instalar o `curl` (um baixador de
   arquivos que o próximo passo usa):

   ```bash
   sudo apt install -y software-properties-common curl
   sudo add-apt-repository universe -y
   ```

---

## ETAPA 3 — Adicionar o repositório do ROS 2 (método atual)

Isso ensina o Ubuntu ONDE baixar o ROS. Cole os três comandos:

```bash
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')

curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb
```

---

## ETAPA 4 — Instalar o ROS 2 Humble

```bash
sudo apt update
sudo apt install -y ros-humble-desktop ros-dev-tools
```

Esse download é grande (alguns GB) e demora. `ros-humble-desktop` já traz o
essencial, incluindo o RViz. Café enquanto baixa.

---

## ETAPA 5 — Fazer o ROS "ligar" sozinho em todo terminal

O ROS não fica ativo por padrão; é preciso "carregá-lo" (sourcing) a cada
terminal novo. Para não fazer isso toda vez, colocamos no arquivo de
inicialização do terminal (`.bashrc`):

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
```

A segunda linha define qual robô o simulador usa (o `burger` é o padrão dos
tutoriais). **Confirme com a sala qual modelo eles usam** e ajuste se preciso.

**Teste rápido de que o ROS está vivo** — abra DOIS terminais Ubuntu:

```bash
# terminal 1
ros2 run demo_nodes_cpp talker
```
```bash
# terminal 2
ros2 run demo_nodes_py listener
```

Se o terminal 1 fica "falando" e o 2 "ouvindo" (mensagens numeradas), o ROS 2
está instalado. `Ctrl+C` encerra cada um.

---

## ETAPA 6 — Instalar as peças do projeto NEXUS

Navegação (Nav2), mapeamento (SLAM), o robô simulado (TurtleBot3) e o
simulador (Gazebo):

```bash
sudo apt install -y \
  ros-humble-navigation2 \
  ros-humble-nav2-bringup \
  ros-humble-slam-toolbox \
  ros-humble-turtlebot3 \
  ros-humble-turtlebot3-simulations \
  nmap
```

> **Aviso honesto sobre o Gazebo:** existe mais de uma versão de Gazebo, e a
> "certa" depende de como as máquinas da sala estão montadas. O comando acima
> puxa o que o pacote do TurtleBot3 pede. Se o mundo não abrir igual ao da sala,
> **a sala manda** — confirme lá qual Gazebo usam e iguale.

---

## ETAPA 7 — Portão de saída da Semana 1

Este é o teste que fecha a semana. Abra o mundo "casa" com o robô:

```bash
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
```

Se abrir uma janela do Gazebo com uma casa e um robozinho dentro, **a Semana 1
está concluída.** (O nome exato do arquivo pode variar; digite
`ros2 launch turtlebot3_gazebo ` e aperte TAB duas vezes para ver as opções.)

Rode também o verificador automático que está no repositório:

```bash
bash verifica_ambiente.sh
```

---

## Se o Gazebo NÃO abrir (só no WSL2)

Às vezes o WSL2 tropeça na parte gráfica. Tente, na ordem:

1. Atualizar o WSL pelo PowerShell (Windows): `wsl --update`
2. Forçar renderização por software antes de abrir o Gazebo:
   ```bash
   echo "export LIBGL_ALWAYS_SOFTWARE=1" >> ~/.bashrc
   source ~/.bashrc
   ```
3. Se ainda assim travar, me mande a mensagem de erro exata do terminal.

---

## O que você precisa saber EXPLICAR (a prova é individual)

- O que é o ROS e por que ele precisa de Linux (por isso o WSL2).
- O que significa "sourcing" (`source ... setup.bash`) e por que está no
  `.bashrc`: sem isso, o comando `ros2` "não existe" no terminal.
- A diferença entre instalar por `apt` (pacote pronto) e a venv leve do Pygame
  das aulas — são dois ambientes diferentes, para dois propósitos diferentes.
