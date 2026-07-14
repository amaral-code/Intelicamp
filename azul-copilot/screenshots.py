#!/usr/bin/env python3
"""Playwright screenshot script for all 3 features."""

import os, time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "/workspaces/Intelicamp/azul-copilot/screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(15000)

        # Navigate
        page.goto("http://127.0.0.1:5002/index.html", wait_until="networkidle")
        time.sleep(1)

        # Click "Iniciar Analise" to open project view
        page.click("text=Iniciar Analise", timeout=5000)
        time.sleep(1)

        # =========================================================
        # SCREENSHOT 1: Analysis result with cultural feedback
        # =========================================================
        # Select BU "Operacoes" and type an idea that triggers reproval
        page.select_option("#buSelect", "Operacoes")
        page.fill("#ideaInput", "Cortar os onibus intermunicipais de conexao em Viracopos como medida de reducao de custos impactando diretamente a conectividade ponta-a-ponta")
        time.sleep(0.5)

        # Click "Analisar com IA" button
        page.click("text=Analisar com IA", timeout=5000)

        # Wait for analysis result to appear (the loading takes 1.8s)
        page.wait_for_selector(".analysis-result.active", timeout=10000)
        time.sleep(1)

        # Take screenshot showing cultural feedback
        page.screenshot(path=os.path.join(OUTPUT_DIR, "01-analise-com-feedback-cultural.png"), full_page=True)

        # =========================================================
        # SCREENSHOT 2: Task drawer with chat
        # =========================================================
        # Click "Ver Tarefa & Chat" button
        page.click("text=Ver Tarefa", timeout=5000)
        time.sleep(1)

        # Wait for drawer to open
        page.wait_for_selector("#taskDrawer.active", timeout=5000)
        time.sleep(0.5)

        # Send a chat message
        page.fill("#chatInput", "Precisamos revisar os impactos desta decisao com urgencia.")
        page.click("text=Enviar", timeout=3000)
        time.sleep(0.5)

        # Add a participant
        page.select_option("#participantSelect", "p2")
        page.click("text=Adicionar", timeout=3000)
        time.sleep(0.5)

        # Send another message
        page.fill("#chatInput", "Vou preparar uma contraproposta alinhada aos pilares de marca.")
        page.click("text=Enviar", timeout=3000)
        time.sleep(0.5)

        # Take screenshot of drawer with chat
        page.screenshot(path=os.path.join(OUTPUT_DIR, "02-drawer-com-chat.png"), full_page=True)

        # =========================================================
        # SCREENSHOT 3: Second validation view
        # =========================================================
        # Close drawer
        page.click(".drawer-close", timeout=3000)
        time.sleep(0.5)

        # Click "Nova Analise" to clear form
        page.click("text=Nova Analise", timeout=3000)
        time.sleep(0.5)

        # Submit an idea that will be approved (low risk)
        page.select_option("#buSelect", "Marketing")
        page.fill("#ideaInput", "Campanha nacional destacando a brasilidade e capilaridade da Azul em todas as regioes do Brasil para fortalecer o posicionamento de marca")
        time.sleep(0.5)

        page.click("text=Analisar com IA", timeout=5000)
        page.wait_for_selector(".analysis-result.active", timeout=10000)
        time.sleep(1)

        # The result should be green (aprovado) - click "Ver Tarefa & Chat"
        page.click("text=Ver Tarefa", timeout=5000)
        page.wait_for_selector("#taskDrawer.active", timeout=5000)
        time.sleep(0.5)

        # Now we need to change the status to "aprovada" to see the second validation
        # Since the mock analysis sets status to "em_validacao", we need to manipulate via JS
        page.evaluate("""
            const a = analyses.find(x => x.id === lastAnalysisId);
            if (a) {
                a.status = 'aprovada';
                renderDrawer(lastAnalysisId);
            }
        """)
        time.sleep(0.5)

        # The second validation section should now be visible
        page.wait_for_selector("#secondValSection", state="visible", timeout=5000)
        time.sleep(0.5)

        # Take screenshot showing second validation
        page.screenshot(path=os.path.join(OUTPUT_DIR, "03-segunda-validacao.png"), full_page=True)

        # =========================================================
        # SCREENSHOT 4: After running second validation (approved)
        # =========================================================
        # Click "Executar Segunda Validacao"
        page.click("text=Executar Segunda Validacao", timeout=5000)
        time.sleep(3)  # Wait for the 2s mock delay

        # Take screenshot showing the result
        page.screenshot(path=os.path.join(OUTPUT_DIR, "04-segunda-validacao-concluida.png"), full_page=True)

        browser.close()
        print(f"Screenshots saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    run()
