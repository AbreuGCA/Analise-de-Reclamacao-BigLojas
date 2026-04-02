# 📊 BIG Lojas: Inteligência de Dados e Diagnóstico de Experiência do Cliente

---

## 🎯 Objetivos Estratégicos

O projeto foi dividido em duas frentes de investigação prioritárias para o negócio:

1. **Análise da Logística dos Produtos:** Mapeamento de gargalos desde o fornecimento até a entrega final, visando reduzir o churn por atrasos.
2. **Análise da Qualidade do Ambiente:** Diagnóstico da integridade das lojas (físicas e online) e avaliação do capital humano (atendimento e postura dos funcionários).

---

## 🏗️ Arquitetura do Projeto

O fluxo de dados segue uma linha de raciocínio de  **Data Storytelling** , partindo do dado bruto até a visualização executiva:

* **`BIGLojas_Analise.ipynb`** : Contém todo o processo de ETL, limpeza de dados e o uso de **Regex (Expressões Regulares)** para criar taxonomias de categorias que não existiam originalmente no dataset.
* **`BIGLOJAS_DADOS_TRATADOS_FINAL.csv`** : Base de dados higienizada, enriquecida com colunas temporais e geográficas prontas para consumo.
* **`dashboard_biglojas.py`** : Aplicação Web interativa desenvolvida em  **Streamlit** . O Dashboard conduz o gestor por um funil de análise (Macro -> Logística -> Ambiente).

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.x** : Linguagem base.
* **Pandas & Numpy** : Manipulação e tratamento de dados.
* **Plotly** : Gráficos dinâmicos e interativos.
* **Streamlit** : Framework para publicação do Dashboard em nuvem.
* **Regex** : Extração de padrões textuais para classificação de queixas.
* **NLP** : Processamento de Linguagem Natural voltada no português para melhorar o filtro do WorldCloud.
