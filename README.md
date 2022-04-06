# SDtoGooglePhotos
Mounts SD card, uploads new photos and videos to Google Photos, unmounts SD card.

# Step by step

1. Copy /home/gphotos/gphotos.py somewhere. Edit the ALBUMTITLE variable.

2. Install google api packages
```
pip3 install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib filelock
```

3. [Enable Google Photos API](https://developers.google.com/photos/library/guides/get-started). Download credentials.json and put it in the folder next to gphotos.py.

4. Copy /home/usb-automount somewhere. Edit the pushover_token, pushover_user and home_dir variables. Make sure the reference to gphotos.py is correct. Give the file execution rights.
```
chmod +x usb-automount
```

5. Create a service called usb-automount (/etc/systemd/system/usb-automount@.service). Make sure the reference to the usb-automount executable is correct.

6. Create a new rule (/etc/udev/rules.d/90-usb-automount.rules) that triggers the service mentioned above. Make sure the model id matches that of your card reader.

Python script is a slightly edited version of [vozh/python-google-photos-api](https://github.com/vozh/python-google-photos-api)