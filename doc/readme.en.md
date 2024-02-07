# mupl - MangaDex Bulk Uploader
Bulk uploads folders and zips (.zip/.cbz) to MangaDex in a quick and easy fashion. 

Read this in other languages: 
[Languages](/readme.md)

## Table of Contents
- [Upload file name format](#file-name-format)
  - [Name format](#name-format)
  - [Name parameters](#name-parameters)
  - [Name parameters](#accepted-image-formats)
- [Config](#config)
  - [User Options](#options)
  - [MangaDex Credentials](#credentials)
  - [Program Paths](#paths)
- [Name to ID File](#name-to-id-map)
  - [Map File Examples](#example)
- [Contribution](#contribution)
- [Translation](#translation)


## File Name Format
#### Name format
`manga_title [lang] - cXXX (vYY) (chapter_title) {publish_date} [group]`

#### Name parameters
- `manga_title` Manga title (same as the key in `name_id_map.json`) or the MangaDex ID.
- `[lang]` Language code in the ISO format. *Omitted for English.*
- `cXXX` Chapter number. *Omit the chapter prefix if the chapter is a oneshot, e.g. `cXXX` > `XXX`.*
- `(vYY)` Chapter volume. *Optional.*
- `(chapter_title)` Chapter title. Use `{question_mark}` in place where there would be a `?`. *Optional.*
- `{publish_date}` Future date of when chapter is released from MangaDex's side. ***MUST** be in the format `YYYY-MM-DDTHH-MM-SS` if included.* *Optional.*
- `[group]` List of group names or IDs. If group names, they must be included in the `name_id_map.json` for the IDs. *Separate multiple groups using `+`.* *Optional.*

#### Folder Format
- `Language`
  - `Work`
    - `Group`
      - `Volume`
        - `Chapter`
          - `Title {data}`
      - `Chapter`
        - `Title {data}`

#### Folder Format Parameters
- `Language` Language code in ISO format. *Required*
- `Work` Manga title (same as the key in `name_id_map.json`) or MangaDex ID.
- `Group` List of group names or IDs. If using group names, they must be included in `name_id_map.json` for the IDs. *Separate multiple groups using `+`.* *Leave as 0 (zero) if there is no group.*
- `Volume` Chapter volume. *Optional.* *Example: v5*
- `Chapter` Chapter number. *For one-shot chapters, set it as 0000 (four zeros)*
- `Title {data}` In *Title*, put the chapter title, and in *{data}*, specify a maximum time of two weeks. *Keep the curly braces {}*

##### Example of {data}
The date can be defined in several different ways.

**{1d}** == In 1 day

**{5h}** == In 5 hours

**{40m}** == In 40 minutes

**{30s}** == In 30 seconds

Or in the common format.
**{2024-01-16 22-00-00}**

You can also combine them.
**{1d 5h 40m 30s}** == In 1 day, 5 hours, 40 minutes, and 30 seconds

You don't need to worry about the order.
**{30s 5h 1d 40m}**

Don't keep the values together; otherwise, it won't work.
**{1d5h40m30s}**

#### Accepted Image formats
- `png`
- `jpg`/`jpeg`
- `gif`
- `webp` *Will be converted to either `png`, `jpg`, or `gif` during the upload process.*

## Config
User changeable settings are available in the `config.json` file. This is also where you put your MangaDex credentials.
Copy and remove the `.example` from `config.json.example` to start using the config file.

*Note: JSON values cannot be empty, hence use (`null`) where a value is meant to be empty, a string (`"username"`) for string values, or a digit (`1`) for number values.*


#### Options
- `number_of_images_upload` Number of images to upload at once. *Default: 10*
- `upload_retry` Attempts to retry image or chapter upload. *Default: 3*
- `ratelimit_time` Time (in seconds) to sleep after API calls. *Default: 2*
- `max_log_days` Days to keep logs. *Default: 30*
- `group_fallback_id` Group ID to use if not found in file or ID map, leave blank to not upload to a group. *Default: null*
- `number_threads`: Number of thread for concurrent image upload. **This can rate limit you.** Threads are limited to the range 1-3 (inclusive). *Default: 3*
- `language`: Language for command line messages. *Default: null*

#### Credentials
***These values cannot be empty, otherwise the uploader will not run.***
- `mangadex_username` MangaDex username.
- `mangadex_password` MangaDex password.
- `client_id` Client ID for the MangaDex API Client.
- `client_secret` Client Secret for the MangaDex API Client.

#### Paths
*These options can be left as is, they do not need to be changed.*
- `name_id_map_file` File name for the name-to-id map. *Default: name_id_map.json*
- `uploads_folder` Directory to get new uploads from. *Default: to_upload*
- `uploaded_files` Directory to move uploaded chapters to. *Default: uploaded*
- `mangadex_api_url` MangaDex API url. *Default: https://api.mangadex.org*
- `mangadex_auth_url` MangaDex Authentication url. *Default: https://auth.mangadex.org/realms/mangadex/protocol/openid-connect*
- `mdauth_path` Local save file for MangaDex login token. *Default: .mdauth*

<details>
  <summary>How to obtain a client ID and secret.</summary>

  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>
<br />


## Name to ID map
The `name_id_map.json` has the follwing format:
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
`manga` and `group` comtain the map of name to ID for the manga to upload to and group to upload to respectively. The name should be the same as the upload file. To avoid potential problems when uploading, try use a name that is lowercase and doesn't have spaces.

Each new name-id pair should be separated by a comma at the end of the line and a colon between the name and ID. The last pair of each map should not have a comma.

#### Example

Take `hyakkano - c025 (v04) [XuN].cbz` as the chapter I want to upload. In my `name_id_map.json`, I would have the key `hyakkano` and the value `efb4278c-a761-406b-9d69-19603c5e4c8b` for the manga ID to upload to. I would also have `XuN` for the group map with the value `b6d57ade-cab7-4be7-b2b8-be68484b3ad3`.

The program would then look through this file for the `hyakkano` key and for the `XuN` key for their assigned ids.

If I have a file named `efb4278c-a761-406b-9d69-19603c5e4c8b [spa] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, the progam would take the manga id directly from the file, the language as Spanish with the code `es`, chapter number as null (oneshot) with no volume, chapter title as `Momi-san` with groups `XuN` (id taken form `name_id_map.json`) and `00e03853-1b96-4f41-9542-c71b8692033b`.


## Contribution
- Make sure there aren't any duplicate issues opened before opening one
- Pull requests are free to be opened if you think it is needed, but please format any code with Python Black (default settings) before doing so.

## Translation
There are two files to translate, this Doc and the [/mupl/loc/en.json](/mupl/loc/en.json) file. 

The translated Doc should be placed in [/doc/](/doc/) with the name `Doc.<>.md` with the ISO language code between the periods, for example: `Doc.pt-br.md`.

The translated json file should be the named `<>.json` with the ISO language code being used and placed inside the directory [/mupl/loc/](/mupl/loc/). 

Please submit a PR with these changes.
