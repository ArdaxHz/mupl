import json
import re
import time
import zipfile
from pathlib import Path

import requests
from dotenv import dotenv_values

uuid_regex = re.compile(r'[0-9a-fA-F]{8}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{4}\-[0-9a-fA-F]{12}')
file_name_regex = re.compile(r'^((?:\[(?P<artist>.+?)\])\s)?(?P<title>.+?)(?:\s\[(?P<language>[a-zA-Z]+)\])?\s-\s(?P<prefix>(?:[c](?:h(?:(?:a)?p(?:ter)?)?)?(?:\.)?)(?:\s)?)?(?P<chapter>\d+(?:\.\d)?)(?:\s\((?:[v](?:ol(?:ume)?(?:s)?)?(?:\.)?(?:\s)?)(?P<volume>\d+(?:\.\d)?)\))?\s?(?:\((?P<chapter_title>.+)\))?\s?(?:\[(?P<group>.+)\])(?:\{(?:v)(?P<version>\d)\})?(?:\.(?P<extension>zip|cbz))?$', re.IGNORECASE)
languages = [{"english":"English","md":"en","iso":"eng"},{"english":"Japanese","md":"ja","iso":"jpn"},{"english":"Polish","md":"pl","iso":"pol"},{"english":"Serbo-Croatian","md":"sh","iso":"hrv"},{"english":"Dutch","md":"nl","iso":"dut"},{"english":"Italian","md":"it","iso":"ita"},{"english":"Russian","md":"ru","iso":"rus"},{"english":"German","md":"de","iso":"ger"},{"english":"Hungarian","md":"hu","iso":"hun"},{"english":"French","md":"fr","iso":"fre"},{"english":"Finnish","md":"fi","iso":"fin"},{"english":"Vietnamese","md":"vi","iso":"vie"},{"english":"Greek","md":"el","iso":"gre"},{"english":"Bulgarian","md":"bg","iso":"bul"},{"english":"Spanish (Es)","md":"es","iso":"spa"},{"english":"Portuguese (Br)","md":"pt-br","iso":"por"},{"english":"Portuguese (Pt)","md":"pt","iso":"por"},{"english":"Swedish","md":"sv","iso":"swe"},{"english":"Arabic","md":"ar","iso":"ara"},{"english":"Danish","md":"da","iso":"dan"},{"english":"Chinese (Simp)","md":"zh","iso":"chi"},{"english":"Bengali","md":"bn","iso":"ben"},{"english":"Romanian","md":"ro","iso":"rum"},{"english":"Czech","md":"cs","iso":"cze"},{"english":"Mongolian","md":"mn","iso":"mon"},{"english":"Turkish","md":"tr","iso":"tur"},{"english":"Indonesian","md":"id","iso":"ind"},{"english":"Korean","md":"ko","iso":"kor"},{"english":"Spanish (LATAM)","md":"es-la","iso":"spa"},{"english":"Persian","md":"fa","iso":"per"},{"english":"Malay","md":"ms","iso":"may"},{"english":"Thai","md":"th","iso":"tha"},{"english":"Catalan","md":"ca","iso":"cat"},{"english":"Filipino","md":"tl","iso":"fil"},{"english":"Chinese (Trad)","md":"zh-hk","iso":"chi"},{"english":"Ukrainian","md":"uk","iso":"ukr"},{"english":"Burmese","md":"my","iso":"bur"},{"english":"Lithuanian","md":"lt","iso":"lit"},{"english":"Hebrew","md":"he","iso":"heb"},{"english":"Hindi","md":"hi","iso":"hin"},{"english":"Norwegian","md":"no","iso":"nor"},{"english":"Other","md":"NULL","iso":"NULL"}]
md_upload_api_url = 'https://api.mangadex.org/upload'


def get_lang_md(language: str) -> str:
    """Convert the inputted language into the format MangaDex uses

    Args:
        language (str): Can be the full language name, ISO 639-2 or ISO 639-3 codes.

    Returns:
        str: ISO 639-2 code, which MangaDex uses for languages.
    """

    if language is None:
        return "en"
    elif len(language) < 2:
        print('Not a valid language option.')
        return
    elif re.match(r'^[a-zA-Z\-]{2,5}$', language):
        return language
    elif len(language) == 3:
        available_langs = [l["md"] for l in languages if l["iso"] == language]

        if available_langs:
            return available_langs[0]
        return "NULL"
    else:
        languages_match = [l for l in languages if language.lower() in l["english"].lower()]

        if len(languages_match) > 1:
            print("Found multiple matching languages, please choose the language you want to download from the following options.")

            for count, item in enumerate(languages_match, start=1):
                print(f'{count}: {item["english"]}')

            try:
                lang = int(input(f'Choose a number matching the position of the language: '))
            except ValueError:
                print("That's not a number.")
                return

            if lang not in range(1, (len(languages_match) + 1)):
                print('Not a valid language option.')
                return

            lang_to_use = languages_match[(lang - 1)]
            return lang_to_use["md"]

        return languages_match[0]["md"]


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
    zip_name_match = file_name_regex.match(to_upload.name)
    if not zip_name_match:
        print(f'{to_upload.name} not in the correct naming format, skipping.')
        return

    series = zip_name_match.group("title")
    if not uuid_regex.match(series):
        try:
            manga_series = names_to_ids["manga"].get(series, None)
        except KeyError:
            manga_series = None

    language = get_lang_md(zip_name_match.group("language"))

    chapter_number = zip_name_match.group("chapter")
    if chapter_number is not None:
        chapter_number = chapter_number.lstrip('0')
        if len(chapter_number) == 0:
            chapter_number = '0'
    
    if zip_name_match.group("prefix") is None:
        chapter_number = None

    volume_number = zip_name_match.group("volume")
    if volume_number is not None:
        volume_number = volume_number.lstrip('0')
        if len(volume_number) == 0:
            volume_number = '0'

    chapter_title = zip_name_match.group("chapter_title")
    if chapter_title is not None:
        chapter_title = chapter_title

    groups = []
    groups_match = zip_name_match.group("group")
    if groups_match is not None:
        groups_array = groups_match.split('||')
        groups_array = [g.strip() for g in groups_array]

        for group in groups_array:
            if not uuid_regex.match(group):
                try:
                    group_id = names_to_ids["group"].get(group, None)
                except KeyError:
                    group_id = None
                if group_id is not None:
                    groups.append(group_id)
            else:
                groups.append(group)

    print(series)
    print(language)
    print(chapter_number)
    print(volume_number)
    print(chapter_title)
    print(manga_series)
    print(groups)
    return (manga_series, language, chapter_number, volume_number, groups, chapter_title)


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
        with open(files_path.joinpath(env_values["NAME_ID_MAP_FILE"]).with_suffix('.json'), 'r') as json_file:
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

    if env_dict["GROUP_FALLBACK_ID"] == '':
        print(f'Group id not found, uploading without a group.')

    return env_dict


if __name__ == "__main__":

    root_path = Path('.')
    env_values = load_env_file(root_path)
    names_to_ids = open_manga_series_map(env_values, root_path)
    to_upload_folder_path = Path(env_values["UPLOADS_FOLDER"])
    uploaded_files_path = Path(env_values["UPLOADED_FILES"])

    session = requests.Session()
    login_to_md(env_values, session)
    group_fallback = [] if env_values["GROUP_FALLBACK_ID"] == '' else [env_values["GROUP_FALLBACK_ID"]]

    for to_upload in to_upload_folder_path.iterdir():
        zip_name = to_upload.name
        zip_extension = to_upload.suffix
        # Only accept zip files
        if zip_extension in ('.zip', '.cbz'):
            image_ids = []
            failed_image_upload = False
            manga_series, language, chapter_number, volume_number, groups, chapter_title = process_zip(to_upload, names_to_ids)
            if not groups:
                print(f'No groups found, using group fallback')
                groups = group_fallback

            if manga_series is None:
                print(f'Skipped {zip_name}, no manga id found.')
                continue

            # Remove any exising upload sessions to not error out
            existing_session = session.get(f'{md_upload_api_url}')
            if existing_session.status_code == 200:
                remove_upload_session(session, existing_session.json()["data"]["id"])

            # Start the upload session
            upload_session_response = session.post(f'{md_upload_api_url}/begin', json={"manga": manga_series, "groups": groups})
            if upload_session_response.status_code != 200:
                print_error(upload_session_response)
                print(f'Error creating draft for {zip_name}.')
                continue

            upload_session_id = upload_session_response.json()["data"]["id"]
            print(f'Created upload session: {upload_session_id}, {zip_name}')

            # Open zip file and read the data
            with zipfile.ZipFile(to_upload) as myzip:
                info_list = myzip.infolist()
                # Remove any directories and none-image files from the zip info array
                info_list_dir_removed = list(reversed([image for image in reversed(info_list.copy()) if not image.is_dir()]))
                info_list_images_only = [image for image in info_list_dir_removed if Path(image.filename).suffix in ('.png', '.jpg', '.jpeg', '.gif')]
                # Separate the image array into smaller arrays of 5 images
                info_list_separate = [info_list_images_only[l:l + 5] for l in range(0, len(info_list_images_only), 5)]

                for array_index, images in enumerate(info_list_separate, start=1):
                    files = {}
                    # Read the image data and add to files dict
                    for image_index, image in enumerate(images, start=1):
                        image_filename = str(Path(image.filename).name)
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
                print(f'Deleting draft due to failed image upload: {upload_session_id}, {zip_name}.')
                remove_upload_session(session, upload_session_id)
                continue

            # Try to commit the chapter 3 times
            commit_retries = 0
            succesful_upload = False
            while commit_retries < 3:
                chapter_commit_response = session.post(f'{md_upload_api_url}/{upload_session_id}/commit',
                    json={"chapterDraft":
                        {"volume": volume_number, "chapter": chapter_number, "title": chapter_title, "translatedLanguage": language}, "pageOrder": image_ids
                    })

                if chapter_commit_response.status_code == 200:
                    succesful_upload = True
                    succesful_upload_id = chapter_commit_response.json()["data"]["id"]
                    print(f'Succesfully uploaded: {succesful_upload_id}, {zip_name}')

                    # Move the uploaded zips to a different folder
                    uploaded_files_path.mkdir(parents=True, exist_ok=True)
                    to_upload.rename(uploaded_files_path.joinpath(zip_name).with_suffix(zip_extension))
                    break

                print(f'Failed to commit {zip_name}, trying again.')
                commit_retries += 1
                time.sleep(1)

            if not succesful_upload:
                print(f'Failed to commit {zip_name}, removing upload draft.')
                remove_upload_session(session, upload_session_id)

            time.sleep(3)
