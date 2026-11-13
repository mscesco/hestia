# Arquitetura — Paradigmas e Padrão de Projeto

Documento que justifica **tecnicamente** as escolhas de arquitetura do Héstia.
Cada integrante deve saber apontar, no código, onde cada item abaixo aparece.

---

## Visão geral do fluxo

```
[Gazebo/ROS 2]  ->  [nó ponte ROS]  ->  [servidor FastAPI]  ->  [Godot]
   percepção          publica pose         expõe /status         renderiza
   e navegação        e stream             e /stream             cena 3D
                                                 ^
                                          alvo do pentest
```

O robô percebe e navega (Robótica). O estado é exposto por uma ponte
(Arquitetura). A ponte alimenta a visualização (Computação Gráfica) e é o alvo
do teste de segurança (Pentest). As partes dependem umas das outras — não são
quatro projetos separados.

---

## Paradigma 1 — Orientação a Objetos (OOP)

**Onde:** modelagem dos componentes do robô (`hestia_robot/modelos.py`).

**Por quê (justificativa técnica):** os componentes do robô são entidades com
**identidade** e **estado mutável** ao longo do tempo — o robô tem uma posição
que muda, um nível de bateria que cai, um estado de operação (patrulhando /
atendendo). OOP é o paradigma adequado para modelar entidades com identidade e
estado interno que evolui, encapsulando esse estado atrás de métodos.

Exemplos de classes: `Robo`, `Sensor`, `Chamado`.

> **Onde roda (prova):** o `gerenciador_chamados` mantém uma instância de `Robo`
> e atualiza seu estado (`iniciar_atendimento`, `concluir_atendimento`,
> `EstadoRobo.PATRULHANDO`) a cada meta despachada/concluída. Não é classe
> ilustrativa: é usada no nó de controle.

## Paradigma 2 — Funcional

**Onde:** pipeline de processamento de leituras de sensor
(`hestia_robot/pipeline_sensores.py`), **executado** pelo nó
`hestia_robot/no_percepcao.py`.

**Por quê (justificativa técnica):** o tratamento de uma leitura de sensor é uma
**transformação de dados** — a leitura bruta entra, passa por uma sequência de
etapas (filtrar, normalizar, classificar) e vira uma decisão. Modelar isso como
uma **cadeia de funções puras** (sem efeito colateral, sem estado
compartilhado) torna cada etapa testável isoladamente e elimina bugs de estado
mutável compartilhado. É o oposto do caso do robô: aqui não há identidade a
preservar, só dados fluindo.

> **Onde roda (prova):** `no_percepcao` assina o `/scan` do LiDAR, passa cada
> varredura por `processar()` (a composição `filtrar_ruido -> normalizar ->
> detectar_obstaculo_proximo`) e publica o resultado em `/obstaculo_proximo`.
> Dá para demonstrar ao vivo: `ros2 topic echo /obstaculo_proximo` muda para
> `True` quando algo se aproxima do robô.

---

## Padrão de Projeto — Observer

**Onde:** duas camadas, uma reforçando a outra.

1. **Implementação autoral explícita** (`hestia_robot/observador.py`): classes
   `Sujeito` e `Observador` (GoF). O `gerenciador_chamados` é um `Sujeito`:
   quando a atividade do robô muda, chama `notificar(...)` e os observadores
   inscritos reagem — `LogAtividade` (registra no log) e `PublicadorAtividade`
   (publica em `/atividade_robo`). Adicionar uma reação (LED, métrica) = criar
   outro `Observador` e inscrevê-lo, **sem tocar no sujeito**.
2. **Aplicação na infraestrutura**: o modelo **publish/subscribe** de tópicos do
   ROS 2 é, ele próprio, uma aplicação do Observer — o `gerenciador` se inscreve
   em `/chamados` e é notificado sem o publicador saber quem ouve.

**Por quê (justificativa técnica):** o Observer desacopla quem **produz** um
evento de quem **reage** a ele. Ter a implementação autoral (camada 1) responde
à cobrança clássica "isso é só o ROS, não vocês aplicando o padrão": o padrão
está escrito no código do grupo, e o ROS confirma o mesmo princípio em escala.

---

## Nota sobre a preempção (ligação Robótica <-> Arquitetura)

A lógica de prioridade não é um simples `if`. Quando um chamado de maior
prioridade chega durante o atendimento de outro, o gerenciador **cancela a meta
de navegação atual** (preempção via action client do Nav2) e envia a nova meta.
O Observer é o mecanismo que dispara essa decisão; a preempção é a consequência
no controle do robô.
