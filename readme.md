
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
