import os
import importlib.util

module_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
module_path = os.path.normpath(module_path)
spec = importlib.util.spec_from_file_location("azul_copilot_app", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = getattr(module, "app")
