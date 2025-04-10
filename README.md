# Processamento AAF 2024

Este repositório contém um script Python desenvolvido com **ArcPy**, **Geopandas** e **PostgreSQL** para o pré-processamento, análise espacial e atualização de dados de **Áreas Afetadas por Fogo (AAF)** no sistema do ICMBio.

## ⚙️ Funcionalidades

O script realiza as seguintes etapas principais:

1. **Conexão com o banco de dados PostgreSQL** para consulta da camada `dmif_fogo.aaf_2024`;
2. **Exportação da camada AAF para Shapefile** e carregamento em memória no ambiente ArcGIS;
3. **Criação e preenchimento de campos temporais**:
   - `data`: campo do tipo data
   - `ano`: extraído da data da imagem
   - `mes_nome`: nome abreviado do mês
   - `mes_num`: número do mês
4. **Classificação da variável `classe`** em:
   - `prevenção`: queima controlada, queima prescrita, aceiro, indígena
   - `combate`: fogo natural, incêndio
5. **Processamento geoespacial**:
   - Reparação de geometrias
   - Interseção (`Intersect`) e recorte (`Erase`) com os limites das Unidades de Conservação (UCs)
   - Cálculo de áreas dentro (`area_uc`) e fora (`area_ent`) das UCs
   - Criação de campo geral de área (`area_ha`)
   - Atualização de campos com valores nulos
6. **Tratamento da tabela de atributos**:
   - Deleção de campos desnecessários
   - Preenchimento dos campos `nome_uc` e `cnuc` com base nas geometrias resultantes
   - Inclusão de atributos complementares das UCs:
     - `bioma`
     - `cr`
     - `gr_nome`
     - `ngi`
7. **Publicação da camada final** no **ArcGIS Online**, via ferramentas `TruncateTable` e `Append`.

## 🛠 Requisitos

- **ArcGIS Pro** com licença válida:
  - Pacotes Spatial Analyst e Image Analyst
- **Python 3.x** com as seguintes bibliotecas:
  - `arcpy` (incluído com ArcGIS Pro)
  - `geopandas`
  - `psycopg2`
  - `datetime`

## 📝 Observações

- A conexão com o banco de dados PostgreSQL requer configuração com seus dados de acesso (`host`, `port`, `user`, `password`).
- O campo `classe` deve estar corretamente preenchido para garantir a categorização correta em **prevenção** ou **combate**.
- O script foi desenvolvido durante estágio no **ICMBio**, como parte do fluxo de atualização da base AAF.
- A automatização busca reduzir erros e agilizar o processo mensal de atualização dos dados no ArcGIS Online.
- Familiaridade com o ambiente ArcGIS e scripts em Python é recomendada para adaptar ou expandir este projeto.

## 📁 Estrutura esperada dos dados de entrada

- `aaf_2024.shp`: shapefile exportado da tabela `dmif_fogo.aaf_2024` do banco PostgreSQL
- `Limites_UCs_2024.shp`: shapefile com os limites atualizados das Unidades de Conservação (UCs)

## ✅ Resultado

A camada final processada é carregada automaticamente no **ArcGIS Online** conforme o item especificado na variável `agol`.


