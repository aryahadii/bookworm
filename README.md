# Bookworm

Bookworm is a Django 2.2 application that signs in to a Fidibo account, lists purchased ebooks, and lets you download a DRM-free EPUB for personal offline reading. It relies on the same AES-based protocol that Fidibo's client uses and re-creates the EPUB locally once an encrypted download completes.

## Requirements

- Python 3.7 or newer (matches Django 2.2 support)
- Pip and virtualenv (recommended) for isolated dependency management
- Access to the Fidibo API with valid account credentials

## Quick start

```bash
# From the project root
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Initialise the SQLite database created by Django
python manage.py migrate

# Start the development server
python manage.py runserver
```

Open `http://127.0.0.1:8000` in a browser, enter your Fidibo username and password, and the app will show the titles that Fidibo reports for the account. Selecting a title triggers a download, removes the DRM layer in-memory, rebuilds an EPUB, and streams it back to the browser as a file download.

## Configuration notes

- `bookworm/settings.py` ships with placeholder `DEVICE_INFO`, `STORE_ID`, and `APP_VERSION_NAME` values that mimic a desktop client. Adjust them if Fidibo changes the required identifiers.
- EPUBs are written to `BOOK_DOWNLOAD_PATH` before they are streamed back. The default (`"{}.epub"`) saves files in the repository root. Update this path if you prefer an isolated temporary directory with appropriate filesystem permissions.
- All requests target `http://api.fidibo.com`; no local mocking is provided.

## Security and privacy considerations

- Credentials are posted to the Django server and also embedded in download URLs (`/download/<username>/<password>/...`). Deploy behind HTTPS and avoid sharing URLs. For production use, refactor the download view to avoid placing secrets in the path.
- Do not deploy this project publicly without adding authentication, rate limiting, logging, and secure secret storage. The sample settings file keeps `DEBUG=True` and a hard-coded `SECRET_KEY`, which are both unsuitable for production.
- DRM removal may violate local laws or Fidibo's terms of service; use responsibly and only with books you own.

## Testing

Run Django's test suite with:

```bash
python manage.py test
```

Only placeholder tests exist today, so consider adding integration coverage around the Fidibo API and the EPUB pipeline before making substantial changes.

## Troubleshooting

- If downloads fail with decryption errors, confirm that the Fidibo credentials are correct and that the account owns the selected title.
- The external API occasionally blocks repeated requests. Add retries or backoff if you build automation on top of this project.
- The app depends on the `pycryptodome` package for AES operations; make sure native build tools are available when installing dependencies on non-Linux hosts.

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes with focused commits.
3. Run `python manage.py test` and any additional tools you rely on.
4. Open a pull request with a clear description of the change, its motivation, and testing evidence.
