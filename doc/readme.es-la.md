# mupl - MangaDex Bulk Uploader
Sube carpetas y archivos zip (.zip/.cbz) a MangaDex de forma rápida y sencilla.

Lee esto en otros lenguajes: 
[English](/readme.md)

## Tabla de contenidos
- [Cómo usar](#cómo-usar)
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


### Descargar
Descarga la [última versión]((https://github.com/ArdaxHz/mupl/releases/latest)) desde la sección de releases.

Descomprime el archivo a una carpeta y abre una nueva terminal (bash, powershell, cmd). Navega a la carpeta creada usando `cd <direccion_de_la_carpeta>`

### Instalar
Antes de ejecutar el programa, necesitarás instalar los módulos necesarios.
Para instalar dichos módulos, ejecuta el comando `pip install -r requirements.txt`, usa `pip3` si usas Mac o Linux en vez de `pip`.

En la carpeta donde extraiste los archivos del programa, crea una carpeta llamada `to_upload` y `uploaded`.

### Ejecutar
Para ejecutar el programa, en la terminal (bash, powershell, cmd) escribe `python mupl.py`. Usa `python3` en vez de `python` si usas Mac o Linux

### Actualizaciones
El programa se actualizará automaticamente al iniciarlo si hay una nueva versión disponible. De este ser el caso se te preguntará si deseas actualizar.

En cambio, puedes desactivar las actualizaciones automaticas agregando `--update` al momento de ejecutar el programa, por ejemplo: `python mupl.py --update`.

### Argumentos de linea de comandos
Hay argumentos que se pueden agregar al comando principal para cambiar el comportamiento del programa, por ejemplo: `python mupl.py -t`

##### Opciones:
- `--update` `-u` El programa no revisará nuevas versiones disponibles al iniciar.
- `--verbose` `-v` Hace que los mensajes de la línea de comandos y los registros sean más detallados.
- `--threaded` `-t` Ejecuta el subidor multihilo. *Default: False*
- `--combine` `c` Combina la imagen cuya resolución es igual o más pequeña a 128px con la imagen anterior. *Default: False*

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

#### Tipos de imagen aceptados
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Serán convertidos automáticamente a `png`, `jpg` o `gif` durante el proceso de subida.*

#### Tamaño de imagenes
##### Separar imagenes
Las imagenes no pueden exceder los `10000px` de altura y ancho. Para separar las imagenes en partes que no excedan dicho limite, la ID del manga deberá estar en la lista de IDs longstrip o widestrip en el mapa de IDs, como se muestra [abajo](#mapa-de-nombre-a-id)

Si la ID no está, la imagen no será separada y el programa se la saltará.

##### Combinar imagenes
Si se está usando la opción `--combine`, las imagenes cuya resolución sean igual o más pequeña a 128px se combinarán con la imagen anterior **SOLO SI** la imagen anterior tiene la misma resolución. (Esto depende de si la imagen es longstrip o widestrip).

Si no se usa esta opción o si las imagenes no son de la misma resolución, el programa se la saltará.

## Configuración
Las opciones modificables por el usuario están disponibles en el archivo `config.json`. Aquí también es donde pones tus credenciales de tu cuenta de MangaDex.
Copia y elimina el `.example` del archivo `config.json.example` para empezar a usar el archivo de configuracion.

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
***Estos valores no pueden estar vacíos, ya que de lo contrario el programa no funcionará***
- `mangadex_username` Nombre de usuario de tu cuenta en MangaDex.
- `mangadex_password` Contraseña de tu cuenta en MangaDex.
- `client_id` ID de cliente para la API de MangaDex.
- `client_secret` Secret del cliente de la API de MangaDex.

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
    },
    "formats": {
        "longstrip": ["efb4278c-a761-406b-9d69-19603c5e4c8b"],
        "widestrip": ["69b4df2d-5ca3-4e58-91bd-74827629dcce"]
    }
}
```
`manga` y `group` contienen el mapa de nombre a id para el manga a subir y el grupo al que le corresponde, respectivamente. Los nombres deben ser los mismos que pondrás en el archivo. Para evitar problemas al subir, es recomendable que los nombres estén en minúsculas, no tengan espacios, ni caracteres especiales.

Cada nuevo par de nombre a id debe ser separado por una coma al final de la linea y tener un dos puntos entre el nombre y la ID. El ultimo par de cada mapa no deberá tener una coma.

`formats` contiene una lista de IDs para los formatos de longstrip (imagen larga o cascada) o widestrip (imagen ancha). Pueden haber multiples IDs en cada lista, pero no deben de haber IDs duplicadas.

#### Ejemplo

Tomando de ejemplo `hyakkano - c025 (v04) [XuN].cbz` como el capítulo el cual quiero subir. En mi archivo `name_id_map.json`, tendré el valor `hyakkano` y la ID `efb4278c-a761-406b-9d69-19603c5e4c8b` como la ID del manga al que quiero subir. También tengo `XuN` como el grupo, con su valor `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

El programa entonces leerá el valor de `hyakkano` y el de `XuN`, así obteniendo las IDs que les corresponden.

Si tengo un archivo llamado `efb4278c-a761-406b-9d69-19603c5e4c8b [es] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, el programa tomará la ID del manga directamente del archivo, el lenguaje será español, usando el código ISO `es`, el número de capítulo será null (oneshot) y no tendrá volumen; tendrá como título `Momi-san` y será asignado a los grupos `XuN` (id tomada del archivo `name_id_map.json`) y el grupo con la ID `00e03853-1b96-4f41-9542-c71b8692033b`.


## Contribuir
- Asegúrate de que no hay problemas duplicados antes de abrir uno.
- Puedes abrir pull requests si crees que es necesario, pero por favor formatea cualquier código con Python Black (configuración por defecto) antes de hacerlo.

## Traducción
Hay dos archivos para traducir, este readme y el archivo [mupl/loc/en.json](mupl/loc/en.json).

- El README traducido debe colocarse en [doc](doc/) con el nombre `readme.<>.md` con el código de idioma ISO entre los puntos, por ejemplo: `readme.pt-br.md`.
- El archivo JSON traducido debe tener el nombre `<>.json` con el código de idioma ISO que se esté utilizando y colocado dentro del directorio [mupl/loc/](mupl/loc/), por ejemplo: `pt-br.json`. 

Por favor, envía un PR con estos cambios.
