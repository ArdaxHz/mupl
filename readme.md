
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

Images can be named whatever you like as they will be sorted naturally, but images **MUST** be either `png`, `jpg` or `gif`, anything else will not be accepted.

----

Copy the `config.ini.example` file and remove the `.example`. Put the respective details next to the equals sign.
- `GROUP_FALLBACK_ID` will be used if the upload file has no groups, you can leave this blank if you do not wish to upload to any group.
- `NUMBER_OF_IMAGES_UPLOAD` is the number of images to upload at once, a maximum of 10 images can be uploaded at once.
- `UPLOAD_RETRY` is the number of times to retry uploading images or committing (releasing) the chapter.

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

----

## Languages

| Language        | MD Code       | ISO-639 Code  | Language        | MD Code       | ISO-639 Code  |
|:---------------:| ------------- | ------------- |:---------------:| ------------- | ------------- |
| Arabic          | ar            | ara           | Italian         | it            | ita           |
| Bengali         | bd            | ben           | Japanese        | ja            | jpn           |
| Bulgarian       | bg            | bul           | Korean          | ko            | kor           |
| Burmese         | my            | bur           | Lithuanian      | li            | lit           |
| Bengali         | bn            | ben           | Malay           | ms            | may           |
| Catalan         | ca            | cat           | Mongolian       | mn            | mon           |
| Chinese (Simp)  | zh            | chi           | Norwegian       | no            | nor           |
| Chinese (Trad)  | zh-hk         | chi           | Persian         | fa            | per           |
| Czech           | cs            | cze           | Polish          | pl            | pol           |
| Danish          | da            | dan           | Portuguese (Br) | pt-br         | por           |
| Dutch           | nl            | dut           | Portuguese (Pt) | pt            | por           |
| English         | en            | eng           | Romanian        | ro            | rum           |
| Filipino        | tl            | fil           | Russian         | ru            | rus           |
| Finnish         | fi            | fin           | Serbo-Croatian  | sh            | hrv           |
| French          | fr            | fre           | Spanish (Es)    | es            | spa           |
| German          | de            | ger           | Spanish (LATAM) | es-la         | spa           |
| Greek           | el            | gre           | Swedish         | sv            | swe           |
| Hebrew          | he            | heb           | Thai            | th            | tha           |
| Hindi           | hi            | hin           | Turkish         | tr            | tur           |
| Hungarian       | hu            | hun           | Ukrainian       | uk            | ukr           |
| Indonesian      | id            | ind           | Vietnamese      | vi            | vie           |


## Contribution
- Make sure there aren't any duplicate issues opened before opening one
- Pull requests are free to be opened if you think it is needed, but please format any code with Python Black with the default settings before doing so.
