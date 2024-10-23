# ETL-Ambulatorios
ETL del proceso de Ambulatorios

Carga los archivos:
- Variables (cargados de internet)
- fecha_cita.xlsx
- oportunidad_fecha_citaBD.xlsx

Después de procesar los archivos genera los archivos:
- Cruce - Oportunidad_cita.xlsx
- Vacíos de fecha - FechaVacias.xlsx
- Vacíos de oportunidad - Oportunidad_citaVacias.xlsx
- Errores en tipo cita - Oportunidad_citaTipoCitaError.xlsx
- Pivote resultante Consulta externa - Consulta_externa.xlsx