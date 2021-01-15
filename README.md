Hello! This is the source code for rainychan.net.

RainyChan is made using Django, a Python backend web development framework. Django has an ORM, and I use Django's MySQL backend to run the site. The webserver uses uWSGI and Nginx.

In case you want to test the code, and perhaps suggest changes, there are a few things you need to do in addition to cloning the repository. You will need to:

Get the dependencies by doing:
```
pip install -r requirements.txt
```

The Django settings file could not be included, as it contains secret server-side information, but if you generate a Django project in a separate directory, you can copy the default settings file from there into the my_site/ directory and then make the following changes:
- Create a database for the site on a MySQL server, and configure the settings.py file to point to it.
- Add "django_extensions", "captcha", and "boards" to INSTALLED_APPS.
- Configure the static files, media files, and templates to point to the right directories.
	- The media files can go wherever you want.
	- The static files live in the static/ directory.
	- The templates live in boards/templates/.

Then, you should be able to do:
```
./manage.py makemigrations
./manage.py migrate
```
To create the tables in the database.

Now, you should be able to run the Django development server with:
```
./manage.py runserver 127.0.0.1:8080
```

No boards are created by default, but you can create one my running the command:
```
./manage.py shell
```
And then adding a board to the database:
```
from boards.models import Board
my_board = Board(name='t', description='My test board.')
my_board.save()
```

And then you can experiment with the code and submit changes!

I hope to see you on RainyChan!
- 
