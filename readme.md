# mupl - MangaDex Bulk Uploader
Bulk uploads folders and archives (.zip/.cbz) to MangaDex in a quick and easy way. 

Read this in other languages:  
[Português (Brasil)](doc/readme.pt-br.md)\
[Español (LATAM)](doc/readme.es-la.md)\
[Français](doc/readme.fr.md)\
[Euskara](doc/readme.eu.md)\
[Tiếng Việt](doc/readme.vi.md)

***There will be a release for each language, with English included in each one. To download all the languages, download the source files zip.***

## Table of Contents
- [How to use](#usage)
  - [As a dependency](#dependency)
  - [Downloading](#downloading)
  - [Installing](#installing)
  - [Running](#running)
  - [Updating](#updating)
  - [Command Line Arguments](#command-line-arguments)
- [Upload file name structure](#file-name-structure)
  - [Name convention](#name-convention)
  - [Name parameters](#name-parameters)
    - [Chapter title replacement characters](#chapter-title-replacement-characters)
  - [Accepted Image Formats](#accepted-image-formats)
  - [Image size](#image-size)
    - [Image Splitting](#image-splitting)
    - [Image Combining](#image-combining)
- [Config](#config)
  - [User Options](#options)
  - [MangaDex Credentials](#credentials)
  - [Program Paths](#paths)
- [Name to ID File](#name-to-id-map)
  - [Map File Examples](#example)
- [Contribution](#contribution)
- [Translation](#translation)


## Usage
### This uploader is tested for Python 3.10+.

#### This uploader can be run from the command line directly, or used as a dependency in other scripts.

### Dependency
To use this uploader in other scripts, install the latest version through pypi `pip install muplr`

```python
from mupl import Mupl
from datetime import datetime
from pathlib import Path

# Initialize Mupl
# Most parameters have sensible defaults, provide credentials as needed.
# Home path on Unix/Mac is /Users/<>/mupl, on Windows it's C:\Users\<>\mupl.

mupl = Mupl(
    mangadex_username="your_username",             # Your MangaDex username
    mangadex_password="your_password",             # Your MangaDex password
    client_id="your_client_id",                    # Your MangaDex API client ID (optional if using username/password)
    client_secret="your_client_secret",            # Your MangaDex API client secret (optional if using username/password)
    # --- Optional Parameters ---       
    # move_files=True,                             # Move files from upload dir to 'uploaded_files' dir after success
    # verbose_level=0,                             # Logging level (0=INFO, 1=DEBUG)
    # number_of_images_upload=10,                  # Number of images per upload session commit request
    # upload_retry=3,                              # Number of retries for failed image uploads
    # ratelimit_time=2,                            # Seconds to wait between API calls
    # logs_dir_path=None,                          # Directory where to store logs. Defaults to home path. Will create 'logs' folder in this directory.
    # max_log_days=30,                             # Days to keep log files
    # group_fallback_id=None,                      # Default group UUID if not found in filename/map
    # number_threads=3,                            # Number of threads for concurrent image uploads
    # language="en",                               # Language code for mupl localisation
    # name_id_map_filename="name_id_map.json",     # Filename for manga/group name-to-ID mapping (relative to home_path or absolute path), not required for single_chapter uploads
    # uploaded_dir_path="uploaded",                # Directory name/path for successfully uploaded files (relative to home_path or absolute path to folder)
    # mangadex_api_url="https://api.mangadex.org", # Base URL for MangaDex API
    # mangadex_auth_url="https://auth.mangadex.org/realms/mangadex/protocol/openid-connect", # Base URL for MangaDex Auth
)

# --- Uploading a Directory ---
# Directory path containing chapter archives (zip/cbz) or folders named according to convention.
# See File Naming Convention section below.
upload_directory_path = Path("path/to/your/chapters_folder") # or "path/to/your/chapters_folder"

failed_uploads_list = mupl.upload_directory(
    upload_dir_path=upload_directory_path,
    # --- Optional Keyword Arguments for upload_directory ---
    # widestrip=False, # Mark chapters as widestrip format
    # combine=False    # Combine small images vertically
)

# Returns:
# 'None' if no valid files are found, otherwise a pathlib objects list of failed uploads is returned.
# If the returned list is empty, there were no failed uploads.

# --- Uploading a Single Chapter ---
# Provide metadata explicitly for a single chapter file or folder.
chapter_file_or_folder_path = Path("path/to/your/chapter.zip") # Or Path("path/to/your/chapter_folder") or a string value "path/to/your/chapter.zip"
manga_uuid = "manga-uuid-here"
group_uuids = ["group-uuid-1", "group-uuid-2"] # List of group UUIDs

upload_successful = mupl.upload_chapter(
    file_path=chapter_file_or_folder_path,
    manga_id=manga_uuid,
    group_ids=group_uuids,
    # --- Optional Keyword Arguments for upload_chapter ---
    # language="en",                        # Chapter language code
    # oneshot=False,                        # Mark as oneshot (True) or regular chapter (False)
    # chapter_number="10",                  # Chapter number (e.g., "10", "10.5"). Ignored if oneshot=True.
    # volume_number="2",                    # Volume number (optional)
    # chapter_title="Chapter Title Here",   # Chapter title (optional)
    # publish_date=None,                    # datetime object for scheduled publishing (optional)
    # widestrip=False,                      # Mark chapter as widestrip format
    # combine=False                         # Combine small images vertically
)

# Returns:
# 'True' if upload was successful, otherwise 'False'.

print(f"Failed directory uploads: {failed_uploads_list}")
print(f"Single chapter upload successful: {upload_successful}")
```


### Downloading
Download the [latest version](https://github.com/ArdaxHz/mupl/releases/latest) from the releases page.

Extract the archive to a folder, and open a new terminal window. On the terminal, navigate to the folder created using `cd "<path_to_folder>"`.

### Installing

Before running the uploader, you will need to install the required modules. 
To install the modules, run the command `pip install -r requirements.txt`, use `pip3` if on mac or linux instead of `pip`.

In the folder you extracted the archive to, create the `to_upload` and `uploaded` folders.

### Running

To run the uploader, in the terminal window, use `python mupl.py` to start the uploader. Use `python3` instead if on mac or linux.

### Updating

The updater will automatically check at the start of the program if there is a new version available on the releases page. If there is a new version, it will prompt you to update.

If you want to disable the updater, you can add the `--update` flag to the command line arguments. For example: `python mupl.py --update`.

### Command Line Arguments
There are command line arguments that can be added after the main command to change the behaviour of the program, for example: `python mupl.py -t`.

##### Options:
- `--update` `-u` Don't check for a new update at the start of the program.
- `--verbose` `-v` Make the command line messages and logs more verbose.
- `--threaded` `-t` Run the threaded uploader. *Default: False*
- `--combine` `-c` Combine images that are smaller than or equal to 128px with the previous image. *Default: False*
- `--widestrip` `-w` Splits images over 10000px wide into multiple, smaller images. *Default: False*

## File Name Structure
#### Name convention
`manga_title [lang] - cXXX (vYY) (chapter_title) {publish_date} [group]`

#### Name parameters
- `manga_title` Manga title (same as the key in `name_id_map.json`) or the MangaDex ID.
- `[lang]` Language code in the ISO format. *Omitted for English.*
- `cXXX` Chapter number. *Omit the chapter prefix if the chapter is a oneshot, e.g. `cXXX` > `XXX`.*
- `(vYY)` Chapter volume. *Optional.*
- `(chapter_title)` Chapter title. See [Chapter title replacement characters](#chapter-title-replacement-characters) for special characters. *Optional.*
- `{publish_date}` Future date of when chapter is released from MangaDex's side. ***MUST** be in the format `YYYY-MM-DDTHH-MM-SS` if included.* *Optional.*
- `[group]` List of group names or IDs. If group names, they must be included in the `name_id_map.json` for the IDs. *Separate multiple groups using `+`.* *Optional.*

##### Chapter title replacement characters
- `{asterisk}` `*` *`{asterisk}` will be replaced with `*` during the upload process.*
- `{backslash}` `\` *`{backslash}` will be replaced with `\` during the upload process.*
- `{slash}` `/` *`{slash}` will be replaced with `/` during the upload process.*
- `{colon}` `:` *`{colon}` will be replaced with `:` during the upload process.*
- `{greater_than}` `>` *`{greater_than}` will be replaced with `>` during the upload process.*
- `{less_than}` `<` *`{less_than}` will be replaced with `<` during the upload process.*
- `{question_mark}` `?` *`{question_mark}` will be replaced with `?` during the upload process.*
- `{quote}` `"` *`{quote}` will be replaced with `"` during the upload process.*
- `{pipe}` `|` *`{pipe}` will be replaced with `|` during the upload process.*

#### Accepted Image formats
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Will be converted to either `png`, `jpg`, or `gif` during the upload process. This will not change the local file.*

#### Image size
##### Image Splitting
Images cannot exceed `10000px` in width or height. Images over 10000px height will be split as a longstrip image. To split a widestrip image, use the CLI argument `--widestrip` `-w`. 


##### Image Combining
If the `--combine` flag is used, images smaller than or equal to `128px` will be combined with the previous image **IF** they are the same width or height as the previous image. (Depends on if the image is a longstrip or widestrip.)

If the flag is not used or the images are not the same width or height as the previous image, the image **WILL* be skipped.


## Config
User changeable settings are available in the `config.json` file. This is also where you put your MangaDex credentials.
Copy and remove the `.example` from `config.json.example` to start using the config file.

*Note: JSON values cannot be empty, and the type of value matters*
- Use (`null`) where a value is meant to be empty
- Text should be in quotation marks (`"username"`)
- Numbers are numbers by themselves (`1.1`)


#### Options
- `number_of_images_upload` Number of images to upload at once. *Default: `10`*
- `upload_retry` Attempts to retry image or chapter upload. *Default: `3`*
- `ratelimit_time` Time (in seconds) to sleep after API calls. *Default: `2`*
- `max_log_days` Days to keep logs. *Default: `30`*
- `group_fallback_id` Group ID to use if not found in file or ID map, leave blank to not upload to a group. *Default: `null`*
- `number_threads`: Number of thread for concurrent image upload. **This can rate limit you.** Threads are limited to the range 1-3 (inclusive). *Default: `3`*
- `language`: Language for command line messages. *Default: `en`*

#### Credentials
***These values cannot be empty, otherwise the uploader will not run.***
- `mangadex_username` MangaDex username.
- `mangadex_password` MangaDex password.
- `client_id` Client ID for the MangaDex API Client.
- `client_secret` Client Secret for the MangaDex API Client.

#### Paths
*These options can be left as is, they do not need to be changed.*
- `name_id_map_file` File name for the name-to-id map. *Default: `name_id_map.json`*
- `uploads_folder` Directory to get new uploads from. *Default: `to_upload`*
- `uploaded_files` Directory to move uploaded chapters to. *Default: `uploaded`*
- `mangadex_api_url` MangaDex API url. *Default: `https://api.mangadex.org`*
- `mangadex_auth_url` MangaDex Authentication url. *Default: `https://auth.mangadex.org/realms/mangadex/protocol/openid-connect`*
- `mdauth_path` Local save file for MangaDex login token. *Default: `.mdauth`*

<details>
  <summary>How to obtain a client ID and secret.</summary>

  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />


## Name to ID map
The `name_id_map.json` has the following format:
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
`manga` and `group` contain the map of name to ID for the manga to upload to and group to upload to respectively. The name should be the same as the upload file. To avoid potential problems when uploading, try use a name that is lowercase and doesn't have spaces.

Each new name-id pair should be separated by a comma at the end of the line and a colon between the name and ID. The last pair of each map should not have a comma.

#### Example

Take `hyakkano - c025 (v04) [XuN].cbz` as the chapter I want to upload. In my `name_id_map.json`, I would have the key `hyakkano` and the value `efb4278c-a761-406b-9d69-19603c5e4c8b` for the manga ID to upload to. I would also have `XuN` for the group map with the value `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

The uploader would then look through this file for the `hyakkano` key and for the `XuN` key for their assigned ids.

If I have a file named `efb4278c-a761-406b-9d69-19603c5e4c8b [es] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, the uploader would take the manga id directly from the file, the language as Spanish with the code `es`, chapter number as null (oneshot) with no volume, chapter title as `Momi-san` with groups `XuN` (id taken form `name_id_map.json`) and `00e03853-1b96-4f41-9542-c71b8692033b`.


## Contribution
- Make sure there aren't any duplicate issues opened before opening one.
- Pull requests are free to be opened if you think it is needed, but please format any code with Python Black (default settings) before doing so.

### Translation
There are two files to translate, this readme and the [mupl/loc/en.json](mupl/loc/en.json) file.

- The translated README should be placed in [doc/](doc/) with the name `readme.<>.md` with the ISO language code between the periods, for example: `readme.pt-br.md`. Update your readme to link back to this readme under the "Read this in other languages" list.
- The translated json file should be named `<>.json` with the ISO language code being used and placed inside the directory [mupl/loc/](mupl/loc/), for example: `pt-br.json`. 

After you have translated these files, update this readme with the link to your translated readme. Please submit a PR with these changes.
