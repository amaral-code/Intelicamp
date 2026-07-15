# Plano de Correção — Intelicamp / OmniBridge

## Arquivos a modificar

1. `azul-copilot/app.py`
2. `azul-copilot/index.html`
3. `azul-copilot/build_html.py`
4. `azul-copilot/tests/test_app.py`

---

## 1. `app.py` — Backend

### 1.1 Substituir `analyze_with_llm` por `mentor_project` (API 1)

Nova função que implementa o "Mentor de Inovação e Marca":

```python
def mentor_project(bu_name: str, project_idea: str) -> dict:
    # Análise de risco baseada em palavras-chave expandida
    # Retorna estrutura padronizada da API 1:
    # - titulo_projeto
    # - unidade_negocio
    # - objetivo_executivo
    # - aderencia_marca_azul
    # - publico_alvo_impacto
    # - recursos_necessarios
    # - mentoria: { veredito, risco, justificativa, sugestao, precedentes_historicos }
```

### 1.2 Adicionar endpoint `POST /api/mentor`

Roteia para `mentor_project`. Substitui `/api/analyze` e `/api/brand-check`.

### 1.3 Adicionar `calculate_brand_strength(project)` (API 2)

```python
def calculate_brand_strength(project: dict) -> dict:
    # Calcula pontuação 0-100 baseada em:
    # - Penalidades: conectividade (-25), atendimento (-20)
    # - Bônus: brasilidade (+10), inovação (+5)
    # Retorna: { pontuacao, nivel, descricao, criterios }
```

### 1.4 Adicionar `generate_verdict(project, brand_strength, similarity)` (API 2)

```python
def generate_verdict(project, brand_strength, similarity) -> dict:
    # Score >= 80 e sem similar → "Investimento Prioritário"
    # Score >= 50 com similar > 50% → "Aprovação Condicional" (fusão)
    # Score >= 50 → "Aprovação Condicional"
    # Score < 50 → "Banco de Ideias"
    # Retorna: { classificacao, plano_acao, score_brand_strength }
```

### 1.5 Adicionar endpoint `POST /api/analyst`

Recebe project_id, calcula brand_strength + similarity + verdict. Retorna relatório executivo.

### 1.6 Adicionar query params no `GET /api/projects`

- `sort`: `date_desc` (padrão), `date_asc`, `importance_desc`, `importance_asc`
- `person`: filtrar por `ownerRole`

### 1.7 Correções adicionais

- Remover `"system_prompt"` do response do endpoint `/api/analyze`
- Melhorar `find_similar_projects` com limiar de 50% para alertas (conforme especificação API 2)

---

## 2. `index.html` — Frontend

### 2.1 Simplificar botões de login

**Landing page:**
- Substituir "PROJETO" + "Entrar" por um único botão "Acessar →"
- Botão "Acessar" mostra a tela de login

**Tela de login:**
- Remover botão "Entrar como demo" (linha 302)
- Manter apenas "Entrar"
- O formulário já vem pré-preenchido com "Carla Nogueira", "Gerente", "Azul Viagens", "Marketing"

### 2.2 Adicionar filtros na busca de projetos

No painel "Busca e filtros" (linhas 417-434), adicionar:

```html
<div class="field">
  <label>Ordenar por data</label>
  <select id="filterDate">
    <option value="date_desc">Mais recente</option>
    <option value="date_asc">Mais antigo</option>
  </select>
</div>
<div class="field">
  <label>Importância</label>
  <select id="filterImportance">
    <option value="">Todas</option>
    <option value="alta">Alta similaridade (>70%)</option>
    <option value="media">Média similaridade (35-70%)</option>
    <option value="baixa">Baixa similaridade (<35%)</option>
  </select>
</div>
<div class="field">
  <label>Responsável</label>
  <select id="filterPerson">
    <option value="">Todos</option>
    <!-- Populado dinamicamente via JS -->
  </select>
</div>
```

**JS:** Atualizar `renderProjects()` para aplicar os novos filtros:
- Ordenar por `createdAt` conforme `filterDate`
- Filtrar por `similarityScore` conforme `filterImportance`
- Filtrar por `ownerRole` conforme `filterPerson`
- Popular `filterPerson` com valores únicos de `ownerRole` dos projetos

### 2.3 Melhorar CSS responsivo e botões interativos

Adicionar/atualizar no `<style>`:

```css
/* Botões mais responsivos */
.btn {
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
  touch-action: manipulation;
  user-select: none;
}
.btn:hover { transform: scale(1.03); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.btn:active { transform: scale(0.97); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

/* Melhorias responsivas */
@media (max-width: 640px) {
  .landing-actions-overlay {
    position: static;
    justify-content: center;
    padding: 20px;
  }
  .landing-hero img { display: none; }
  .landing-hero { min-height: 300px; background: #0a1a3d; }
  .login-panel { padding: 20px; }
  .hero-panel .hero-visual-stack { display: none; }
  .hero-panel { grid-template-columns: 1fr; }
  .project-grid { grid-template-columns: 1fr; }
  .grid-2 { grid-template-columns: 1fr; }
  .content { grid-template-columns: 1fr; }
  .sidebar { flex-direction: row; flex-wrap: wrap; padding: 12px; }
  .topbar { flex-direction: column; gap: 8px; padding: 12px; }
  .topbar-left { flex-direction: column; text-align: center; }
  .btn { min-height: 44px; } /* touch target */
}

@media (max-width: 480px) {
  .login-copy { padding: 32px 20px; }
  .main { padding: 12px; }
  .panel { padding: 14px; }
  .landing-actions-overlay .btn { font-size: 14px; padding: 12px 20px; }
}
```

### 2.4 Corrigir exibição do role nos comentários

No template do modal (linha ~768-773), adicionar exibição do cargo:

```javascript
commentList.innerHTML = (project.comments || []).map(c => `
  <div class="comment-card">
    <div class="author">${c.author}</div>
    <div class="role">${c.role}</div>
    <div class="text">${c.text}</div>
  </div>
`).join('');
```

(O código já está correto, verificar se `comment.role` está sendo enviado pelo backend)

### 2.5 Event listeners dos novos filtros

```javascript
document.getElementById('filterDate').addEventListener('change', renderProjects);
document.getElementById('filterImportance').addEventListener('change', renderProjects);
document.getElementById('filterPerson').addEventListener('change', renderProjects);
```

---

## 3. `build_html.py` — Remover stub vazio

Substituir conteúdo por:

```python
#!/usr/bin/env python3
# Este arquivo não é mais necessário - o HTML é servido diretamente pelo Flask.
```

Ou simplesmente remover o arquivo.

---

## 4. `test_app.py` — Corrigir índice no teste

Linha 92: `project_id = self.client.get('/api/projects').get_json()['projects'][3]['id']`

Como a lista `PROJECTS` tem 2 itens iniciais, o índice 3 causa `IndexError`. Corrigir para:

```python
projects = self.client.get('/api/projects').get_json()['projects']
# Criar um novo projeto para ter mais itens
self.client.post('/api/projects', json={
    'title': 'Projeto de teste',
    'summary': 'Resumo de teste para votação',
    'organization': 'Azul Conecta',
    'areas': ['TI'],
    'ownerRole': 'Gerente',
})
project_id = self.client.get('/api/projects').get_json()['projects'][0]['id']
```

---

## 5. Ordem de execução

1. `app.py` — todas as mudanças backend
2. `index.html` — todas as mudanças frontend
3. `build_html.py` — remover stub
4. `test_app.py` — corrigir teste
5. Rodar testes e verificar
