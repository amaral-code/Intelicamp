# OmniBridge (azul-copilot)

Instruções rápidas para rodar o site localmente.

Pré-requisitos:
- Python 3.10+ (recomendado)
- git

Instalação (Linux/macOS):

```bash
cd azul-copilot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Rodando a aplicação:

```bash
# opção 1: usar o script de start (respeita $PORT)
cd azul-copilot
export PORT=5001
./start.sh

# opção 2: iniciar diretamente
cd azul-copilot
PORT=5001 python app.py
```

Testes:

```bash
cd azul-copilot
python -m unittest discover -s tests -v
```

Observações:
- O servidor de desenvolvimento do Flask detecta alterações e pode reiniciar em outra porta quando o debugger está ativo; verifique os logs para a porta efetiva.
- Se a porta desejada estiver em uso, mate o processo (ex.: `lsof -ti :5001 | xargs -r kill`) ou escolha outra porta.
