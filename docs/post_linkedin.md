# Post para o LinkedIn

> **Imagens sugeridas (carrossel):** `powerbi/previews/pagina1_visao_geral.png` → `reports/figures/02_gargalo_etapas.png` →
> `powerbi/previews/pagina2_ranking_templates.png` → `reports/figures/07_matriz_nicho_tipo.png`.
> Coloque o link do GitHub no primeiro comentário.

---

⏱️ Como reduzi em 30% o prazo de entrega de sites usando dados

Os sites atrasavam, e o motivo não era o desenvolvimento.

Ao analisar o histórico de projetos, encontrei o gargalo: **não havia critério para escolher o layout**.
Cada projeto começava com a mesma pergunta, "qual template usar?", e a resposta dependia da preferência de cada pessoa.
O resultado eram dias de escolha, várias rodadas de aprovação e retrabalho.

🔎 O que eu fiz:
• Consolidei o histórico de projetos com **SQL** em um banco centralizado (modelo estrela)
• Integrei os dados do **Google Analytics 4** por nicho, tipo de site e tipo de página
• Criei um score de desempenho para cada template: conversão comparada ao benchmark do nicho, prazo, retrabalho e entrega no prazo
• Construí **dashboards no Power BI** para ranquear e padronizar os **10 templates de maior desempenho**
• Montei uma matriz nicho × tipo de site e um fluxo documentado para a equipe

📊 Resultados:
✅ −30% no tempo médio de entrega (de 44,8 para 31,5 dias)
✅ +10% na taxa de conversão das páginas (de 2,0% para 2,2%)
✅ Entregas no prazo passaram de 26% para 69%
✅ Retrabalho de layout caiu 59%

💡 Aprendizado: o template mais bonito nem sempre é o melhor. Os templates mais leves e pensados para um nicho específico
entregaram mais rápido **e** converteram mais. E padronizar não engessou a criatividade: o tempo que ia para a escolha do layout passou a ir para a personalização.

Disponibilizei no GitHub uma versão do projeto com dados simulados: banco SQL, consultas, notebook em Python, medidas DAX e o layout do dashboard. Link nos comentários 👇

Qual critério você usa para escolher layouts na sua equipe?

#AnaliseDeDados #PowerBI #SQL #GoogleAnalytics #WordPress #DataAnalytics #Python #WebDesign #MelhoriaDeProcessos

---

## Comentário fixado
📂 Projeto completo: https://github.com/Proclise/selecao-templates-wordpress
Para rodar tudo: `python src/pipeline.py`

---

## Versão curta (para a seção "Projetos" ou "Experiência" do perfil)
Identifiquei um gargalo no prazo de entrega de sites causado pela falta de critérios na escolha de layouts. Consolidei e analisei
o histórico de projetos integrando dados via SQL e Google Analytics (nicho, tipo de página e conversão). Construí dashboards no
Power BI para ranquear e padronizar os 10 templates de maior desempenho, estruturando um banco de dados centralizado e um fluxo
documentado para a equipe. **Resultados:** redução de 30% no tempo médio de entrega e aumento de 10% na taxa de conversão (de 2% para 2,2%).
*Competências: SQL · Power BI · Google Analytics 4 · Python · Modelagem de dados · Melhoria de processos*
