#!/usr/bin/env python3
"""Screenshot tests for the 3 features."""

import os, sys, time, subprocess

OUTPUT_DIR = "/workspaces/Intelicamp/azul-copilot/screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Start HTTP server
server = subprocess.Popen(
    [sys.executable, "-m", "http.server", "5002"],
    cwd="/workspaces/Intelicamp/azul-copilot",
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(2)

from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"]
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(30000)

        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto("http://127.0.0.1:5002/index.html", wait_until="domcontentloaded")
        time.sleep(3)

        if errors:
            print("Page load errors:", errors[:3])
            browser.close()
            sys.exit(1)
        print("Page loaded - no console errors")

        # Navigate to project view
        page.evaluate("abrirProjeto()")
        time.sleep(1)

        # =========================================================
        # SCREENSHOT 1: Analysis with cultural feedback
        # =========================================================
        page.evaluate('document.getElementById("buSelect").value = "Operacoes"')
        page.evaluate(
            'document.getElementById("ideaInput").value = '
            '"Cortar os onibus intermunicipais de conexao em Viracopos como medida de reducao de custos"'
        )
        page.evaluate("enviarAnalise()")

        time.sleep(3)
        page.wait_for_selector(".analysis-result.active", timeout=10000)
        time.sleep(1)

        if errors:
            print("Errors after analysis:", errors[:3])

        page.screenshot(path=os.path.join(OUTPUT_DIR, "01-analise-com-feedback-cultural.png"), full_page=True)
        print("Screenshot 1: Analysis with cultural feedback")

        # =========================================================
        # SCREENSHOT 2: Task drawer with chat
        # =========================================================
        page.evaluate("openDrawer(lastAnalysisId)")
        time.sleep(1)
        page.wait_for_selector("#taskDrawer.active", timeout=5000)
        time.sleep(0.5)

        # Send messages
        page.evaluate("""
            document.getElementById('chatInput').value = 'Precisamos revisar os impactos desta decisao com urgencia.';
            sendChatMessage();
        """)
        time.sleep(0.3)

        # Add participant
        page.evaluate("""
            document.getElementById('participantSelect').value = 'p2';
            addParticipantToTask();
        """)
        time.sleep(0.3)

        page.evaluate("""
            document.getElementById('chatInput').value = 'Vou preparar uma contraproposta alinhada aos pilares de marca.';
            sendChatMessage();
        """)
        time.sleep(0.3)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "02-drawer-com-chat.png"), full_page=True)
        print("Screenshot 2: Task drawer with chat")

        # =========================================================
        # SCREENSHOT 3: Second validation
        # =========================================================
        page.evaluate("closeDrawer()")
        time.sleep(0.5)

        # New low-risk analysis
        page.evaluate("novaAnalise()")
        time.sleep(0.5)
        page.evaluate('document.getElementById("buSelect").value = "Marketing"')
        page.evaluate(
            'document.getElementById("ideaInput").value = '
            '"Campanha nacional destacando a brasilidade e capilaridade da Azul em todas as regioes"'
        )
        page.evaluate("enviarAnalise()")
        time.sleep(3)
        page.wait_for_selector(".analysis-result.active", timeout=10000)
        time.sleep(1)

        # Open drawer and force status to aprovada
        page.evaluate("openDrawer(lastAnalysisId)")
        time.sleep(1)
        page.evaluate("""
            var a = analyses.find(function(x) { return x.id === lastAnalysisId; });
            if (a) {
                a.status = 'aprovada';
                renderDrawer(lastAnalysisId);
            }
        """)
        time.sleep(1)

        sv = page.query_selector("#secondValSection")
        print("Second val section visible:", sv is not None and sv.is_visible())

        page.screenshot(path=os.path.join(OUTPUT_DIR, "03-segunda-validacao.png"), full_page=True)
        print("Screenshot 3: Second validation view")

        # Run second validation
        page.evaluate("runSecondValidation()")
        time.sleep(3)

        page.screenshot(path=os.path.join(OUTPUT_DIR, "04-segunda-validacao-concluida.png"), full_page=True)
        print("Screenshot 4: Second validation result")

        if errors:
            print("\nConsole errors during session:", errors)
        else:
            print("\nNo console errors during entire session!")

        browser.close()

finally:
    server.terminate()
    server.wait()
