# mupl - MangaDex Bulk Uploader
Sube carpetas y zips (.zip/.cbz) a MangaDex de forma rápida y sencilla.

Lee esto en otros lenguajes: 
[English](doc/readme.md) 
[Português (Brasil)](doc/readme.pt-br.md)
[French](doc/readme.fr.md)

## Tabla de contenidos
- [Cómo usar](#cómo-usar)
  - [Argumentos de linea de comandos](#argumentos-de-linea-de-comandos)
- [Formato de archivos a subir](#formato-de-archivo-a-subir)
  - [Formato de nombre](#formato-de-nombre)
  - [Parametros](#parámetros)
  - [Tipos de imagen aceptados](#tipos-de-imagen-aceptados)
- [Configuración](#configuración)
  - [Configuración de usuario](#opciones)
  - [Credenciales de MangaDex](#credenciales)
  - [Rutas del programa](#rutas)
- [Mapa de Nombre a ID](#mapa-de-nombre-a-id)
  - [Ejemplo](#ejemplo)
- [Contribuir](#contribution)
- [Traducción](#translation)


## Cómo usar
Descarga la [última versión]((https://github.com/ArdaxHz/mupl/releases/latest)) (el zip con el código fuente) desde la sección de releases, descomprime el archivo a una carpeta y abre la terminal en esa carpeta.

En la terminal (bash, powershell, cmd) escribe `python mupl.py` para ejecutar el subidor.
Asegúrate que tienes Python 3.9+ instalado, escribe `python` si estás en windows y `python3` si estás en mac o linux

### Argumentos de linea de comandos
Hay argumentos que se pueden agregar al comando principal para cambiar el comportamiento del programa, por ejemplo: `python mupl.py -u`

##### Opciones:
- `--update` `-u` El programa no revisará nuevas versiones disponibles al iniciar.
- `--verbose` `-v` Hace que los mensajes de la línea de comandos y los registros sean más detallados.
- `--threaded` `-t` Ejecuta el subidor multihilo. *Default: False*

## Formato de archivo a subir
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

#### Tipos de imagen aceptados
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Serán convertidos automáticamente a `png`, `jpg`, o `gif` durante el proceso de subida.*

## Configuración
Las opciones modificables por el usuario están disponibles en el archivo `config.json`. Aquí también es donde pones tus credenciales de MangaDex.
Copia y elimina el `.example` de `config.json.example` para empezar a usar el archivo de configuracion.

*Nota: Los valores JSON no pueden estar vacíos, por lo tanto utiliza (`null`) cuando un valor deba estar vacío, una cadena (`"username"`) para valores de cadena, o un dígito (`1`) para valores numéricos.*


#### Opciones
- `number_of_images_upload` Número de imágenes para subir a la vez. *Default: 10*
- `upload_retry` Número de reintentos de subida de imágenes o capítulos. *Default: 3*
- `ratelimit_time` Tiempo (en segundos) de espera tras cada llamada a la API. *Default: 2*
- `max_log_days` Tiempo (en días) en los que se mantienen los registros. *Default: 30*
- `group_fallback_id` ID de grupo a utilizar si no se encuentra en el archivo o mapa de IDs, dejar en blanco para no subir a un grupo.. *Default: null*
- `number_threads`: Número de hilos para la subida simultanea de imágenes. **Esto puede limitar tu velocidad de subida.** El número de hilos están limitados a un rango de 1-3 (inclusivo). *Default: 3*
- `language`: Idioma para los mensajes de la línea de comandos. *Default: null*

#### Credenciales
***Estos valores no pueden estar vacíos, ya que de lo contrario el programa no funcionará***
- `mangadex_username` Nombre de usuario de tu cuenta en MangaDex.
- `mangadex_password` Contraseña de tu cuenta en MangaDex.
- `client_id` ID de cliente para la API de MangaDex.
- `client_secret` Secret de cliente para la API de MangaDex.

#### Rutas
*Estas opciones no es necesario que las modifiques, puedes dejarlas tal cual están*
- `name_id_map_file` Nombre de archivo para el mapa de nombre a id. *Default: name_id_map.json*
- `uploads_folder` Directorio de donde se obtienen los archivos a subir. *Default: to_upload*
- `uploaded_files` Directorio a donde se mueven los archivos subidos. *Default: uploaded*
- `mangadex_api_url` URL de la API de MangaDex *Default: https://api.mangadex.org*
- `mangadex_auth_url` URL de atentitación de MangaDex *Default: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` Archivo de guardado local para el token de inicio de sesión de MangaDex. *Default: .mdauth*

<details>
  <summary>Cómo obtener un ID de cliente y secret</summary>

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
`manga` y `group` contienen el mapa de nombre a id para el manga a subir y el grupo al que le corresponde, respectivamente. Los nombres deben ser los mismos que pondrás en el archivo. Para evitar problemas al subir, es recomendable que los nombres estén en minúsculas, no tengan espacios, ni caracteres especiales.

Cada nuevo par de nombre a id debe ser separado por una coma al final de la linea y tener un dos puntos entre el nombre y la ID. El ultimo par de cada mapa no deberá tener una coma.

#### Ejemplo

Tomando de ejemplo el capítulo `hyakkano - c025 (v04) [XuN].cbz` como el cual quiero subir. En mi `name_id_map.json`, tendré `hyakkano` y el valor `efb4278c-a761-406b-9d69-19603c5e4c8b` y como la ID del manga al que quiero subir. También tengo `XuN` como el grupo, con su valor `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

El programa entonces leerá el valor de `hyakkano` y el de `XuN`, así obteniendo las IDs que les corresponden.

Si tengo un archivo llamado `efb4278c-a761-406b-9d69-19603c5e4c8b [es] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, el programa tomará la ID del manga directamente del archivo, el lenguaje será español, usando el código ISO `es`, el número de capítulo será null (oneshot) y no tendrá volumen; tendrá como título `Momi-san` y será asignado a los grupos `XuN` (id tomada del `name_id_map.json`) y `00e03853-1b96-4f41-9542-c71b8692033b`.


## Contribuir
- Asegúrate de que no hay problemas duplicados antes de abrir uno.
- Puedes abrir pull requests si crees que es necesario, pero por favor formatea cualquier código con Python Black (configuración por defecto) antes de hacerlo.

## Traducción
Hay dos archivos para traducir, este readme y el archivo [mupl/loc/en.json](mupl/loc/en.json).

- El README traducido debe colocarse en [doc](doc/) con el nombre `readme.<>.md` con el código de idioma ISO entre los puntos, por ejemplo: `readme.pt-br.md`.
- El archivo JSON traducido debe tener el nombre `<>.json` con el código de idioma ISO que se esté utilizando y colocado dentro del directorio [mupl/loc/](mupl/loc/), por ejemplo: `pt-br.json`. 

Por favor, envía un PR con estos cambios.
