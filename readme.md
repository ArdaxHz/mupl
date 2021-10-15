
## Only accepts zip files. Files to upload must be in a `to_upload` folder.
### Files must be named in the format `manga_title [lang] - cXXX (vYY) (chapter_title) [group]`

- `manga_title` can either be a key to be used in the `name_id_map.json` or the manga id.
- `[lang]` is omitted for English. Use the languages table at the bottom of this page to find out which language code to use for MangaDex. 
- Omit the chapter prefix if the chapter is a oneshot, e.g. `cXXX` > `XXX`.
- `(vYY)` can be omitted if the chapter has no volume.
- `(chapter_title)` can be omitted if the chapter has no title. Use `<question_mark>` in place where there would be a `?`.
- `[group]` can be a list of groups. Separate each separate group with a `||`. Groups can be a key for the `name_id_map.json` file or the group ids.


Copy the `.env.example` file and remove the `.example`. Put the respective details next to the equals sign.
- `GROUP_FALLBACK_ID` will be used if the upload file has no groups, you can leave this blank if you do not wish to upload to any group.

In the `name_id_map.json` file, replace `series1_name` with the `manga_title` used in your zip file and `series1_id` with the MangaDex id of the series. You can add more series by adding new lines under `series1_name` following the same format as the `series1_name` line. If adding more lines, each line except the last, must end with a `,`. You can do the same for the group names and ids.


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
The progam would then look into this file for the `takamine` key and for the `XuN` key for their ids and would use ids assigned to these keys.

Or if I have a file named `efb4278c-a761-406b-9d69-19603c5e4c8b [spa] - 000 (Momi-san) [XuN ||  00e03853-1b96-4f41-9542-c71b8692033b ]`, the progam would take the manga id directly from the file, the language as Spanish with the code `es`, chapter number Oneshot and no volume number, chapter title as `Momi-san` with groups `XuN` (id taken form `name_id_map.json`) and `00e03853-1b96-4f41-9542-c71b8692033b`.
