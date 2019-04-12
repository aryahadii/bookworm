from os.path import getsize
import mimetypes

from django.http import HttpResponse
from django.shortcuts import render

from fidibo.api import FidiboConnection


def home(request):
    return render(request, 'fidibo/home.html')


def books(request):
    username, password = request.POST['username'], request.POST['password']
    conn = FidiboConnection(username, password)
    books = conn.get_bought_books()
    return render(
        request,
        'fidibo/books.html',
        context={
            'books': books,
            'username': username,
            'password': password
        })


def download(request, username, password, book_id, book_title, book_password):
    book_password = book_password.encode('ascii')

    conn = FidiboConnection(username, password)
    conn.download_book(book_id)
    conn.remove_drm(book_id, book_password)
    conn.create_epub_file(book_id, book_title)
    conn.remove_original_epub(book_id)

    file_path = conn.get_epub_file_path(book_id)
    with open(file_path, 'rb') as f:
        data = f.read()

    response = HttpResponse(
        data, content_type=mimetypes.guess_type(file_path)[0])
    response['Content-Disposition'] = "attachment; filename={0}".format(
        book_id + '.epub')
    response['Content-Length'] = getsize(file_path)
    return response
