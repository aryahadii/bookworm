import base64
import zipfile
from json import dumps, loads
from os import listdir, path, remove, walk
from shutil import rmtree
from urllib.parse import unquote, urlencode

import requests
from Crypto.Cipher import AES
from Crypto.Util import Padding
from django.conf import settings


class Session:
    def __init__(self, user_id, session_key, username, password, *args,
                 **kwargs):
        self.user_id = user_id
        self.session_key = session_key
        self.username = username
        self.password = password


METHOD_STARTUP = 'app.startup'
METHOD_LOGIN = 'user.login'
METHOD_BOOKS = 'user.books'


class FidiboConnection:
    def __init__(self, username, password, *args, **kwargs):
        self.API_URL = 'http://api.fidibo.com/api/request?'
        self.FIDIBO_TEXT_DIR = 'OEBPS/Text/'
        self.FIDIBO_IV = r'fedcba9876543210'.encode('ascii')

        self._start_session(username, password)

    def _encrypt_request_data(self, data, second_key):
        key = b'B@41Ner2' + second_key
        decryptor = AES.new(key, AES.MODE_ECB)
        data = data.encode('utf-8')
        data = Padding.pad(data, 16)
        enc = decryptor.encrypt(data)
        return base64.standard_b64encode(enc)

    def _decrypt_response_data(self, data, second_key):
        key = ('B@41Ner2' + second_key).encode('utf-8')
        decryptor = AES.new(key, AES.MODE_ECB)
        unpa = base64.standard_b64decode(unquote(data))
        dec = decryptor.decrypt(unpa)
        return dec

    def _request(self, data):
        data = dumps(data)
        second_key = b'BhdTNbSp'
        data = {
            'data': second_key + self._encrypt_request_data(data, second_key),
        }
        url = self.API_URL + urlencode(data)
        resp = requests.get(url).text
        dec = self._decrypt_response_data(resp[8:], resp[:8])
        dec = dec.decode("utf-8").strip(b'\x08'.decode('utf-8')).strip(
            b'\x0e'.decode('utf-8')).rpartition('}')[0] + '}'
        return dec

    def _login(self, session_key, username, password):
        req = {
            'method': METHOD_LOGIN,
            'username': username,
            'password': password,
            'session': session_key,
        }
        resp = loads(self._request(req))
        if not resp['output']['result']:
            raise Exception('cannot login')

        return resp['output']['user_id']

    def _start_session(self, username, password):
        req = {
            'method': METHOD_STARTUP,
            'first_req': True,
            'app_ver': settings.APP_VERSION_NAME,
            'device': settings.DEVICE_INFO,
            'storeId': settings.STORE_ID,
        }
        resp = loads(self._request(req))
        session_key = resp['output']['session']

        user_id = self._login(session_key, username, password)
        self.session = Session(user_id, session_key, username, password)

    def _decrypt_book_password(self, password):
        key = 'm4n0Ma!iDoF@r5Ha'.encode('utf8')
        decryptor = AES.new(key, AES.MODE_ECB)
        password = base64.standard_b64decode(password)
        password = decryptor.decrypt(password)
        return ('t@l&6S3!' +
                password[:-password[-1]].decode('utf-8')).encode('ascii')

    def get_bought_books(self):
        req = {
            'method': METHOD_BOOKS,
            'session': self.session.session_key,
            'user_Id': self.session.user_id,
            'username': self.session.username,
            'password': self.session.password,
        }
        books = loads(self._request(req))['output']['books']

        res = []
        for book in books:
            res.append(
                Book(
                    id=book['book_id'],
                    title=book['book_title'],
                    url=book['path'],
                    password=self._decrypt_book_password(book['pass']),
                ))
        return res

    def download_book(self, book_id):
        data = {
            'method': 'books.download',
            'book_id': book_id,
            'storeId': settings.STORE_ID,
            'user_Id': self.session.user_id,
            'session': self.session.session_key,
            'username': self.session.username,
            'password': self.session.password,
        }

        data = dumps(data)
        second_key = b'BhdTNbSp'
        data = {
            'data': second_key + self._encrypt_request_data(data, second_key),
        }
        url = self.API_URL + urlencode(data)
        reader = requests.get(url, allow_redirects=True)
        open(self.get_epub_file_path(book_id), 'wb').write(reader.content)

    def remove_drm(self, book_id, book_password):
        ext_dir = self.get_epub_file_path(book_id)[:-5]
        self._unzip_file(self.get_epub_file_path(book_id), ext_dir)

        for file in listdir(path.join(ext_dir, self.FIDIBO_TEXT_DIR)):
            self._decode_file(book_password,
                              path.join(ext_dir, self.FIDIBO_TEXT_DIR, file))

    def _unzip_file(self, file_path, dest_dir):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)

    def create_epub_file(self, book_id, book_title):
        with zipfile.ZipFile(
                self.get_epub_file_path(book_id), 'w',
                zipfile.ZIP_DEFLATED) as archive:
            for root, dirs, files in walk(book_id):
                for file in files:
                    file_path = path.join(root, file)
                    archive.write(
                        filename=file_path,
                        arcname=path.sep.join(file_path.split(path.sep)[1:]))

    def _decode_file(self, book_password, file_path):
        decoded_str = ''
        with open(file_path, 'rb') as text_file:
            decryptor = AES.new(book_password, AES.MODE_CBC, self.FIDIBO_IV)
            content = text_file.read()
            decoded = decryptor.decrypt(content)
            decoded = decoded.decode('utf-8').strip(chr(0))

            unhexed = bytearray(b'')
            for i in range(0, len(decoded), 2):
                try:
                    unhexed.append(int(decoded[i:i + 2], 16))
                except Exception:
                    pass
            decoded_str = unhexed.decode('utf-8')

        with open(file_path, 'w', encoding='utf-8') as text_file:
            text_file.write(decoded_str)

    def get_epub_file_path(self, book_id):
        return settings.BOOK_DOWNLOAD_PATH.format(book_id)

    def _get_extracted_epub_file_path(self, book_id):
        return settings.BOOK_DOWNLOAD_PATH.format(book_id)[:-5]

    def remove_original_epub(self, book_id):
        # remove(self.get_epub_file_path(book_id))
        rmtree(self._get_extracted_epub_file_path(book_id))


class Book:
    def __init__(self, id, title, url, password, *args, **kwargs):
        self.id = id
        self.title = title
        self.url = url
        self.password = password.decode('ascii')

    def __str__(self):
        return self.id
