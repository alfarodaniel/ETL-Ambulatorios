# -*- coding: utf-8 -*-
"""
Oportunidad Cita

Se procesan los reportes de DGH "fecha_cita.xlsx", "oportunidad_fecha_citaBD.xlsx" y el archivo de internet "Variables.xlsx" generando como resultado:
1. Cruce - Oportunidad_cita.xlsx
2. Vacíos de fecha - FechaVacias.xlsx
3. Vacíos de oportunidad - Oportunidad_citaVacias.xlsx
4. Errores en tipo cita - Oportunidad_citaTipoCitaError.xlsx
5. Pivote resultante Consulta externa - Consulta_externa.xlsx
"""
# %% Cargar archivos

# Cargar librerias
import pandas as pd
import numpy as np
import requests
import io
import duckdb
import os

print('Cargar archivos')
# Conectar a DuckDB y cargar los xlsx a df
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")

# Función descargaExcel para descargar los excel compartidos en OneDrive 365
def descargaExcel(url):
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
print('-Variables')
dfVariables = descargaExcel("https://subredeintenorte-my.sharepoint.com/:x:/g/personal/gestiondelainformacion_subrednorte_gov_co/EXm0_LeeWK9HlP755iqoY30BW6AWaQilIXmtzlZZDMxQlQ?e=r3Pf02")

print('-fecha_cita.xlsx')
dfFecha = con.query("SELECT * FROM st_read('fecha_cita.xlsx')").df()

print('-oportunidad_fecha_citaBD.xlsx')
dfOportunidad = con.query("SELECT * FROM st_read('oportunidad_fecha_citaBD.xlsx')").df()

# %% Procesar datos
print('Procesar datos')
# Agregar las vacias de dfFecha a dfOportunidad creando dfOportunidad_cita
# Filtrar dfFecha con la columna 'Fecha de Grabacion' vacia seleccionando las columnas 'Codigo Producto (CUPS)',
# 'Especialidad', 'Nombre Especialidad', 'Estructura Administrativa', 'Sede', 'Medico', 'Nombre Medico',
# 'Duracion Cita', 'Servicio Nieto'
dfFechaVacias = dfFecha[dfFecha['Fecha de Grabacion'].isna()][['Codigo Producto (CUPS)', 'Especialidad', 'Nombre Especialidad', 'Estructura Administrativa', 'Sede', 'Medico', 'Nombre Medico', 'Duracion Cita', 'Servicio Nieto']]

# Crear dfOportunidad_cita uniendo dfOportunidad con dfFechaVacias
dfOportunidad_cita = pd.concat([dfOportunidad, dfFechaVacias], ignore_index=True)

# Agregar a dfOportunidad_cita desde dfFecha las columnas 'Tipo Asignacion', 'Nacionalidad', 'Barrio',
# 'Nombre Barrio', 'Localidad', 'Nombre Localidad' cruzando con la columna 'Documento de la Cita', excluyendo las vacias, en ambas tablas
dfOportunidad_cita = pd.merge(dfOportunidad_cita, dfFecha[['Tipo Asignacion', 'Nacionalidad', 'Barrio', 'Nombre Barrio', 'Localidad', 'Nombre Localidad', 'Documento de la Cita']].dropna(subset=['Documento de la Cita']), on='Documento de la Cita', how='left')

# Convertir la columna 'Duracion Cita' a formato datetime
dfOportunidad_cita['Duracion Cita'] = pd.to_datetime(dfOportunidad_cita['Duracion Cita'], format='%H:%M:%S')

# Calcular los minutos totales
dfOportunidad_cita['Duracion Cita'] = dfOportunidad_cita['Duracion Cita'].dt.hour * 60 + dfOportunidad_cita['Duracion Cita'].dt.minute

# Agregar a dfOportunidad_cita otras columnas de dfVariables
# En dfVariables cambiar los nombres de las columnas de 'Especialidad (Actividades)', 'ESPECIALIDAD AGRUP', 'Nieto-CIP' y 'valida'
# a 'Servicio Nieto', 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA' y 'TIPO 2', validando solo los valores únicos de 'Especialidad (Actividades)'
dfVariables.columns = ['Servicio Nieto', 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA', 'TIPO 2']

# Pasar a minusculas las columnas 'Servicio Nieto' para garantizar la coincidencia de los registros en el cruce
dfOportunidad_cita['Servicio Nieto'] = dfOportunidad_cita['Servicio Nieto'].str.lower()
dfVariables['Servicio Nieto'] = dfVariables['Servicio Nieto'].str.lower()

# Agregar a dfOportunidad_cita desde dfVariables las columnas 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA' y 'TIPO 2'
dfOportunidad_cita = pd.merge(dfOportunidad_cita, dfVariables.drop_duplicates(subset='Servicio Nieto'), on='Servicio Nieto', how='left')

# Reportar y arreglar las colmunas con vacios

# Crear dfOportunidad_citaVacias con las filas de dfOportunidad_cita que tienen campos vacios en alguna de las columnas 'Nombre Especialidad CIP AJUST', 'nieto CIP AJUST FECHA CITA' y 'TIPO 2'
dfOportunidad_citaVacias = dfOportunidad_cita[dfOportunidad_cita['Nombre Especialidad CIP AJUST'].isna() | dfOportunidad_cita['nieto CIP AJUST FECHA CITA'].isna() | dfOportunidad_cita['TIPO 2'].isna()]

# Reemplaza los valores vacios de 'Nombre Especialidad CIP AJUST' y 'nieto CIP AJUST FECHA CITA' por el valor de 'Servicio Nieto'
dfOportunidad_cita['Nombre Especialidad CIP AJUST'] = dfOportunidad_cita['Nombre Especialidad CIP AJUST'].fillna(dfOportunidad_cita['Servicio Nieto'])
dfOportunidad_cita['nieto CIP AJUST FECHA CITA'] = dfOportunidad_cita['nieto CIP AJUST FECHA CITA'].fillna(dfOportunidad_cita['Servicio Nieto'])

# Reportar 'TIPO CITA' con errores

# Filtrar 'TIPO CITA' si tiene valor 'Remision' o si es vacío y 'Identificacion' no es vacío
dfOportunidad_citaTipoCitaError = dfOportunidad_cita[(dfOportunidad_cita['TIPO CITA'] == 'Remision') | (dfOportunidad_cita['TIPO CITA'].isna() & dfOportunidad_cita['Identificacion'].notnull())]

# Ordenar

# Ordenar por 'Sede' (Nombre compañia), 'Nombre Especialidad', 'Nombre Medico', 'Fecha Cita', 'Hora Cita', 'Documento de la Cita
dfOportunidad_cita = dfOportunidad_cita.sort_values(by=[ 'Sede', 'Nombre Especialidad', 'Nombre Medico', 'Fecha Cita', 'Hora Cita', 'Documento de la Cita'])

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

        # Si si se cumple la segunda condición se entra en una Tercera condición: Si 'Estado Cita' fila anterior es 'Cancelada'
        np.where(dfOportunidad_cita['Estado Cita'].shift(1) == 'Cancelada', 'Reprogramada', 'No Reprogramada'),

        # Si no se cumple la segunda condición se entra en una Cuarta condición: Si 'Estado Cita' fila anterior es 'Cancelada'
        np.where(dfOportunidad_cita['Estado Cita'].shift(1) == 'Cancelada', 'Reprogramada', dfOportunidad_cita['Estado Cita'])
    ),

    # Si no se cumple la primera condición, dejar el valor original de 'Estado Cita'
    dfOportunidad_cita['Estado Cita']
)

# %% Pivotes

# Filtrar dfOportunidad_cita por 'Estado Cita' igual a 'Atendida' creando dfOportunidad_cita_Atendida
dfOportunidad_cita_Atendida = dfOportunidad_cita[dfOportunidad_cita['Estado Cita'] == 'Atendida']

# Crear la tabla pivote Asignadas
pivote_Asignadas = dfOportunidad_cita.groupby(['TIPO 2', 'Sede', 'Nombre Especialidad']).size().reset_index(name='Asignadas')

# Pivote Estado

# Crear la tabla pivote Estados
pivote_Estados = dfOportunidad_cita.pivot_table(index=['TIPO 2', 'Sede', 'Nombre Especialidad'], columns='Estado Cita', aggfunc='size', fill_value=0).reset_index()

# Pivote Reprogramadas

# Crear la tabla pivote Estados
pivote_Reprogramadas = dfOportunidad_cita.pivot_table(index=['TIPO 2', 'Sede', 'Nombre Especialidad'], columns='Reprogramadas', aggfunc='size', fill_value=0).reset_index()

# Pivote Atendida Tipo

# Crear la tabla pivote Atendida Tipo
pivote_AtendidaTipo = dfOportunidad_cita_Atendida.pivot_table(index=['TIPO 2', 'Sede', 'Nombre Especialidad'], columns='TIPO CITA', aggfunc='size', fill_value=0).reset_index()

# Pivote Atendida Vinculacion

# Crear la tabla pivote Atendida Vinculacion
pivote_AtendidaVinculacion = dfOportunidad_cita_Atendida.pivot_table(index=['TIPO 2', 'Sede', 'Nombre Especialidad'], columns='Vinculacion', aggfunc='size', fill_value=0).reset_index()

# Pivote Tipo

# Crear la tabla pivote Tipo
pivote_Tipo = dfOportunidad_cita.pivot_table(index=['TIPO 2', 'Sede', 'Nombre Especialidad'], columns='TIPO CITA', aggfunc='size', fill_value=0).reset_index()

# Pivote Tipo Oportunidad

# Crear la tabla pivote Tipo Oportunidad
pivote_TipoOportunidad = dfOportunidad_cita.pivot_table(values='Oportunidad', index=['TIPO 2', 'Sede', 'Nombre Especialidad'], columns='TIPO CITA', aggfunc='sum', fill_value=0).reset_index()

# Pivote Tipo Asignacion

# Crear la tabla pivote Tipo Asignacion
pivote_TipoAsignacion = dfOportunidad_cita_Atendida.pivot_table(index=['TIPO 2', 'Sede', 'Nombre Especialidad'], columns='Tipo Asignacion', aggfunc='size', fill_value=0).reset_index()

# Combinar pivotes en dfConsulta_externa

# Combinar los pivotes en dfConsulta_externa
dfConsulta_pivote = pd.merge(pivote_Asignadas, pivote_Estados, on=['TIPO 2', 'Sede', 'Nombre Especialidad'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_Reprogramadas, on=['TIPO 2', 'Sede', 'Nombre Especialidad'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_AtendidaTipo, on=['TIPO 2', 'Sede', 'Nombre Especialidad'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_AtendidaVinculacion, on=['TIPO 2', 'Sede', 'Nombre Especialidad'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_Tipo, on=['TIPO 2', 'Sede', 'Nombre Especialidad'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_TipoOportunidad, on=['TIPO 2', 'Sede', 'Nombre Especialidad'], how='left')
dfConsulta_pivote = pd.merge(dfConsulta_pivote, pivote_TipoAsignacion, on=['TIPO 2', 'Sede', 'Nombre Especialidad'], how='left')

# Crear columan 'Reales' como la suma de 'Programado' + 'No Reprogramada' + 'Reprogramada' + 'Extra'
dfConsulta_pivote['Reales'] = dfConsulta_pivote['Asignadas'] + dfConsulta_pivote['No Reprogramada'] + dfConsulta_pivote['Reprogramada'] + dfConsulta_pivote['Extra']

# Crear 'horas_inf' como 'Programado' dividido 3
dfConsulta_pivote['horas_inf'] = dfConsulta_pivote['Asignadas'] / 3

# Crear 'oportunidad_primera_vez' dividiendo 'Primer Vez_y' por 'Primer Vez' y manejando errores con np.where
dfConsulta_pivote['oportunidad_primera_vez'] = np.where(dfConsulta_pivote['Primer Vez_y'] != 0, dfConsulta_pivote['Primer Vez'] / dfConsulta_pivote['Primer Vez_y'], 0)

# Crear 'oportunidad_control' dividiendo 'Primer Vez_y' por 'Primer Vez' y manejando errores con np.where
dfConsulta_pivote['oportunidad_control'] = np.where(dfConsulta_pivote['Control_y'] != 0, dfConsulta_pivote['Control'] / dfConsulta_pivote['Control_y'], 0)

# Crear 'val1' con valor 'Ok' si 'Primer Vez_y' + 'Control_y' = 'Asignadas', de lo contrario 'Error'
dfConsulta_pivote['val1'] = np.where(dfConsulta_pivote['Primer Vez_y'] + dfConsulta_pivote['Control_y'] ==
                                      dfConsulta_pivote['Asignadas'], 'Ok', 'Error')

# Crear 'val2' con valor 'Ok' si ('Vinculado' + 'Subsidiado' + 'Contributivo' + 'Otro') = ('Primer Vez_x' + 'Control_x'), de lo contrario 'Error'
dfConsulta_pivote['val2'] = np.where(dfConsulta_pivote['Vinculado'] + dfConsulta_pivote['Subsidiado'] + dfConsulta_pivote['Contributivo'] + dfConsulta_pivote['Otro'] ==
                                     dfConsulta_pivote['Primer Vez_x'] + dfConsulta_pivote['Control_x'], 'Ok', 'Error')

# Seleccionar las columnas finales
dfConsulta_pivote = dfConsulta_pivote[['TIPO 2', 'Sede', 'Nombre Especialidad', 'Asignadas', 'Reales',
                                       'Asignadas', 'Reprogramada', 'Cancelada_x', 'Incumplida_x', 'Primer Vez_x',
                                       'Control_x', 'Vinculado', 'Subsidiado', 'Contributivo', 'Otro',
                                       'horas_inf', 'Primer Vez_y', 'Primer Vez', 'oportunidad_primera_vez', 'Control_y',
                                       'Control','val1', 'val2']]

# Cambiar los nombres de las columnas
dfConsulta_pivote.columns = ['Tipo', 'Sede', 'Nieto', 'Programado', 'Reales',
                             'Asignadas','Reprogramada', 'Cancelada', 'Inasistencia', 'Primer_Vez',
                             'Control','Vinculado', 'Subsidiado', 'Contributivo', 'Otro',
                             'horas_inf', 'asig_primer_vez', 'dias_primer_vez', 'oportunidad_primera_vez', 'asig_control',
                             'dias_control','val1', 'val2']

# %% Descargar los archivos

print('Descargar archivos')
# Convertir las columnas tipo fecha/hora a solo fecha en texto
dfOportunidad_cita['Fecha de Grabacion'] = dfOportunidad_cita['Fecha de Grabacion'].dt.strftime('%d/%m/%Y')
dfOportunidad_cita['Fecha Cita'] = dfOportunidad_cita['Fecha Cita'].dt.strftime('%d/%m/%Y')
#dfOportunidad_cita['Fecha Preferencia Paciente'] = dfOportunidad_cita['Fecha Preferencia Paciente'].dt.strftime('%d/%m/%Y')
dfOportunidad_cita['Fecha Nacimiento'] = dfOportunidad_cita['Fecha Nacimiento'].dt.strftime('%d/%m/%Y')

# Convertir los df a xlsx
print('-Oportunidad_cita.xlsx')
con.execute("COPY (SELECT * FROM dfOportunidad_cita) TO 'Oportunidad_cita.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('-FechaVacias.xlsx')
con.execute("COPY (SELECT * FROM dfFechaVacias) TO 'FechaVacias.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('-Oportunidad_citaVacias.xlsx')
con.execute("COPY (SELECT * FROM dfOportunidad_citaVacias) TO 'Oportunidad_citaVacias.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('-Oportunidad_citaTipoCitaError.xlsx')
con.execute("COPY (SELECT * FROM dfOportunidad_citaTipoCitaError) TO 'Oportunidad_citaTipoCitaError.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")
print('-Consulta_pivote.xlsx')
con.execute("COPY (SELECT * FROM dfConsulta_pivote) TO 'Consulta_pivote.xlsx' WITH (FORMAT GDAL, DRIVER 'xlsx');")