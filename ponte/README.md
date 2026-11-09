# Ponte (FastAPI)

Ponte HTTP entre o ROS 2 e o Godot. Também é o alvo do pentest.

## Rodar
```bash
pip install -r requirements.txt
uvicorn servidor:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints
- `GET  /status`  — o Godot lê pose + atividade daqui
- `POST /pose`    — o nó ROS atualiza a pose
- `POST /comando` — controle do robô (SEM auth até a Semana 6 — alvo do pentest)
- `/stream`       — vídeo da câmera (a definir)
