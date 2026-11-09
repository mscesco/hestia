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

## Paradigma 2 — Funcional

**Onde:** pipeline de processamento de leituras de sensor
(`hestia_robot/pipeline_sensores.py`).

**Por quê (justificativa técnica):** o tratamento de uma leitura de sensor é uma
**transformação de dados** — a leitura bruta entra, passa por uma sequência de
etapas (filtrar, normalizar, classificar) e vira uma decisão. Modelar isso como
uma **cadeia de funções puras** (sem efeito colateral, sem estado
compartilhado) torna cada etapa testável isoladamente e elimina bugs de estado
mutável compartilhado. É o oposto do caso do robô: aqui não há identidade a
preservar, só dados fluindo.

---

## Padrão de Projeto — Observer

**Onde:** comunicação por eventos entre os chamados e o gerenciador
(`hestia_robot/gerenciador_chamados.py`), sobre o modelo de tópicos do ROS 2.

**Por quê (justificativa técnica):** o Observer desacopla quem **produz** um
evento de quem **reage** a ele. O produtor não conhece os consumidores; os
consumidores se inscrevem e são notificados. O modelo **publish/subscribe** de
tópicos do ROS 2 é uma aplicação direta do Observer: o gerenciador de chamados
se inscreve no tópico de chamados e é notificado quando um novo chamado é
publicado, sem que o publicador saiba quem está ouvindo.

Isso significa que o padrão **emerge da arquitetura** — não foi adicionado
artificialmente para cumprir o requisito.

---

## Nota sobre a preempção (ligação Robótica <-> Arquitetura)

A lógica de prioridade não é um simples `if`. Quando um chamado de maior
prioridade chega durante o atendimento de outro, o gerenciador **cancela a meta
de navegação atual** (preempção via action client do Nav2) e envia a nova meta.
O Observer é o mecanismo que dispara essa decisão; a preempção é a consequência
no controle do robô.
