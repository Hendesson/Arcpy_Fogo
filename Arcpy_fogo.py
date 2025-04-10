# Bibliotecas
import arcpy
import os
from arcgis.gis import GIS  # faz conexão com o arcgis online
import psycopg2
import geopandas as gpd
from datetime import datetime

# ARQUIVOS DE ENTRADA

ucs_path = r"Limites_UCs_2024.shp"


# FUNÇÕES

# Função retorna ano (string) a partir de data
def stryear(field):
    ano = field.year
    return ano


# Função para retornar o nome do mês abreviado a partir de uma data
def obter_mes(field):
    if field:
        return field.strftime("%b")  # Retorna o nome abreviado do mês
    return None


# Função para retornar o nome do mês a partir de uma data
def obter_num(field):
    if field:
        return field.strftime("%m")  # Retorna o numero de mes
    return None


# Função para reparar geometrias
def reparar_geometrias(arquivos):
    arcpy.RepairGeometry_management(arquivos)


# Função para realizar o Intersect e Erase
def intersect_e_erase(aaf_2024, limites_uc):
    intersect = r'memory\intersect'
    erase = r'memory\erase'

    # Realiza o Intersect entre AAF e Limites das UCs
    arcpy.analysis.Intersect([aaf_2024, limites_uc], intersect, output_type="INPUT")

    # Adiciona o campo 'local' no resultado do Intersect
    arcpy.management.AddField(intersect, "local", "TEXT", field_length=10)
    with arcpy.da.UpdateCursor(intersect, ["local"]) as cursor:
        for row in cursor:
            row[0] = "interior"
            cursor.updateRow(row)

    # Realiza o Erase: áreas fora das UCs
    arcpy.analysis.Erase(aaf_2024, limites_uc, erase)
    arcpy.management.AddField(erase, "local", "TEXT", field_length=10)
    with arcpy.da.UpdateCursor(erase, ["local"]) as cursor:
        for row in cursor:
            row[0] = "entorno"
            cursor.updateRow(row)

    return intersect, erase


# Função para calcular áreas
def calcular_geometria(intersect, erase):
    # Dentro das UCs
    arcpy.management.CalculateGeometryAttributes(intersect, [["area_uc", "AREA_GEODESIC"]], area_unit="HECTARES")

    # Fora das UCs
    arcpy.management.CalculateGeometryAttributes(erase, [["area_ent", "AREA_GEODESIC"]], area_unit="HECTARES")


# Função para mesclar resultados de intersect e Erase
def mesclar_camadas(intersect, erase):
    merge = r'memory\merge'
    arcpy.management.Merge([intersect, erase], merge)
    return merge


# Função para categorizar os valores de "classe" em "prevenção" ou "combate"
def categorizar_classe(classe):
    # prevenção
    prevencao_classes = ["queima controlada", "queima prescrita", "aceiro", "indigena"]

    # combate
    combate_classes = ["fogo natural", "incendio"]

    # Verificar a categoria com base no valor da classe
    if classe.lower() in [val.lower() for val in prevencao_classes]:
        return "prevenção"
    elif classe.lower() in [val.lower() for val in combate_classes]:
        return "combate"
    else:
        return None


# Função para deletar campos desnecessários
def deletar_campos(merge):
    campos_para_deletar = ['pk_aaf', 'data_img', 'BRIGADA', 'pk_ordem', 'UF', 'NUM_BRIG', 'Hectares', 'Grupo',
                           'CR_Nome', 'GR', 'Criacao', 'FID_Limites_UCs_2024', 'FID_copy_features_aaf']
    arcpy.management.DeleteField(merge, campos_para_deletar)


def calcular_area(merge):
    campo_para_calcular = ['area_ha']
    arcpy.management.CalculateGeometryAttributes(merge, [["area_ha", "AREA_GEODESIC"]], area_unit="HECTARES")


def valores_null(merge):
    campos_att = ["area_uc", "area_ent"]

    with arcpy.da.UpdateCursor(merge, campos_att) as cursor:
        for row in cursor:
            # None por 0
            for i in range(len(row)):
                if row[i] is None:
                    row[i] = 0
            cursor.updateRow(row)


# Função para deletar os campos nome_uc e cnuc do merge
# def deletar_campos_uc(merge):
#    campos_para_deletar = ['nome_uc', 'cnuc']
#    arcpy.management.DeleteField(merge, campos_para_deletar)

def criar_campos_uc(merge):
    #    # Adiciona os campos 'nome_uc' e 'cnuc' no merge
    #    arcpy.management.AddField(merge, "nome_uc", "TEXT", field_length=255)
    #    arcpy.management.AddField(merge, "cnuc", "TEXT", field_length=255)

    # Atualiza os campos 'nome_uc' e 'cnuc' com os valores de 'Nome_UC_1' e 'Cnuc_1'
    with arcpy.da.UpdateCursor(merge, ["Nome_UC_1", "Cnuc_1", "nome_uc", "cnuc", "local"]) as cursor:
        for row in cursor:
            if row[4] == 'interior':
                row[2] = row[0]  # Nome_UC_1 para nome_uc
                row[3] = row[1]  # Cnuc_1 para cnuc
                cursor.updateRow(row)


def deletar_campo(merge):
    deletar = ['Nome_UC_1', 'Cnuc_1']
    arcpy.management.DeleteField(merge, deletar)


# Função principal
def processar_geometria(aaf_2024, ucs_path):
    arquivos = {
        aaf_2024,
        ucs_path
    }

    # Repara geometrias
    reparar_geometrias(aaf_2024)

    # Realiza intersect e Erase
    intersect, erase = intersect_e_erase(aaf_2024, ucs_path)

    # Calcula geometria
    calcular_geometria(intersect, erase)

    # Mescla os resultados
    merge = mesclar_camadas(intersect, erase)

    # Calcular area_ha
    calcular_area(merge)

    # Substituir valores Null
    valores_null(merge)

    # Deleta campos desnecessários
    deletar_campos(merge)

    # Deleta os campos nome_uc e cnuc após o merge
    # deletar_campos_uc(merge)

    # Cria novamente os campos nome_uc e cnuc
    criar_campos_uc(merge)

    # Deleta os campos Cnuc_1 e Nome_UC_1
    deletar_campo(merge)

    print("Processamento completo.")
    return merge


# PRÉ-PROCESSAMENTO

# 1. CONECTA COM O BANCO DE DADOS DA DGEO, ACESSA CAMADA DE AAF E EXPORTA PARA SHP
# Conecta com o PostgreSQL e usa Geopandas para criar GeoDataFrame
con = psycopg2.connect(database="",
                       user="",
                       host='',
                       password="",
                       port=)

sql = "SELECT * FROM dmif_fogo.aaf_2024"
aaf_gdf = gpd.GeoDataFrame.from_postgis(sql, con, geom_col='geom')

# para passar os dados de GeoDataFrame pra .shp é preciso converter o campo de data para texto.
aaf_gdf['data_img'] = aaf_gdf['data_img'].astype(str)
aaf_gdf.to_file(
    r'aaf_2024.shp',
    driver='ESRI Shapefile')
aaf_2024 = r'aaf_2024.shp'

# 2. PROCESSAMENTO

# 2.1. MANIPULAÇÃO DE INFORMAÇÕES NA TABELA DE ATRIBUTOS

gdb_aaf_2024 = arcpy.management.CopyFeatures(aaf_2024, r'memory\copy_features_aaf')

# 2.1.1. CRIA CAMPO DE DATA E PREENCHE COM INFORMAÇÕES DO CAMPO DO DATA_IMG
arcpy.management.AddField(gdb_aaf_2024, "data", "DATE")
arcpy.management.CalculateField(gdb_aaf_2024, "data", "!data_img!")

# 2.1.2. CRIA CAMPO ANO E PREENCHE COM INFORMAÇÃO DO ANO A PARTIR DO CAMPO DE DATA
arcpy.management.AddField(gdb_aaf_2024, "ano", "INTEGER")

with arcpy.da.UpdateCursor(gdb_aaf_2024, ["data", "ano"]) as update_cur:
    for update_row in update_cur:
        update_row[1] = stryear(update_row[0])
        update_cur.updateRow(update_row)

# 2.1.3. CRIA CAMPO MÊS E PREENCHE COM INFORMAÇÃO DO MÊS ABREVIADO A PARTIR DO CAMPO DE DATA
# Adicionar o campo "mes" (para armazenar os nomes dos meses)
arcpy.management.AddField(gdb_aaf_2024, "mes_nome", "TEXT", field_length=20)

# Atualizar o campo "mes" com base na data
with arcpy.da.UpdateCursor(gdb_aaf_2024, ["data", "mes_nome"]) as update_cur:
    for update_row in update_cur:
        update_row[1] = obter_mes(update_row[0])  # Calcula o nome do mês
        update_cur.updateRow(update_row)

# 2.1.4. CRIA CAMPO MES_NUM E PREENCHE COM INFORMAÇÃO DO NÚMERO DO MÊS A PARTIR DO CAMPO DE DATA
# Adicionar o campo "mes_num" (para armazenar os nomes dos meses)
arcpy.management.AddField(gdb_aaf_2024, "mes_num", "TEXT", field_length=20)

# Atualizar o campo "mes_num" com base na data
with arcpy.da.UpdateCursor(gdb_aaf_2024, ["data", "mes_num"]) as update_cur:
    for update_row in update_cur:
        update_row[1] = obter_num(update_row[0])  # Calcula o nome do numero do mes
        update_cur.updateRow(update_row)

# 2.2. CRIAÇÃO DAS GEOMETRIAS RECORTADAS PARA O ENTORNO E INTERIOR DAS UCS E DEMAIS ATUALIZAÇÕES NA TABELA DE ATRIBUTOS


# 2.2.1. ADICIONA CAMPO "CATEGORIA" PARA POVOAR ESTA COLUNA COM AS SUBCLASSES "PREVENÇÃO" OU "COMBATE"
arcpy.management.AddField(gdb_aaf_2024, "categoria", "TEXT", field_length=20)

# Atualiza o campo "categoria" com base nos valores de "classe"
with arcpy.da.UpdateCursor(gdb_aaf_2024, ["classe", "categoria"]) as cursor:
    for row in cursor:
        row[1] = categorizar_classe(row[0])  # categorizar
        cursor.updateRow(row)

arquivo_final = processar_geometria(gdb_aaf_2024, ucs_path)

# 2.2.1. POVEIA O CAMPO "CNUC"

search_cur = dict([(key, val) for key, val in arcpy.da.SearchCursor(ucs_path, ["nome_uc", "cnuc"])])

with arcpy.da.UpdateCursor(arquivo_final, ["cnuc", "nome_uc"]) as update_cur:
    for update, key in update_cur:
        if not key in search_cur:
            continue
        row = (search_cur[key], key)
        update_cur.updateRow(row)

# bioma
search_cur = dict([(key, val) for key, val in arcpy.da.SearchCursor(ucs_path, ["nome_uc", "bioma"])])
with arcpy.da.UpdateCursor(arquivo_final, ["bioma", "nome_uc"]) as update_cur:
    for update, key in update_cur:
        if not key in search_cur:
            continue
        row = (search_cur[key], key)
        update_cur.updateRow(row)

# ngi
search_cur = dict([(key, val) for key, val in arcpy.da.SearchCursor(ucs_path, ["nome_uc", "ngi"])])

with arcpy.da.UpdateCursor(arquivo_final, ["ngi", "nome_uc"]) as update_cur:
    for update, key in update_cur:
        if not key in search_cur:
            continue
        row = (search_cur[key], key)
        update_cur.updateRow(row)

# gr_nome
search_cur = dict([(key, val) for key, val in arcpy.da.SearchCursor(ucs_path, ["nome_uc", "gr_nome"])])

with arcpy.da.UpdateCursor(arquivo_final, ["gr_nome", "nome_uc"]) as update_cur:
    for update, key in update_cur:
        if not key in search_cur:
            continue
        row = (search_cur[key], key)
        update_cur.updateRow(row)

# cr
search_cur = dict([(key, val) for key, val in arcpy.da.SearchCursor(ucs_path, ["nome_uc", "cr"])])

with arcpy.da.UpdateCursor(arquivo_final, ["cr", "nome_uc"]) as update_cur:
    for update, key in update_cur:
        if not key in search_cur:
            continue
        row = (search_cur[key], key)
        update_cur.updateRow(row)

# Sobescrever camada no ArcGIS Online

agol = r''

arcpy.management.TruncateTable(agol)
arcpy.management.Append(arquivo_final, agol, "NO_TEST")




