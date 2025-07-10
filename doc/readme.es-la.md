# mupl - MangaDex Bulk Uploader
Sube carpetas y archivos zip (.zip/.cbz) a MangaDex de forma rápida y sencilla.

*Deberás aceptar los [términos y condiciones de MangaDex](https://mangadex.org/compliance) para utilizar esta herramienta. Mupl no se hace responsable de las subidas que vayan en contra de los términos y condiciones.*

Lee esto en otros lenguajes: 
[English](/readme.md)

***Habrá una versión para cada idioma, con el inglés incluido en cada una de ellas. Para descargar todos los idiomas, descarga el zip de los archivos fuente.***

## Tabla de contenidos
- [Cómo usar](#cómo-usar)
  - [Como dependencia](#dependencia)
  - [Descargar](#descargar)
  - [Instalar](#instalar)
  - [Ejecutar](#ejecutar)
  - [Argumentos de linea de comandos](#argumentos-de-linea-de-comandos)
- [Estructura de los archivos](#estructura-de-los-archivos)
  - [Formato de nombre](#formato-de-nombre)
  - [Parametros](#parámetros)
  - [Tipos de imagen aceptados](#tipos-de-imagen-aceptados)
  - [Tamaño de las imagenes](#tamaño-de-imagenes)
    - [Separar imagenes](#separar-imagenes)
    - [Combinar imagenes](#combinar-imagenes)
- [Configuración](#configuración)
  - [Configuración de usuario](#opciones)
  - [Credenciales de MangaDex](#credenciales)
  - [Rutas del programa](#rutas)
- [Mapa de Nombre a ID](#mapa-de-nombre-a-id)
  - [Ejemplo](#ejemplo)
- [Contribuir](#contribution)
- [Traducción](#translation)


## Cómo usar
### Este programa solo está probado en la versión de Python 3.10+

### Dependencia
Para utilizar este subidor en otros scripts, instale la última versión a través de pypi `pip install muplr`.

```python
from mupl import Mupl
from datetime import datetime
from pathlib import Path

# Inicializar Mupl
# La mayoría de los parámetros tienen valores razonables por defecto, proporciona las credenciales necesarias.
# La ruta de Home en Unix/Mac es /Users/<>/mupl, en Windows es C:\Users\<>\mupl.

mupl = Mupl(
    mangadex_username="your_username",             # Tu nombre de usuario de MangaDex.
    mangadex_password="your_password",             # Tu contraseña de MangaDex
    client_id="your_client_id",                    # Tu ID de cliente de la API MangaDex (opcional si utilizas nombre de usuario/contraseña)
    client_secret="your_client_secret",            # Tu clave de cliente de la API de MangaDex (opcional si utilizas nombre de usuario/contraseña)
    # --- Optional Parameters ---       
    # move_files=True,                             # Mover archivos del directorio upload al directorio “uploaded_files” al finalizar una subida éxitosa
    # verbose_level=0,                             # Nivel de registro (0=INFO, 1=DEBUG)
    # number_of_images_upload=10,                  # Número de imagenes por petición de subida
    # upload_retry=3,                              # Número de reintentos para subidas fallidas
    # ratelimit_time=2,                            # Segundos de espera entre llamadas a la API
    # logs_dir_path=None,                          # Directorio donde almacenar los logs. Por defecto es la ruta de Home. Se creará la carpeta "logs" en este directorio.
    # max_log_days=30,                             # Días de conservación de los registros
    # group_fallback_id=None,                      # UUID de grupo por defecto si no se encuentra en el nombre de archivo/mapa
    # number_threads=3,                            # Número de subprocesos para la subida simultánea de imágenes
    # language="en",                               # Código de idioma para el lenguaje de mupl
    # name_id_map_filename="name_id_map.json",     # Nombre del archivo del mapa de nombre-a-id (relativo a home_path o ruta absoluta), no es necesario para las subdas de un solo capítulo.
    # uploaded_dir_path="uploaded",                # Nombre del directorio/ruta para los archivos subidos correctamente (relativo a home_path o ruta absoluta para la carpeta)
    # mangadex_api_url="https://api.mangadex.org", # URL base para la API MangaDex
    # mangadex_auth_url="https://auth.mangadex.org/realms/mangadex/protocol/openid-connect", # URL base para MangaDex Auth
)

# --- Subir un directorio ---
# Ruta del directorio que contiene los archivos de los capítulos (zip/cbz) o carpetas nombradas según la estructura de los archivos.
# Consulta la sección Estructura de los archivos más abajo.
upload_directory_path = Path("ruta/a/tu/carpeta_de_capitulos") # o "ruta/a/tu/carpeta_de_capitulos"

failed_uploads_list = mupl.upload_directory(
    upload_dir_path=upload_directory_path,
    # --- Argumentos opcionales para upload_directory ---
    # widestrip=False, # Marcar capítulos como formato widestrip
    # combine=False    # Combinar imágenes pequeñas verticalmente
)

# Retorna:
# 'None' si no se encuentran archivos válidos, de lo contrario se devuelve una lista de objetos pathlib de subidas fallidas.
# Si la lista está vacía, no se ha habido ninguna subida fallida.

# --- Subir un solo capítulo ---
# Proporciona metadatos explícitamente para un archivo o carpeta de un solo capítulo.
chapter_file_or_folder_path = Path("ruta/a/tu/capitulo.zip") # o Path("ruta/a/tu/carpeta_de_capitulos") o una cadena de caracteres "ruta/a/tu/capitulo.zip"
manga_uuid = "manga-uuid-aqui"
group_uuids = ["grupo-uuid-1", "grupo-uuid-2"] # Lista de UUIDs de los grupos

upload_successful = mupl.upload_chapter(
    file_path=chapter_file_or_folder_path,
    manga_id=manga_uuid,
    group_ids=group_uuids,
    # --- Argumentos opcionales para upload_chapter ---
    # language="en",                        # Código de idioma del capítulo
    # oneshot=False,                        # Marcar como oneshot (True) o capítulo normal (False)
    # chapter_number="10",                  # Número de capítulo (por ejemplo, "10", "10.5"). Se ignora si oneshot=True.
    # volume_number="2",                    # Número de volumen (opcional)
    # chapter_title="Chapter Title Here",   # Título del capítulo (opcional)
    # publish_date=None,                    # Valor de fecha y hora para una publicación programada (opcional)
    # widestrip=False,                      # Marcar capítulo como formato widestrip
    # combine=False                         # Combinar imágenes pequeñas verticalmente
)

# Retorna:
# 'True' si la subida fue éxitosa, de lo contrario 'False'.

print(f"Failed directory uploads: {failed_uploads_list}")
print(f"Single chapter upload successful: {upload_successful}")
```

### Descargar
Descarga la [última versión]((https://github.com/ArdaxHz/mupl/releases/latest)) desde la sección de releases.

Descomprime el archivo a una carpeta y abre una nueva terminal (bash, powershell, cmd). Navega a la carpeta creada usando `cd <direccion_de_la_carpeta>`

### Instalar
Antes de ejecutar el programa, necesitarás instalar los módulos necesarios.
Para instalar dichos módulos, ejecuta el comando `pip install -r requirements.txt` en la carpeta del programa. Si usas Mac o Linux, usa `pip3` en vez de `pip`.

En la carpeta del programa, crea una nueva carpeta llamada `to_upload` y otra llamada `uploaded`.

### Ejecutar
Para ejecutar el programa, escribe `python mupl.py` en la terminal (bash, powershell, cmd). Si usas Mac o Linux, utiliza `python3` en lugar de `python`.

### Actualizaciones
El programa comprobará automáticamente al iniciar si hay una nueva versión disponible en la página de versiones. Si hay una nueva versión, te preguntará si quieres actualizar.

Puedes desactivar la comprobación automatica añadiendo `--update` en el comando de ejecución del programa. Por ejemplo: `python mupl.py --update`.

### Argumentos de linea de comandos
Hay argumentos que se pueden agregar al comando de ejecución para cambiar el comportamiento del programa, por ejemplo: `python mupl.py -t`

##### Opciones:
- `--update` `-u` El programa no revisará nuevas versiones disponibles al iniciar.
- `--verbose` `-v` Hace que los mensajes de la línea de comandos y los registros sean más detallados.
- `--threaded` `-t` Ejecuta el subidor multihilo. *Default: False*
- `--combine` `-c` Combina la imagen cuya resolución es igual o más pequeña a 128px con la imagen anterior. *Default: False*
- `--widestrip` `-w` Divide las imágenes de más de 10000px de ancho en varias imágenes más pequeñas. *Default: False*

## Estructura de los archivos
#### Formato de nombre
`manga_title [lang] - cXXX (vYY) (chapter_title) {publish_date} [group]`

#### Parámetros
- `manga_title` El título del manga (el mismo que estableciste en `name_id_map.json`) o la ID del manga en MangaDex.
- `[lang]` Código ISO del lenguaje *Omitido para inglés.*
- `cXXX` Número del capítulo *Omitir el prefijo si el capítulo es un oneshot, ejemplo: `cXXX` > `XXX`.*
- `(vYY)` Volumen del capítulo *Opcional.*
- `(chapter_title)` Título del capítulo. Utiliza `{question_mark}` en donde deba de haber un `?`. *Opcional.*
- `{publish_date}` Fecha a futuro de cuando el capítulo será publicado en MangaDex. *El formato **TIENE QUE SER** el siguiente: `AAA-MM-DDTHH-MM-SS` si se incluye.* *Opcional.*
- `[group]` Lista de nombre de los grupos o sus ID. Si son nombres, deberán estar en el `name_id_map.json` con sus IDs correspondientes. *Separa multiples grupos utilizando `+`.* *Opcional.*

##### Caracteres de sustitución para los títulos de capítulo
- `{asterisk}` `*` *`{asterisk}` se reemplazará con `*` durante el proceso de subida.*
- `{backslash}` `\` *`{backslash}` se reemplazará con `\` durante el proceso de subida.*
- `{slash}` `/` *`{slash}` se reemplazará con `/` durante el proceso de subida.*
- `{colon}` `:` *`{colon}` se reemplazará con `:` durante el proceso de subida.*
- `{greater_than}` `>` *`{greater_than}` se reemplazará con `>` durante el proceso de subida.*
- `{less_than}` `<` *`{less_than}` se reemplazará con `<` durante el proceso de subida.*
- `{question_mark}` `?` *`{question_mark}` se reemplazará con `?` durante el proceso de subida.*
- `{quote}` `"` *`{quote}` se reemplazará con `"` durante el proceso de subida.*
- `{pipe}` `|` *`{pipe}` se reemplazará con `|` durante el proceso de subida.*

#### Tipos de imagen aceptados
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Serán convertidos automáticamente a `png`, `jpg` o `gif` durante el proceso de subida.*

#### Tamaño de imagenes
##### Separar imagenes
Las imágenes no pueden superar los `10000px` de anchura o altura. Las imágenes de más de 10000px de altura se dividirán como una imagen longstrip. Para dividir una imagen widestrip, utiliza el argumento `--widestrip` `-w`.

##### Combinar imagenes
Si se está usando el argumento `--combine`, las imágenes cuya resolución sea igual o más pequeña que `128px` se combinarán con la imagen anterior, **SOLO SI** la imagen anterior tiene la misma resolución (esto depende de si la imagen es longstrip o widestrip).

Si no se utiliza esta opción o si las imágenes no tienen la misma resolución, el programa las saltará.

## Configuración
Las opciones que pueden modificarse están disponibles en el archivo `config.json`. Aquí es donde introduces tus credenciales de tu cuenta de MangaDex.
Para empezar a usar el archivo de configuración, copia y elimina la extensión `.example` del archivo `config.json.example.`

*Nota: Los valores JSON no pueden estar vacíos.*
- Escribe (`null`) cuando un valor deba estar vacío.
- El texto debe ir entre comillas (`"username"`).
- Dígitos (`1.1`) para valores numéricos.


#### Opciones
- `number_of_images_upload` Número de imágenes para subir a la vez. *Default: 10*
- `upload_retry` Número de reintentos de subida de imágenes o capítulos. *Default: 3*
- `ratelimit_time` Tiempo (en segundos) de espera tras cada llamada a la API. *Default: 2*
- `max_log_days` Tiempo (en días) en los que se mantienen los registros del programa. *Default: 30*
- `group_fallback_id` ID de grupo a utilizar si no se encuentra en el archivo o mapa de IDs, dejar en blanco para no subir a un grupo. *Default: null*
- `number_threads`: Número de hilos para la subida simultanea de imágenes. **Esto puede limitar tu velocidad de subida.** El número de hilos están limitados a un rango de 1-3 (inclusivo). *Default: 3*
- `language`: Idioma para los mensajes de la línea de comandos. *Default: en*

#### Credenciales
***Estos valores no pueden estar vacíos, ya que de lo contrario el programa no funcionará.***
- `mangadex_username` Nombre de usuario de tu cuenta en MangaDex.
- `mangadex_password` Contraseña de tu cuenta en MangaDex.
- `client_id` ID de cliente para la API de MangaDex.
- `client_secret` Clave del cliente de la API de MangaDex.

#### Rutas
*Estas opciones no es necesario que las modifiques, puedes dejarlas tal cual están*
- `name_id_map_file` Nombre del archivo para el mapa de nombre-a-id. *Default: name_id_map.json*
- `uploads_folder` Directorio de donde se obtienen los archivos a subir. *Default: to_upload*
- `uploaded_files` Directorio a donde se mueven los archivos subidos. *Default: uploaded*
- `mangadex_api_url` URL de la API de MangaDex *Default: https://api.mangadex.org*
- `mangadex_auth_url` URL de autenticación de MangaDex *Default: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` Archivo de guardado local para el token de inicio de sesión de MangaDex. *Default: .mdauth*

<details>
  <summary>Cómo obtener un ID de cliente y clave</summary>

  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />


## Mapa de Nombre a ID
El archivo `name_id_map.json` tiene el siguiente formato:
```json
{
    "manga": {
        "hyakkano": "efb4278c-a761-406b-9d69-19603c5e4c8b"
    },
    "group": {
        "XuN": "b6d57ade-cab7-4be7-b2b8-be68484b3ad3"
    }
}
```
`manga` y `group` contienen el mapa de nombre a ID para el manga que se va a subir y el grupo al que corresponde, respectivamente. Los nombres deben ser los mismos que pondrás en el archivo. Para evitar problemas al subir, se recomienda que los nombres estén en minúsculas y no contengan espacios ni caracteres especiales.

Cada nuevo par de nombre a id debe ir separado por una coma al final de la línea y tener dos puntos entre el nombre y la ID. El último par de cada mapa no debe tener coma.

#### Ejemplo

Tomando como ejemplo `hyakkano - c025 (v04) [XuN].cbz` como el capítulo el cual quiero subir. En mi archivo `name_id_map.json`, tendré el valor `hyakkano` y la ID `efb4278c-a761-406b-9d69-19603c5e4c8b` como la ID del manga al que quiero subir. También tengo `XuN` como el grupo, con su valor `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

El programa entonces leerá el valor de `hyakkano` y el de `XuN`, y obtendrá las ID correspondientes.

Si tengo un archivo llamado `efb4278c-a761-406b-9d69-19603c5e4c8b [es] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, el programa tomará la ID del manga directamente del archivo y el idioma será español. Usando el código ISO `es`, el número de capítulo será nulo (oneshot) y no tendrá volumen. Tendrá como título `Momi-san` y se asignará a los grupos `XuN` (ID tomada del archivo `name_id_map.json`) y al grupo con la ID `00e03853-1b96-4f41-9542-c71b8692033b`.


## Contribuir
- Asegúrate de que no hay problemas duplicados antes de abrir uno.
- Puedes abrir pull requests si crees que es necesario, pero por favor formatea cualquier código con Python Black (configuración por defecto) antes de hacerlo.

## Traducción
Hay dos archivos para traducir, este readme y el archivo [mupl/loc/en.json](mupl/loc/en.json).

- El README traducido debe colocarse en [doc](doc/) con el nombre `readme.<>.md` con el código de idioma ISO entre los puntos, por ejemplo: `readme.pt-br.md`.
- El archivo JSON traducido debe tener el nombre `<>.json` con el código de idioma ISO que se esté utilizando y colocado dentro del directorio [mupl/loc/](mupl/loc/), por ejemplo: `pt-br.json`. 

Por favor, envía un PR con estos cambios.
