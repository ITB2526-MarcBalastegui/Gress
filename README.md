# Gress

Asistente personal proactivo y autoalojado. En lugar de esperar a que le pregunte,
Gress vigila fuentes de datos y me avisa por Telegram cuando pasa algo relevante.

## Estado
En desarrollo.

## Stack
- Python + python-telegram-bot
- Servidor: Oracle Cloud Always Free (ARM, Oracle Linux 9), pendiente de capacidad
- Memoria: SQLite (próximamente)
- IA: LLM local con Ollama (fase posterior)

## Hoja de ruta
- [x] Fase 0: repositorio y estructura
- [x] Fase 2: bot que responde solo a su dueño
- [ ] Fase 1: servidor en Oracle asegurado
- [ ] Fase 3: Google Calendar ("apunta que mañana...")
- [ ] Fase 4: recordatorios y memoria propia
- [ ] Fase 5: monitorización y alertas de seguridad
- [ ] Fase 6: LLM local y notas de voz

## Puesta en marcha
1. `python -m venv venv` y activar el entorno
2. `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env` y rellenar los valores
4. `python -m gress.bot`

## Seguridad
Ningún secreto se guarda en el repositorio. El bot ignora cualquier chat que no sea el de su dueño.