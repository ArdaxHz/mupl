import os
import re
import sys
import json
import time
import shutil
import asyncio
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List

import natsort

from mupl.file_validator import FileProcesser
from mupl.http.client import HTTPClient
from mupl.updater import check_for_update
from mupl.uploader.uploader import ChapterUploader
from mupl.utils.config import config, RATELIMIT_TIME, root_path, VERBOSE, translate_message
import mupl.utils.imagemagick_check as img_check

logger = logging.getLogger("mupl")
height_max = 10000

def cup_images(input_images, output_folder, extension, chapter_tag, allow_ext):
    os.makedirs(output_folder, exist_ok=True)
    output_filename = os.path.join(output_folder, f"%d.{extension}")
    command = ["magick", "convert", "-quality", "100", "-crop", "50000x5000"]
    command += input_images + [output_filename]
    subprocess.run(command, check=True)
    
    for image_file in input_images:
        os.remove(image_file)
        
        count = 1

        output_files = sorted([f for f in os.listdir(output_folder) if f.lower().endswith(tuple(allow_ext))], key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        for filename in output_files:
            base, ext = os.path.splitext(filename)
            new_filename = f"{count:02d}{ext}"
            os.rename(os.path.join(output_folder, filename), os.path.join(output_folder, new_filename))
            count += 1

        output_files = [f for f in os.listdir(output_folder) if f.lower().endswith(tuple(allow_ext))]
        for image in output_files:
            output_pathfile = os.path.join(output_folder, image)
            shutil.move(output_pathfile, chapter_tag)
            
    os.rmdir(output_folder)


def check_images(path, allow_ext):
    image_files = [f for f in os.listdir(path) if f.lower().endswith(tuple(allow_ext))]
    input_images = [os.path.join(path, image) for image in image_files]
    output_folder = os.path.join(path, "temp")
    
    cup = False
    try:
        cup = any(int(subprocess.check_output(["magick", "identify", "-format", "%h", image]).decode("utf-8").strip()) > height_max for image in input_images)
    except:
        pass

    if cup:
        cup_images(input_images, output_folder, "jpg", path, allow_ext)
        
    return


def get_zips_to_upload(names_to_ids: "dict", ImageMagick, allow_ext = ['.png', '.jpg', '.jpeg', '.webp', '.gif']) -> "Optional[List[FileProcesser]]":
    """Get a list of files that end with a zip/cbz extension for uploading."""
    to_upload_folder_path = Path(config["paths"]["uploads_folder"])
    zips_to_upload: "List[FileProcesser]" = []
    zips_invalid_file_name = []
    zips_no_manga_id = []

    for archive in to_upload_folder_path.iterdir():
        
        # Language [1]
        if archive.name.startswith('[') and archive.name.endswith(']'):
            if archive.is_dir():
                
                # Name project [2]
                for title_tag in archive.iterdir():
                    if title_tag.is_dir():
                        
                        # Group scan [3]
                        for group_tag in title_tag.iterdir():
                            if group_tag.is_dir():
                                
                                # Volume [4]
                                for volume_tag in group_tag.iterdir():
                                    if not volume_tag.name.startswith('v'):
                                        continue
                                    
                                    if volume_tag.is_dir():
                                        
                                        # Chapter [5]
                                        for chapter_tag in volume_tag.iterdir():
                                            if chapter_tag.is_dir():
                                                
                                                # Title chapter [6]
                                                if any(name_tag.is_dir() for name_tag in chapter_tag.iterdir()):
                                        
                                                    for name_tag in chapter_tag.iterdir():
                                                        if name_tag.is_dir():
                                                            
                                                            if ImageMagick:
                                                                check_images(name_tag, allow_ext)
                                                            zip_obj = FileProcesser(name_tag, names_to_ids)
                                                            zip_name_process = zip_obj.process_zip_name_extanded()
                                                            
                                                            if zip_name_process:
                                                                if not zip_obj in zips_to_upload:
                                                                    zips_to_upload.append(zip_obj)

                                                            if zip_obj.zip_name_match is None:
                                                                zips_invalid_file_name.append(name_tag)

                                                            if zip_obj.manga_series is None and zip_obj.zip_name_match is not None:
                                                                zips_no_manga_id.append(name_tag)
                                                        
                                                else:
                                                    if ImageMagick:
                                                        check_images(chapter_tag, allow_ext)
                                                    zip_obj = FileProcesser(chapter_tag, names_to_ids)
                                                    zip_name_process = zip_obj.process_zip_name_extanded()
                                                    
                                                    if zip_name_process:
                                                        if not zip_obj in zips_to_upload:
                                                            zips_to_upload.append(zip_obj)

                                                    if zip_obj.zip_name_match is None:
                                                        zips_invalid_file_name.append(chapter_tag)

                                                    if zip_obj.manga_series is None and zip_obj.zip_name_match is not None:
                                                        zips_no_manga_id.append(chapter_tag)
                                
                                # Chapter [4]
                                for chapter_tag in group_tag.iterdir():
                                    if chapter_tag.is_dir():
                                        
                                        if chapter_tag.name.startswith('v'):
                                            continue
                                        
                                        # Title chapter [5]
                                        if any(name_tag.is_dir() for name_tag in chapter_tag.iterdir()):
                                            
                                            for name_tag in chapter_tag.iterdir():
                                                if name_tag.is_dir():
                                                    
                                                    if ImageMagick:
                                                        check_images(name_tag, allow_ext)
                                                    zip_obj = FileProcesser(name_tag, names_to_ids)
                                                    zip_name_process = zip_obj.process_zip_name_extanded()
                                                    
                                                    if zip_name_process:
                                                        if not zip_obj in zips_to_upload:
                                                            zips_to_upload.append(zip_obj)

                                                    if zip_obj.zip_name_match is None:
                                                        zips_invalid_file_name.append(name_tag)

                                                    if zip_obj.manga_series is None and zip_obj.zip_name_match is not None:
                                                        zips_no_manga_id.append(name_tag)
                                            
                                        else:
                                            if ImageMagick:
                                                check_images(chapter_tag, allow_ext)
                                            zip_obj = FileProcesser(chapter_tag, names_to_ids)
                                            zip_name_process = zip_obj.process_zip_name_extanded()
                                            
                                            if zip_name_process:
                                                if not zip_obj in zips_to_upload:
                                                    zips_to_upload.append(zip_obj)

                                            if zip_obj.zip_name_match is None:
                                                zips_invalid_file_name.append(chapter_tag)

                                            if zip_obj.manga_series is None and zip_obj.zip_name_match is not None:
                                                zips_no_manga_id.append(chapter_tag)
    
        
        else:
            zip_obj = FileProcesser(archive, names_to_ids)
            zip_name_process = zip_obj.process_zip_name()
        
        if zip_name_process:
            if not zip_obj in zips_to_upload:
                zips_to_upload.append(zip_obj)

        if zip_obj.zip_name_match is None:
            zips_invalid_file_name.append(archive)

        if zip_obj.manga_series is None and zip_obj.zip_name_match is not None:
            zips_no_manga_id.append(archive)

    # Sort the array to mirror your system's file explorer
    zips_to_upload = natsort.os_sorted(zips_to_upload, key=lambda x: x.to_upload)
    zips_to_upload = natsort.os_sorted(zips_to_upload, key=lambda x: (x.volume_number, x.chapter_number))

    if zips_invalid_file_name:
        logger.warning(
            f"Skipping {len(zips_invalid_file_name)} files as they don't match the FILE_NAME_REGEX pattern: {zips_invalid_file_name}"
        )

    if zips_no_manga_id:
        zips_no_manga_id_skip_message = (
            "Skipping {} files as they have a missing manga id".format(
                len(zips_no_manga_id)
            )
        )
        logger.warning(f"{zips_no_manga_id_skip_message}: {zips_no_manga_id}")
        print(
            "{}, check the logs for the file names.".format(
                zips_no_manga_id_skip_message
            )
        )

    if not zips_to_upload:
        print(translate_message['mulp_text_1'])
        logger.error(f"Exited due to {len(zips_to_upload)} zips not being valid.")
        return

    logger.debug(f"Uploading files: {zips_to_upload}")
    return zips_to_upload


def open_manga_series_map(files_path: "Path") -> "dict":
    """Get the manga-name-to-id map."""
    try:
        with open(
            files_path.joinpath(config["paths"]["name_id_map_file"]),
            "r",
            encoding="utf-8",
        ) as json_file:
            names_to_ids = json.load(json_file)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.exception("Please check your name-to-id file.")
        print(translate_message['mulp_text_2'])
        return {"manga": {}, "group": {}}
    return names_to_ids


def main(threaded: "bool" = True):
    ImageMagick = img_check.setup()
    
    """Run the mupl on each zip."""
    names_to_ids = open_manga_series_map(root_path)
    zips_to_upload = get_zips_to_upload(names_to_ids, ImageMagick)
    if zips_to_upload is None:
        return

    http_client = HTTPClient()
    failed_uploads: "List[Path]" = []

    for index, file_name_obj in enumerate(zips_to_upload, start=1):
        try:
            print(f"\n\n{translate_message['mulp_text_3']} {str(file_name_obj)}\n{'-'*40}")

            uploader_process = ChapterUploader(
                http_client, file_name_obj, names_to_ids, failed_uploads, threaded
            )
            uploader_process.upload()
            if not uploader_process.folder_upload:
                uploader_process.myzip.close()

            http_client.login()

            # Delete to save memory on large amounts of uploads
            del uploader_process

            print(f"{'-'*10}\n{translate_message['mulp_text_4']} {str(file_name_obj)}\n{'-'*10}")
            logger.debug("Sleeping between zip upload.")
            time.sleep(RATELIMIT_TIME * 2)
        except KeyboardInterrupt:
            logger.warning(
                f"Keyboard Interrupt detected during upload of {str(file_name_obj)}"
            )
            print(translate_message['mulp_text_5'])
            try:
                asyncio.get_event_loop().stop()
                asyncio.get_event_loop().close()
                uploader_process.remove_upload_session()
                if not uploader_process.folder_upload:
                    uploader_process.myzip.close()
                del uploader_process
            except UnboundLocalError:
                pass
            else:
                failed_uploads.append(file_name_obj.to_upload)
            break

    if failed_uploads:
        logger.info(f"Failed uploads: {failed_uploads}")
        print(translate_message['mulp_text_6'])
        for fail in failed_uploads:
            prefix = translate_message['mulp_text_7'] if fail.is_dir() else translate_message['mulp_text_8']
            print("{}: {}".format(prefix, fail.name))

    sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Log verbosity.",
    )
    parser.add_argument(
        "--threaded",
        "-t",
        default=True,
        const=False,
        nargs="?",
        help="Upload the images concurrently.",
    )

    vargs = vars(parser.parse_args())

    if vargs["verbose"] == 0:
        logger.setLevel(logging.INFO)
    else:
        VERBOSE = True
        logger.setLevel(logging.DEBUG)

    main(vargs["threaded"])
