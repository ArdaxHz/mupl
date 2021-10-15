
## Only accepts zip files. Files to upload must be in a `to_upload` folder.
### Files must be named in the format `series-name_cXXX (vYY)_chapter-title`

- Use `0` for the chapter number if the chapter is a oneshot, e.g. `c0`.
- `(vYY)` can be omitted if the chapter has no volume.
- `chapter-title` can be omitted if the chapter has no title.

Copy the `.env.example` file and remove the `.example`. Put the respective details next to the equals sign.
- You can leave `GROUP_ID` blank if you do not wish to upload to any group.

In the `manga_series.json` file, replace `series1_name` with the `series-name` used in your zip file and `series1_id` with the MangaDex id of the series. You can add more series by adding new lines under `series1_name` following the same format as the `series1_name` line. If adding more lines, each line except the last, must end with a `,`.
