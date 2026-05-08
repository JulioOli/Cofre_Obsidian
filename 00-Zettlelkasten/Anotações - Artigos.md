---
tags:
  - note
---
04/05/2026 - 09:01

### ~={Titulo}Repurposing of abandoned oil and gas wells as geothermal power plants: A comprehensive sensitivity analysis and AI based performance prediction=~

→ Análise de Sensibilidade e previsão de performance baseada em IA

Autores: Yasin Ahmadpoor, Mozhdeh Sajjadi, Mohammad Emami Niri (Universidade de Teerã)  
Publicação: _Renewable Energy_ 253 (2025), artigo 123510 (Elsevier).

Aparentemente a energia geotérmica é uma fonte de energia renovável com um imenso potencial intocado, mas o alto custo inicial faz com que os projetos de desenvolvimento geot´rmico sejam viáveis só para reservas de alta temperatura.

> [!cite]
> 
Repur- posing of abandoned oil and gas wells as heat exchangers, relieves the drilling cost and presents a promising path for more affordable geothermal energy development.

>Nessa frase, o termo **"heat exchangers"** (trocadores de calor) refere-se à transformação do poço de petróleo em um sistema que coleta o calor natural do subsolo sem a necessidade de extrair grandes quantidades de fluido da terra.

~={blue}**Ideia central**=~: reaproveitar poços de petróleo e gás abandonados como trocadores de calor (sistema fechado, DBHE – _deep borehole heat exchanger_), em configuração coaxial de duplo tubo, com injeção no anular e retorno pelo tubo interno (configuração CXA). Assim se evita o custo de perfuração, que pesa muito em projetos geotérmicos.

~={green}**Método**=~: simulação numérica com OpenGeoSys (T-H em meio poroso, validada com o experimento de Beier et al.); análise de sensibilidade e ranking de variáveis (Pearson, regressão linear, XGBoost); dois cenários de “isolamento” do tubo interno (condutividade térmica baixa = bem isolado; alta = pouco isolado); depois machine learning (regressão linear, SVR, XGBoost, _stacking_ LR+XGBoost, PCA + SVR) para prever temperatura de saída (e, por corolário, potência e COP).

~={yellow}**Conclusões principais**=~: sem isolamento eficaz, a perda de calor no retorno reduz muito a potência (ex.: máx. ~1,6 MW vs ~0,6 MW no texto); com pouco isolamento, fluido de trabalho e parâmetros operacionais importam mais que os “[[screening factors]]” do reservatório; com bom isolamento, profundidade, vazão, gradiente geotérmico e temperatura de entrada sobem no ranking. O melhor modelo entre os testados foi SVR com PCA (R² ≈ 0,96, RMSE ≈ 1,88 °C na temperatura de saída).

>O custo de perfuração é uma limitação no desenvolvimento de sistemas geotérmicos por somar apoximadamente 50% do custo total de um projeto.

> [!info]
>A utilização desses poços abandonados para a produção de energia geotérmica não só reduziria os custos de perfuração, como também resolveria problemas de incrustação, corrosão e reinjeção. [(p. 2)](../02-Referencias/julio/Repurposing%20of%20abandoned%20oil%20and%20gas%20wells%20as%20geothermal%20power%20plants.pdf#page=2)



___

[[Organic Rankine Cycle (ORC)]]