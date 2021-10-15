import json
import re
import time
import zipfile
from pathlib import Path

import requests
from dotenv import dotenv_values

chapter_regex = re.compile(r'(?:[c](?:h(?:(?:a)?p(?:ter)?)?)?(?:\.)?(?:\s)?)(\d+(?:\.\d)?)', re.IGNORECASE)
volume_regex = re.compile(r'(?:[v](?:ol(?:ume)?(?:s)?)?(?:\.)?(?:\s)?)(\d+(?:\.\d)?)', re.IGNORECASE)
md_upload_api_url = 'https://api.mangadex.org/upload'


def remove_upload_session(session: requests.Session, upload_session_id: str):
    """Delete the upload session."""
    session.delete(f'{md_upload_api_url}/{upload_session_id}')


def print_error(error_json: requests.Response):
    """Print the errors the site returns."""
    # Api didn't return json object
    try:
        error_json = error_json.json()
    except json.JSONDecodeError:
        print(error_json.status_code)
        return
    # Maybe already a json object
    except AttributeError:
        # Try load as a json object
        try:
            error_json = json.loads(error_json)
        except json.JSONDecodeError:
            print(error_json.status_code)
            return

    # Api response doesn't follow the normal api error format
    try:
        error = [e["detail"] for e in error_json["errors"] if e["detail"] is not None]
        error = ', '.join(error)
        code = [str(e["status"]) for e in error_json["errors"] if e["status"] is not None]
        code = ', '.join(code)

        print(f'Error: {code}, {error}')
    except KeyError:
        print(error_json.status_code)


def print_error_upload_legacy(error_response: requests.Response):
    """The legacy errors array format returned when uploading images."""
    # Maybe the api didn't return a json object
    try:
        error_json = error_response.json()
    except json.JSONDecodeError:
        pass

    # Api error format changed
    try:
        errors = [e["message"] for e in error_json["errors"] if e["message"] is not None]
        print(f'Error', ', '.join(errors))
    except KeyError:
        print_error(error_response)


def process_zip(to_upload: Path, names_to_ids: dict):
    """Get the chapter data from the file name."""

    # Split the file name into the different components
    zip_name = to_upload.name
    zip_name_split = zip_name.split('_')

    series = zip_name_split[0]
    try:
        manga_series = names_to_ids[series]
    except KeyError:
        manga_series = None

    chapter_number_match = chapter_regex.search(zip_name_split[1])
    if chapter_number_match:
        chapter_number = chapter_number_match.group(1).lstrip('0')
        # Oneshot chapter
        if chapter_number in ('', '0'):
            chapter_number = None
    else:
        chapter_number = None

    volume_number_match = volume_regex.search(zip_name)
    if volume_number_match:
        volume_number = volume_number_match.group(1).lstrip('0')
    else:
        volume_number = None

    try:
        chapter_title = zip_name_split[2].replace('(question-mark)', '?')
    except IndexError:
        chapter_title = None   

    print(series)
    print(chapter_number)
    print(volume_number)
    print(chapter_title)
    print(manga_series)
    return manga_series, chapter_title, chapter_number, volume_number


def login_to_md(env_values: dict, session: requests.Session):
    """Login to MangaDex using the credentials found in the env file."""
    username = env_values["MANGADEX_USERNAME"]
    password = env_values["MANGADEX_PASSWORD"]
    login_response = session.post('https://api.mangadex.org/auth/login', json={"username": username, "password": password})

    if login_response.status_code != 200:
        print_error(login_response)
        raise Exception("Couldn't login.")

    # Update requests session with headers to always be logged in
    session_token = login_response.json()["token"]["session"]
    session.headers.update({"Authorization": f"Bearer {session_token}"})


def open_manga_series_map(env_values: dict, files_path: Path):
    """Get the manga-name-to-id map."""
    try:
        with open(files_path.joinpath(env_values["MANGA_NAME_ID_FILE_NAME"]).with_suffix('.json'), 'r') as json_file:
            names_to_ids = json.load(json_file)
    except FileNotFoundError:
        raise Exception(f"The manga name-to-id json file couldn't be found.")
    except json.JSONDecodeError:
        raise Exception(f"The manga name-to-id json file is corrupted.")
    return names_to_ids


def load_env_file(root_path: Path):
    """Read the data from the env if it exists."""
    env_file_path = root_path.joinpath('.env')
    if not env_file_path.exists():
        raise Exception(f"Couldn't find env file.")

    env_dict = dotenv_values(env_file_path)
    if env_dict["MANGADEX_USERNAME"] == '' or env_dict["MANGADEX_PASSWORD"] == '':
        raise Exception(f'Missing login details.')

    if env_dict["GROUP_ID"] == '':
        print(f'Group id not found, uploading without a group.')

    return env_dict


if __name__ == "__main__":

    root_path = Path('.')
    to_upload_folder_path = root_path.joinpath('to_upload')
    if not to_upload_folder_path.exists():
        print(f'Uploads folder not found, looking for files in the root directory.')
        to_upload_folder_path = root_path

    uploaded_files_path = root_path.joinpath('uploaded')
    env_values = load_env_file(root_path)

    session = requests.Session()
    login_to_md(env_values, session)

    names_to_ids = open_manga_series_map(env_values, root_path)
    groups = [] if env_values["GROUP_ID"] == '' else [env_values["GROUP_ID"]]

    for to_upload in to_upload_folder_path.iterdir():
        # Only accept zip files
        if to_upload.suffix in ('.zip', '.cbz'):
            image_ids = []
            failed_image_upload = False
            manga_series, chapter_title, chapter_number, volume_number = process_zip(to_upload, names_to_ids)

            if manga_series is None:
                print(f'Skipped {to_upload}, no manga id found.')
                continue

            # Remove any exising upload sessions to not error out
            existing_session = session.get(f'{md_upload_api_url}')
            if existing_session.status_code == 200:
                remove_upload_session(session, existing_session.json()["data"]["id"])

            # Start the upload session
            upload_session_response = session.post(f'{md_upload_api_url}/begin', json={"manga": manga_series, "groups": groups})
            if upload_session_response.status_code != 200:
                print_error(upload_session_response)
                print(f'Error creating draft for {to_upload}.')
                continue

            upload_session_id = upload_session_response.json()["data"]["id"]
            print(f'Created upload session: {upload_session_id}, {to_upload}')

            # Open zip file and read the data
            with zipfile.ZipFile(to_upload) as myzip:
                info_list = myzip.infolist()
                # Remove any directories from the zip info array
                info_list_dir_removed = list(reversed([image for image in reversed(info_list.copy()) if not image.is_dir()]))
                # Separate the image array into smaller arrays of 5 images
                info_list_separate = [info_list_dir_removed[l:l + 5] for l in range(0, len(info_list_dir_removed), 5)]

                for array_index, images in enumerate(info_list_separate, start=1):
                    files = {}
                    # Read the image data and add to files dict
                    for image_index, image in enumerate(images, start=1):
                        image_filename = str(Path(image.filename).stem)
                        with myzip.open(image) as myfile:
                            files.update({f'{image_filename}': myfile.read()})

                    # Upload the images
                    image_upload_response = session.post(f'{md_upload_api_url}/{upload_session_id}', files=files)
                    if image_upload_response.status_code != 200:
                        print(image_upload_response.status_code)
                        print_error_upload_legacy(image_upload_response)
                        failed_image_upload = True
                        break

                    # Some images returned errors
                    uploaded_image_data = image_upload_response.json()
                    if uploaded_image_data["errors"]:
                        print_error_upload_legacy(image_upload_response)

                    # Add successful image uploads to the image ids array
                    for uploaded_image in uploaded_image_data["data"]:
                        image_ids.append(uploaded_image["id"])
                        uploaded_image_attributes = uploaded_image["attributes"]
                        print(f'Success: Uploaded page {uploaded_image_attributes["originalFileName"]}, size: {uploaded_image_attributes["fileSize"]} bytes.')

                    if failed_image_upload:
                        break

                    # Rate limit
                    if array_index % 5 == 0:
                        time.sleep(3)

            # Skip chapter upload and delete upload session
            if failed_image_upload:
                print(f'Deleting draft due to failed image upload: {upload_session_id}, {to_upload}.')
                remove_upload_session(session, upload_session_id)
                continue

            # Try to commit the chapter 3 times
            commit_retries = 0
            succesful_upload = False
            while commit_retries < 3:
                chapter_commit_response = session.post(f'{md_upload_api_url}/{upload_session_id}/commit',
                    json={"chapterDraft":
                        {"volume": volume_number, "chapter": chapter_number, "title": chapter_title, "translatedLanguage": "en"}, "pageOrder": image_ids
                    })

                if chapter_commit_response.status_code == 200:
                    succesful_upload = True
                    succesful_upload_id = chapter_commit_response.json()["data"]["id"]
                    print(f'Succesfully uploaded: {succesful_upload_id}, {to_upload}')

                    # Move the uploaded zips to a different folder
                    uploaded_files_path.mkdir(parents=True, exist_ok=True)
                    to_upload_name = to_upload.name
                    to_upload_extension = to_upload.suffix
                    to_upload.rename(uploaded_files_path.joinpath(to_upload_name).with_suffix(to_upload_extension))
                    break

                print(f'Failed to commit {to_upload}, trying again.')
                commit_retries += 1
                time.sleep(1)

            if not succesful_upload:
                print(f'Failed to commit {to_upload}, removing upload draft.')
                remove_upload_session(session, upload_session_id)

            time.sleep(3)
