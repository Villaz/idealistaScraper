# idealistaScraper
Trabajo de la asignatura Tipología y ciclo de vida de los datos 

## Contexto
Actualmente la compra-venta y alquiler de vivienda es un tema de actualidad, teniendo especial interés
los precios y la disponibilidad de vivienda en las diferentes zonas de la geografía Española.

Para ello se ha decidido recolectar información de las viviendas ofertadas en territorios específicos
para así poder estudiar cual es la evolución del precio y la cantidad de las ofertas a lo largo del tiempo.

Para conseguir este objetivo se ha decidido extraer la información del portal inmobiliario Idealista, dado
que Idealista es considerado como el portal de viviendas más importante y grande del país posiblemente se puede
extraer del mismo la información más completa y veraz acerca de como se encuentra el parque inmobiliario en un instante de tiempo específico.

#Definición título dataset
El titulo del dataset depende de la tipología y zona geográfica donde se realiza el proceso de scraping.
El formato seguirá la siguiente estructura:
- <tipo_transaccion>-<tipologia>_<ciudad>-<provincia>.csv
- <tipo_transaccion>-<tipologia>_<ciudad>-<provincia_images>.csv

Donde:
- **tipo_transaccion** puede ser venta o alquiler.
- **tipologia** Actualmente solo puede ser viviendas, pero se puede extender a cualquier tipologia existente en el portal de Idealista.
- **ciudad** Ciudad donde se realiza la búsqueda.
- **provincia**: Provincia a la que pertenece la ciudad.

Así si por ejemplo queremos buscar las viviendas en venta en la ciudad de Oviedo que pertenece a Asturias, los csvs generandos serán:
- **venta-viviendas_oviiedo-asturias.csv** Conteniendo los datos de cada inmueble.
- **venta-viviendas_oviiedo-asturias_images.csv** Conteniendo la ruta de las imágenes de cada inmueble.

