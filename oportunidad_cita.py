# -*- coding: utf-8 -*-
"""
Oportunidad Cita

Este script procesa los reportes de DGH "fecha_cita.xlsx", "oportunidad_fecha_citaBD.xlsx" y el archivo de internet "Variables.xlsx" para generar los siguientes resultados:
1. Cruce - Oportunidad_cita.xlsx
2. Vacíos de fecha - FechaVacias.xlsx
3. Vacíos de oportunidad - Oportunidad_citaVacias.xlsx
4. Errores en tipo cita - Oportunidad_citaTipoCitaError.xlsx
5. Pivotes resultante - Consulta_pivote.xlsx

Pasos del proceso:
1. Carga de archivos.
2. Procesamiento de datos.
3. Generación de pivotes.
4. Descarga de archivos resultantes.
"""
# %% Cargar archivos

# Cargar librerias
import pandas as pd
import numpy as np
import requests
import duckdb
import os

print('Cargando archivos...')
# Conectar a DuckDB y cargar los xlsx a df
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")

# Función descargaExcel para descargar los excel compartidos en OneDrive 365
def descargaExcel(url):
    """
    Descarga un archivo Excel desde una URL de OneDrive 365 y lo carga en un DataFrame.
    
    Args:
    - url (str): URL del archivo Excel en OneDrive 365.
    
    Returns:
    - df (DataFrame): DataFrame con los datos del archivo Excel descargado.
    """

    # Reemplazar la parte después del ? con download=1
    url = url.split('?')[0] + '?download=1'

    # Descargar el Excel
    data = requests.get(url)

    # Verificar si la descarga fue exitosa
    if data.status_code == 200:
        # Guardar el contenido en un archivo temporal
        with open("temp.xlsx", "wb") as file:
            file.write(data.content)

        # Leer el archivo temporal con pandas
        df = con.query("SELECT * FROM st_read('temp.xlsx')").df()

        # Eliminar el archivo temporal (opcional)
        os.remove("temp.xlsx")
        return df
    else:
        print(f"Error al descargar el archivo: {data.status_code}")
        return False

# Cargar Variables de Google Sheet
print('- Cargando Variables')
dfVariables = descargaExcel("https://subredeintenorte-my.sharepoint.com/:x:/g/personal/gestiondelainformacion_subrednorte_gov_co/EXm0_LeeWK9HlP755iqoY30BW6AWaQilIXmtzlZZDMxQlQ?e=r3Pf02")

if os.path.exists('fecha_cita.csv'):
    print('- Cargando fecha_cita.csv')
    dfFecha = con.query("SELECT * FROM st_read('fecha_cita.csv')").df()
else:
    print('- Cargando fecha_cita.xlsx')
    dfFecha = con.query("SELECT * FROM st_read('fecha_cita.xlsx')").df()

if os.path.exists('oportunidad_fecha_citaBD.csv'):
    print('- Cargando oportunidad_fecha_citaBD.csv')
    dfOportunidad = con.query("SELECT * FROM st_read('oportunidad_fecha_citaBD.csv')").df()
else:
    print('- Cargando oportunidad_fecha_citaBD.xlsx')
    dfOportunidad = con.query("SELECT * FROM st_read('oportunidad_fecha_citaBD.xlsx')").df()

# Actualizar los nombres de las columnas segun listado de DGH
dfFecha.columns = [
    'Fuente de la Cita','Documento de la Cita','Fecha de Grabacion','Carnet','Identificacion del Responsable',
    'Nombre Responsable','Concepto Facturacion','Codigo Producto (CUPS)','Especialidad','Nombre Especialidad',
    'Fecha Cita','Hora Cita','TIPO CITA','Fecha Preferencia Paciente','Estructura Administrativa',
    'Sede','Medico','Nombre Medico','Estado Cita','Duracion Cita',
    'Usuario','Nombre usuario','Primer Apellido usuario','Segundo Apellido usuario','Ingreso',
    'Primer Apellido Paciente','Segundo Apellido Paciente','Nombre Paciente','Fecha Nacimiento','Identificacion',
    'Tipo Doc','Nacionalidad','Telefono','Sexo Paciente','Barrio',
    'Nombre Barrio','Localidad','Nombre Localidad','Servicio Nieto','Regimen',
    'Grupo Usuario','Tipo Asignacion']
dfOportunidad.columns = [
    'Documento de la Cita','Fecha de Grabacion','Identificacion del Responsable','Nombre Responsable','Especialidad',
    'Nombre Especialidad','Fecha Cita','Hora Cita','TIPO CITA','Fecha Preferencia Paciente',
    'Estructura Administrativa','Sede','Medico','Nombre Medico','Estado Cita',
    'Duracion Cita','Usuario','Grupo Usuario','Ingreso','Primer Apellido Paciente',
    'Segundo Apellido Paciente','Nombre Paciente','Fecha Nacimiento','EDAD','Identificacion',
    'Tipo Doc','Telefono','Sexo Paciente','Servicio Nieto','Especialidad2',
    'Tipo Valida','Tipo de Cita','Vinculacion','OPORTUNIDAD_INST','OPORTUNIDAD_USU',
    'Codigo Producto (CUPS)','CMACODIGO']

# Convertir 'Estado Cita', 'TIPO CITA', 'Tipo Asignacion', 'Vinculacion' a mayuscula cada palabra
dfFecha['Estado Cita'] = dfFecha['Estado Cita'].str.title()
dfFecha['TIPO CITA'] = dfFecha['TIPO CITA'].str.title()
dfFecha['Tipo Asignacion'] = dfFecha['Tipo Asignacion'].str.title()
dfOportunidad['Estado Cita'] = dfOportunidad['Estado Cita'].str.title()
dfOportunidad['TIPO CITA'] = dfOportunidad['TIPO CITA'].str.title()
dfOportunidad['Vinculacion'] = dfOportunidad['Vinculacion'].str.title()

# Para validar - filtrar dfFecha para los que Nombre Responsable es 'ALIANZA MEDELLIN ANTIOQUIA EPSS S.A.S. SUBSIDIADO'
#dfFecha = dfFecha[dfFecha['Nombre Responsable'] == 'ALIANZA MEDELLIN ANTIOQUIA EPSS S.A.S. SUBSIDIADO']
#dfOportunidad = dfOportunidad[dfOportunidad['Nombre Responsable'] == 'ALIANZA MEDELLIN ANTIOQUIA EPSS S.A.S. SUBSIDIADO']

# %% Procesar datos
print('Procesando datos...')
# Agregar las vacias de dfFecha a dfOportunidad creando dfOportunidad_cita
# Filtrar dfFecha con la columna 'Fecha de Grabacion' vacia seleccionando las columnas 'Codigo Producto (CUPS)',
# 'Especialidad', 'Nombre Especialidad', 'Estructura Administrativa', 'Sede', 'Medico', 'Nombre Medico',
# 'Duracion Cita', 'Servicio Nieto'
dfFechaVacias = dfFecha[dfFecha['Fecha de Grabacion'].isna()][[
    'Codigo Producto (CUPS)', 'Especialidad', 'Nombre Especialidad', 'Estructura Administrativa', 'Sede',
    'Medico', 'Nombre Medico', 'Duracion Cita', 'Servicio Nieto']]

# Crear dfOportunidad_cita uniendo dfOportunidad con dfFechaVacias
dfOportunidad_cita = pd.concat([dfOportunidad, dfFechaVacias], ignore_index=True)

# Agregar a dfOportunidad_cita desde dfFecha las columnas 'Tipo Asignacion', 'Nacionalidad', 'Barrio',
# 'Nombre Barrio', 'Localidad', 'Nombre Localidad' cruzando con la columna 'Documento de la Cita', excluyendo las vacias, en ambas tablas
dfOportunidad_cita = pd.merge(
    dfOportunidad_cita,
    dfFecha[['Tipo Asignacion', 'Nacionalidad', 'Barrio', 'Nombre Barrio', 'Localidad',
    'Nombre Localidad', 'Documento de la Cita']].dropna(subset=['Documento de la Cita']),
    on='Documento de la Cita', how='left')

# Convertir la columna 'Duracion Cita' a formato datetime
dfOportunidad_cita['Duracion Cita'] = pd.to_datetime(dfOportunidad_cita['Duracion Cita'], format='%H:%M:%S')

# Calcular los minutos totales
dfOportunidad_cita['Duracion Cita'] = dfOportunidad_cita['Duracion Cita'].dt.hour * 60 + dfOportunidad_cita['Duracion Cita'].dt.minute

# Agregar a dfOportunidad_cita otras columnas de dfVariables
# En dfVariables cambiar los nombres de las columnas de 'Especialidad (Actividades)', 'ESPECIALIDAD AGRUP', 'Nieto-CIP' y 'valida'
# a 'Servicio Nieto', 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA' y 'TIPO 2', validando solo los valores únicos de 'Especialidad (Actividades)'
dfVariables.columns = ['Servicio Nieto', 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA', 'TIPO 2']

# Pasar a minusculas las columnas 'Servicio Nieto' para garantizar la coincidencia de los registros en el cruce
dfOportunidad_cita['Servicio Nieto'] = dfOportunidad_cita['Servicio Nieto'].str.lower().str.strip()
dfVariables['Servicio Nieto'] = dfVariables['Servicio Nieto'].str.lower().str.strip()

# Agregar a dfOportunidad_cita desde dfVariables las columnas 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA' y 'TIPO 2'
dfOportunidad_cita = pd.merge(
    dfOportunidad_cita,
    dfVariables.drop_duplicates(subset='Servicio Nieto'),
    on='Servicio Nieto', how='left')

# Reportar y arreglar las colmunas con vacios

# Crear dfOportunidad_citaVacias con las filas de dfOportunidad_cita que tienen campos vacios en alguna de las columnas 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA' y 'TIPO 2'
dfOportunidad_citaVacias = dfOportunidad_cita[
    dfOportunidad_cita['Nombre Especialidad CIP AJUST'].isna() |
    dfOportunidad_cita['nieto CIP AJUST FECHA CITA'].isna() |
    dfOportunidad_cita['TIPO 2'].isna()]

# Reemplaza los valores vacios de 'Nombre Especialidad CIP AJUST' y 'nieto CIP AJUST FECHA CITA' por el valor de 'Servicio Nieto'
dfOportunidad_cita['Nombre Especialidad CIP AJUST'] = dfOportunidad_cita[
    'Nombre Especialidad CIP AJUST'].fillna(dfOportunidad_cita['Servicio Nieto'])
dfOportunidad_cita['nieto CIP AJUST FECHA CITA'] = dfOportunidad_cita[
    'nieto CIP AJUST FECHA CITA'].fillna(dfOportunidad_cita['Servicio Nieto'])

# Reportar 'TIPO CITA' con errores

# Filtrar 'TIPO CITA' si tiene valor 'Remision' o si es vacío y 'Identificacion' no es vacío
dfOportunidad_citaTipoCitaError = dfOportunidad_cita[
    (dfOportunidad_cita['TIPO CITA'] == 'Remision') |
    (dfOportunidad_cita['TIPO CITA'].isna() &
    dfOportunidad_cita['Identificacion'].notnull())]

# Ordenar

# Ordenar por 'Sede' (Nombre compañia), 'Nombre Especialidad', 'Nombre Medico', 'Fecha Cita', 'Hora Cita', 'Documento de la Cita
dfOportunidad_cita = dfOportunidad_cita.sort_values(
    by=['Sede', 'Nombre Especialidad', 'Nombre Medico', 'Fecha Cita', 'Hora Cita', 'Documento de la Cita'])

# Oportunidad

# Convertir las columnas a tipo fecha
dfOportunidad_cita['Fecha de Grabacion'] = pd.to_datetime(dfOportunidad_cita['Fecha de Grabacion'], format='%d/%m/%Y')
dfOportunidad_cita['Fecha Cita'] = pd.to_datetime(dfOportunidad_cita['Fecha Cita'], format='%d/%m/%Y')
#dfOportunidad_cita['Fecha Preferencia Paciente'] = pd.to_datetime(dfOportunidad_cita['Fecha Preferencia Paciente'], format='%d/%m/%Y').dt.date
dfOportunidad_cita['Fecha Nacimiento'] = pd.to_datetime(dfOportunidad_cita['Fecha Nacimiento'], format='%d/%m/%Y')

# Calcular la Oportunidad como la diferencia de días entre 'Fecha de Grabacion' y 'Fecha Cita'
dfOportunidad_cita['Oportunidad'] = (dfOportunidad_cita['Fecha Cita'] - dfOportunidad_cita['Fecha de Grabacion']).dt.days

# Reprogramadas

# Crear Reprogramadas
dfOportunidad_cita['Reprogramadas'] = np.where(
    # Primera condición: Estas columnas deben coincidir con la fila anterior
    (dfOportunidad_cita['Sede'] == dfOportunidad_cita['Sede'].shift(1)) &
    (dfOportunidad_cita['Nombre Especialidad'] == dfOportunidad_cita['Nombre Especialidad'].shift(1)) &
    (dfOportunidad_cita['Nombre Medico'] == dfOportunidad_cita['Nombre Medico'].shift(1)) &
    (dfOportunidad_cita['Fecha Cita'] == dfOportunidad_cita['Fecha Cita'].shift(1)) &
    (dfOportunidad_cita['Hora Cita'] == dfOportunidad_cita['Hora Cita'].shift(1)),

    # Si si se cumple la primera condición, se entra en una segunda condicion
    np.where(
        # Segunda condición: Si 'Estado Cita' es 'Cancelada'
        dfOportunidad_cita['Estado Cita'] == 'Cancelada',

        # Si sí se cumple la segunda condición se entra en una Tercera condición: Si 'Estado Cita' fila anterior es 'Cancelada'
        np.where(dfOportunidad_cita['Estado Cita'].shift(1) == 'Cancelada', 'Reprogramada', 'No Reprogramada'),

        # Si no se cumple la segunda condición se entra en una Cuarta condición: Si 'Estado Cita' fila anterior es 'Cancelada'
        np.where(dfOportunidad_cita['Estado Cita'].shift(1) == 'Cancelada', 'Reprogramada', dfOportunidad_cita['Estado Cita'])
    ),

    # Si no se cumple la primera condición, dejar el valor original de 'Estado Cita'
    dfOportunidad_cita['Estado Cita']
)

# %% Pivotes

# Función para verificar columnas y crearlas en 0 si no existen
def verificaColumnas(df, columnas):
    """
    Verifica la existencia de las columnas y las crea en 0 si no existen.
    
    Args:
    - df (DataFrame): DataFrame a evaluar.
    - columnas (list): Lista de columnas a evaluar.
    
    Returns:
    - df (DataFrame): DataFrame con las columas verificadas.
    """

    # Itera por cada columna en la lista columnas
    for columna in columnas:
        # Valida si la columna existe
        if columna not in df.columns:
            # Si no existe, crearla y llenarla con ceros
            df[columna] = 0

    return df

# Filtrar dfOportunidad_cita por 'Estado Cita' igual a 'Atendida' creando dfOportunidad_cita_Atendida
dfOportunidad_cita_Atendida = dfOportunidad_cita[dfOportunidad_cita['Estado Cita'] == 'Atendida']

# Crear la tabla pivote Asignadas, crea columna 'Asignadas'
pivote_Asignadas = dfOportunidad_cita.groupby(
    ['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA']).size().reset_index(name='Asignadas')

# Pivote Estado

# Crear la tabla pivote Estados, crea columnas 'Atendida_x', 'Cancelada_x', 'Inatencion_x', 'Incumplida_x'
pivote_Estados = dfOportunidad_cita.pivot_table(
    index=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], columns='Estado Cita', aggfunc='size', fill_value=0).reset_index()

# Verificar si las columnas existen
pivote_Estados = verificaColumnas(pivote_Estados, ['Atendida', 'Cancelada', 'Inatencion', 'Incumplida'])

# Pivote Reprogramadas

# Crear la tabla pivote Estados, crea columnas 'Atendida_y', 'Cancelada_y', 'Inatencion_y', 'Incumplida_y', 'No Reprogramada', 'Reprogramada'
pivote_Reprogramadas = dfOportunidad_cita.pivot_table(
    index=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], columns='Reprogramadas', aggfunc='size', fill_value=0).reset_index()

# Verificar si las columnas existen
pivote_Reprogramadas = verificaColumnas(pivote_Reprogramadas, ['Atendida', 'Cancelada', 'Inatencion', 'Incumplida', 'No Reprogramada', 'Reprogramada'])

# Pivote Atendida Tipo

# Crear la tabla pivote Atendida Tipo, crea columnas 'Control_x', 'Primer Vez_x', 'Remision_x'
pivote_AtendidaTipo = dfOportunidad_cita_Atendida.pivot_table(
    index=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], columns='TIPO CITA', aggfunc='size', fill_value=0).reset_index()

# Verificar si las columnas existen
pivote_AtendidaTipo = verificaColumnas(pivote_AtendidaTipo, ['Control', 'Primer Vez', 'Remision'])

# Pivote Atendida Vinculacion

# Crear la tabla pivote Atendida Vinculacion, crea columnas 'Contributivo', 'Otro', 'Subsidiado', 'Vinculado'
pivote_AtendidaVinculacion = dfOportunidad_cita_Atendida.pivot_table(
    index=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], columns='Vinculacion', aggfunc='size', fill_value=0).reset_index()

# Verificar si las columnas existen
pivote_AtendidaVinculacion = verificaColumnas(pivote_AtendidaVinculacion, ['Contributivo', 'Otro', 'Subsidiado', 'Vinculado'])

# Pivote Tipo

# Crear la tabla pivote Tipo, crea columnas 'Control_y', 'Primer Vez_y', 'Remision_y'
pivote_Tipo = dfOportunidad_cita.pivot_table(
    index=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], columns='TIPO CITA', aggfunc='size', fill_value=0).reset_index()

# Verificar si las columnas existen
pivote_Tipo = verificaColumnas(pivote_Tipo, ['Control', 'Primer Vez', 'Remision'])

# Pivote Tipo Oportunidad

# Crear la tabla pivote Tipo Oportunidad, crea columnas 'Control', 'Primer Vez', 'Remision'
pivote_TipoOportunidad = dfOportunidad_cita.pivot_table(
    values='Oportunidad', index=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], columns='TIPO CITA', aggfunc='sum', fill_value=0).reset_index()

# Verificar si las columnas existen
pivote_TipoOportunidad = verificaColumnas(pivote_TipoOportunidad, ['Control', 'Primer Vez', 'Remision'])

# Pivote Tipo Asignacion

# Crear la tabla pivote Tipo Asignacion, crea columnas 'Extra', 'Normal'
pivote_TipoAsignacion = dfOportunidad_cita_Atendida.pivot_table(
    index=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], columns='Tipo Asignacion', aggfunc='size', fill_value=0).reset_index()

# Verificar si las columnas existen
pivote_TipoAsignacion = verificaColumnas(pivote_TipoAsignacion, ['Extra', 'Normal'])

# Combinar pivotes en dfConsulta_externa

# Combinar los pivotes en dfConsulta_externa
dfConsulta_pivote = pd.merge(pivote_Asignadas, pivote_Estados, on=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_Reprogramadas, on=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_AtendidaTipo, on=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_AtendidaVinculacion, on=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_Tipo, on=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_TipoOportunidad, on=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_TipoAsignacion, on=['Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA'], how='left')

# Crear columan 'Reales' como la suma de 'Programado' + 'No Reprogramada' + 'Reprogramada' + 'Extra'
dfConsulta_pivote['Reales'] = dfConsulta_pivote['Asignadas'] - dfConsulta_pivote['No Reprogramada'] - dfConsulta_pivote['Reprogramada'] - dfConsulta_pivote['Extra'] - dfConsulta_pivote['Inatencion_x']

# Crear 'horas_inf' como 'Programado' dividido 3
#dfConsulta_pivote['horas_inf'] = dfConsulta_pivote['Asignadas'] / 3

# Crear 'oportunidad_primera_vez' dividiendo 'Primer Vez_y' por 'Primer Vez' y manejando errores con np.where
#dfConsulta_pivote['oportunidad_primera_vez'] = np.where(
#    dfConsulta_pivote['Primer Vez_y'] != 0, dfConsulta_pivote['Primer Vez'] / dfConsulta_pivote['Primer Vez_y'], 0)

# Crear 'oportunidad_control' dividiendo 'Primer Vez_y' por 'Primer Vez' y manejando errores con np.where
#dfConsulta_pivote['oportunidad_control'] = np.where(dfConsulta_pivote['Control_y'] != 0, dfConsulta_pivote['Control'] / dfConsulta_pivote['Control_y'], 0)

# Crear 'val1' con valor 'Ok' si 'Primer Vez_y' + 'Control_y' = 'Asignadas', de lo contrario 'Error'
#dfConsulta_pivote['val1'] = np.where(
#    dfConsulta_pivote['Primer Vez_y'] + dfConsulta_pivote['Control_y'] ==
#    dfConsulta_pivote['Asignadas'], 'Ok', 'Error')

# Crear 'val2' con valor 'Ok' si ('Vinculado' + 'Subsidiado' + 'Contributivo' + 'Otro') = ('Primer Vez_x' + 'Control_x'), de lo contrario 'Error'
#dfConsulta_pivote['val2'] = np.where(
#    dfConsulta_pivote['Vinculado'] + dfConsulta_pivote['Subsidiado'] + dfConsulta_pivote['Contributivo'] + dfConsulta_pivote['Otro'] ==
#    dfConsulta_pivote['Primer Vez_x'] + dfConsulta_pivote['Control_x'], 'Ok', 'Error')

# Seleccionar las columnas finales
dfConsulta_pivote = dfConsulta_pivote[[
    'Nombre Responsable', 'Fecha Cita', 'TIPO 2', 'Sede', 'nieto CIP AJUST FECHA CITA',
    'Asignadas', 'Reales', 'Asignadas', 'Reprogramada', 'Cancelada_x',
    'Inatencion_x', 'Incumplida_x', 'Primer Vez_x', 'Control_x', 'Vinculado',
    'Subsidiado', 'Contributivo', 'Otro',
    #'horas_inf', 'Primer Vez_y', 'Primer Vez', 'oportunidad_primera_vez', 'Control_y',
    'Primer Vez_y', 'Primer Vez', 'Control_y',
    #'Control', 'oportunidad_control', 'val1', 'val2']]
    'Control']]

# Cambiar los nombres de las columnas
dfConsulta_pivote.columns = [
    'Responsable', 'Fecha', 'Tipo', 'Sede', 'Nieto',
    'Programado', 'Reales', 'Asignadas','Reprogramada', 'Cancelada',
    'Inatencion', 'Inasistencia', 'Primer_Vez', 'Control','Vinculado',
    'Subsidiado', 'Contributivo', 'Otro',
    #'horas_inf', 'asig_primer_vez', 'dias_primer_vez', 'oportunidad_primera_vez', 'asig_control',
    'asig_primer_vez', 'dias_primer_vez', 'asig_control',
    #'dias_control', 'oportunidad_control', 'val1', 'val2']
    'dias_control']

# %% Descargar los archivos

print('Descargando archivos ...')
# Convertir las columnas tipo fecha/hora a solo fecha en texto
dfOportunidad_cita['Fecha de Grabacion'] = dfOportunidad_cita['Fecha de Grabacion'].dt.strftime('%d/%m/%Y')
dfOportunidad_cita['Fecha Cita'] = dfOportunidad_cita['Fecha Cita'].dt.strftime('%d/%m/%Y')
#dfOportunidad_cita['Fecha Preferencia Paciente'] = dfOportunidad_cita['Fecha Preferencia Paciente'].dt.strftime('%d/%m/%Y')
dfOportunidad_cita['Fecha Nacimiento'] = dfOportunidad_cita['Fecha Nacimiento'].dt.strftime('%d/%m/%Y')

# Convertir los df a xlsx
print('- Descargando Oportunidad_cita.xlsx')
con.execute("COPY (SELECT * FROM dfOportunidad_cita) TO 'Oportunidad_cita.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('- Descargando FechaVacias.xlsx')
con.execute("COPY (SELECT * FROM dfFechaVacias) TO 'FechaVacias.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('- Descargando Oportunidad_citaVacias.xlsx')
con.execute("COPY (SELECT * FROM dfOportunidad_citaVacias) TO 'Oportunidad_citaVacias.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('- Descargando Oportunidad_citaTipoCitaError.xlsx')
con.execute("COPY (SELECT * FROM dfOportunidad_citaTipoCitaError) TO 'Oportunidad_citaTipoCitaError.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('- Descargando Consulta_pivote.xlsx')
con.execute("COPY (SELECT * FROM dfConsulta_pivote) TO 'Consulta_pivote.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
# %%
