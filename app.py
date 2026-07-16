import os
import importlib.util

# Carrega dinamicamente o módulo do app localizado em ./azul-copilot/app.py
module_path = os.path.join(os.path.dirname(__file__), "azul-copilot", "app.py")
spec = importlib.util.spec_from_file_location("azul_copilot_app", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Expõe a instância Flask como `app` para compatibilidade com os testes
app = getattr(module, "app")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Iniciando servidor em http://0.0.0.0:%s (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
