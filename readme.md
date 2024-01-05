
## Accepts zip files and folders. Files and folders to upload must be in a `to_upload` folder. Code is tested for Python 3.9.
### File names **MUST** be in the format `manga_title [lang] - cXXX (vYY) (chapter_title) {publish_date} [group]`
#### To stop check for program update, add the `--update` or `-u` command line argument.

----

- `manga_title` can either be a key to be used in the `name_id_map.json` or the manga id.
- `[lang]` is omitted for English. MangaDex uses the ISO-639-2 code, the language will not be validated client-side, but is left for the MD API to validate. 
- Omit the chapter prefix if the chapter is a oneshot, e.g. `cXXX` > `XXX`.
- `(vYY)` can be omitted if the chapter has no volume.
- `(chapter_title)` can be omitted if the chapter has no title. Use `{question_mark}` in place where there would be a `?`.
- `{publish_date}` can be omitted and **MUST** be in the format `YYYY-MM-DDTHH-MM-SS[+0000]` if included.
- `[group]` can be a list of groups. Separate each separate group with a `+`. Groups can be a key for the `name_id_map.json` file or the group ids.

Images can be named whatever you like as they will be sorted naturally, but they **MUST** be in one of the following formats: `png`, `jpg`, `gif` or `webp`. Anything else will not be accepted. 

*Note: webp is not supported by MangaDex; as such, it will be automatically converted to one of the following formats during the uploading process: `png`, `jpg`, or `gif`.*

----

# config.json
Copy the `config.json.example` file and remove the `.example`. Put the respective details next to the colon.

*JSON values cannot be empty, use `null` where a value is meant to be empty, a string `"username"` for string values, or a digit `1` for number values.*


## Options
- `number_of_images_upload`: Number of images to upload at once, 10 maximum at once.
- `upload_retry`: Attempts to retry image or chapter upload.
- `ratelimit_time`: Time (in seconds) to sleep after API calls.
- `max_log_days`: Number of days to keep logs.
- `group_fallback_id`: Group ID to use if not found in file or ID map, leave blank to not upload to a group.
- `number_threads`: Number of thread for concurrent image upload. ***This can rate limit you.*** Threads are limited to the range 1-3 (inclusive). 
- `language`: Language for command line messages.

## Credentials
- `mangadex_username`: MangaDex username.
- `mangadex_password`: MangaDex password.
- `client_id`: Client ID for the MangaDex API Client.
- `client_secret`: Client Secret for the MangaDex API Client.

<details>
  <summary>How to obtain a client ID and secret.</summary>

  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_1.png?raw=true)
  ![a screenshot of the mangadex-mass-uploader](https://github.com/Xnot/mangadex-mass-uploader/blob/main/assets/usage_2.png?raw=true)
</details>

In the `name_id_map.json` file, replace `series1_name` with the `manga_title` used in your zip file and `series1_id` with the MangaDex id of the series. You can add more series by adding new lines under `series1_name` following the same format as the `series1_name` line. If adding more lines, each line except the last, must end with a `,`. You can do the same for the group names and ids.

----

## Examples
Take `takamine - c025 (v04) [XuN].cbz` as the chapter I want to upload. In my `name_id_map.json`, I would have 
```
{
    "manga": {
        "takamine": "46748d60-9b15-4647-8250-de0926b20268"
    },
    "group": {
        "XuN": "b6d57ade-cab7-4be7-b2b8-be68484b3ad3"
}
```
The program would then look through this file for the `takamine` key and for the `XuN` key for their assigned ids.

If I have a file named `efb4278c-a761-406b-9d69-19603c5e4c8b [spa] - 000 (Momi-san) [XuN+00e03853-1b96-4f41-9542-c71b8692033b]`, the progam would take the manga id directly from the file, the language as Spanish with the code `es`, chapter number Oneshot and no volume number, chapter title as `Momi-san` with groups `XuN` (id taken form `name_id_map.json`) and `00e03853-1b96-4f41-9542-c71b8692033b`.


## Contribution
- Make sure there aren't any duplicate issues opened before opening one
- Pull requests are free to be opened if you think it is needed, but please format any code with Python Black with the default settings before doing so.
