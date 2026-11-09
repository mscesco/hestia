# Interface Godot

Projeto Godot que renderiza a casa e o robô em 3D e reflete o estado
real vindo da ponte.

> Assets binários do Godot (`.glb`, texturas, `.tscn` com dados embutidos) e o
> cache `.godot/` NÃO ficam bem versionados soltos no Git. Use o `.gitignore` da
> raiz e, se o projeto crescer, Git LFS para os binários grandes.

## O que entra aqui (Semana 5)
- Cena com a casa modelada no Blender (exportada em glTF `.glb`) e importada no Godot.
- Robô como nó de cena cuja pose é atualizada lendo `GET /status` da ponte
  (via nó `HTTPRequest`, em polling, ou WebSocket).
- Câmera acoplada ao robô = visão "pelos olhos do robô" — implementada **dentro
  do Godot** como painel picture-in-picture (SubViewport), sem depender de stream
  HTTP. Ver seção abaixo.
- Ao menos um shader autoral (`.gdshader`) + iluminação em tempo real
  (evita a crítica de "2D disfarçada de 3D").
- Destaque visual no painel quando há chamado de emergência.

## Visão "pelos olhos do robô" (picture-in-picture)
Painel no canto superior direito da tela mostrando o que o robô "vê". Como
funciona na cena `Main.tscn`:

- `OlhoViewport` (`SubViewport`) renderiza o **mesmo mundo 3D** (não tem
  `own_world_3d`, então compartilha o World3D da cena) a partir da câmera
  `OlhoCam`.
- `OlhoCam` é dirigida por um `RemoteTransform3D` (`RemoteOlho`, filho de
  `Robo/CamRobo`): ele copia a transform global da `CamRobo` — que já está
  posicionada no robô — para a `OlhoCam`. Assim o painel segue o robô
  automaticamente, sem código, e **ajustar a `CamRobo` ajusta o painel junto**.
- `HUD/CamPanel/CamView` (`TextureRect`) exibe a textura do `OlhoViewport`.

Para validar: abra o projeto no Godot e rode a cena (F5). Se o painel aparecer
cinza, confira que `OlhoCam` está com `current = true` e que a `CamRobo` está
enquadrando a cena (se a direção parecer invertida, gire a `CamRobo` — o painel
acompanha).

## Fonte dos dados
Servidor-ponte em `http://<host>:8000` — ver ../ponte/README.md
