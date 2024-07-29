import os

from target.photoPrism.PPClient import PPClient


def _delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def sync_photo(photo_paths,username,password,base_url,ablum_name):
    ppClient = PPClient(username, password, base_url)
    user_id = ppClient.get_uid()
    albums = ppClient.get_albums()
    exist = False
    album_id = None
    for album in albums:
        if album['Title'] == ablum_name:
            exist = True
            album_id = album['UID']
            break
    if exist is False:
        album = ppClient.create_album(ablum_name)
        album_id = album['UID']

    for photo_path in photo_paths:
        for root, dirs, files in os.walk(photo_path):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file_path)[1]
                mimetype = None
                if ext in ['.jpg', 'jpeg', '.png', 'gif', '.mp4']:
                    if ext in ['.jpg', 'jpeg', '.png', '.gif']:
                        mimetype = 'image/jpeg'
                    if ext in ['.mp4']:
                        mimetype = 'video/mp4'
                    ppClient.upload_photo(file, open(file_path, 'rb'),user_id, mimetype=mimetype,album_ids=[album_id])
                    print(f"upload {file_path} success")
                    _delete_file(file_path)
