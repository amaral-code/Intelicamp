import os
import importlib.util

# Carrega dinamicamente o módulo do app localizado em ./azul-copilot/app.py
module_path = os.path.join(os.path.dirname(__file__), "azul-copilot", "app.py")
spec = importlib.util.spec_from_file_location("azul_copilot_app", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Expõe a instância Flask como `app` para compatibilidade com os testes
app = getattr(module, "app")
