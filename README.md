# Catalog App (Categories with Items)
The Catalog App can be used by users in world to view different Categories and its respective items.  It can have sports categories and items, or any as you prefer.

Users can view all the Categories and Items.  Logged in users can add, edit, delete their own Categories and Items.  Can view who added a specific Category.

Users can login using secure OAuth login providers like Google and Facebook.

The Catalog App can contain list of Categories.  Each Category has list of items.  Each item has title, description, date created, and which category it belongs to.

The Catalog App is a application developed in HTML, CSS, JavaScript, Bootstrap Framework, Ajax, jQuery, JSON, RESTfull APIs, Python, Flask Framework, Database with SQLAlChemy Python Module.  Hosted on AWS Lightsail!


# Table of Contents
1. [Author](#author)
2. [Instructions on running the project](#instructions)
3. [Directory Structure](#directory-structure)
4. [Resources](#resources)


<br><br>
### <a name="author"></a>1. Author

Anilkumar P
<br>
<br>
<br>

### <a name="instructions"></a>2. Instructions on running the project

1) The IP address and ssh port to connect to the server as grader user is given below:
    IP Address: 52.91.56.199
    SSH port: 2200
    URL to hosted web app: http://ec2-52-91-56-199.compute-1.amazonaws.com/
2) The software I have installed:
    Used Amazon Lightsail (https://lightsail.aws.amazon.com) to host web app
    Selected Ubuntu 16.04 version as the OS
    Once the Ubuntu OS is up updated and upgraded
    Installed below packages in OS:
  	apache2
	libapache2-mod-wsgi
	python-dev
        postgresql
	python-psycopg2
	python-flask python-sqlalchemy
	python-pip
    Using pip installed below modules:
	bleach
	werkzeug==0.8.3
	flask==0.9
	Flask-Login==0.1.3
	oauth2client
	requests
	httplib2
	passlib
	itsdangerous
	flask-httpauth
3) In the PostgreSQL database created the catalog user and the catalog database
4) Configuration changes made after moving the catalog web app project
    Followed the document https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps to create:
	Created the VirtualHost under /etc/apache2/sites-available/catalog.conf
	The app directory structure:
	    /var/www/catalog
		catalog
			static
			templates
			__init__.py
		catalog.wsgi
	Enabled the wsgi mode and enabled the catalog site
5) Code changes done to original code to run on this new environment:
    database_setup.py is updated to use postgresql database with the catalog username and password
    application.py is renamed to __init__.py and have done below changes in the file:
	Used constant APP_PATH for the application path /var/www/catalog/catalog/
	Used constant G_CLIENT_SECRETS_PATH and FB_CLIENT_SECRETS_PATH for google and facebook client_secrets json files
	Updated open functions with right values
	Updated database create_engine with postgresql username and password 
	app.run is updated without arguments so it takes the default localhost and port
6) Finally to start the application create the database and restarted the apache2
    $ cd /var/www/catalog/catalog
    $ ./database_setup.py
    $ sudo service apache2 restart
      

<br>
<br>
<br>

### <a name="directory-structure"></a>3. Directory Structure

```
-/var/www/catalog
   catalog.wsgi - file for Apache to serve the Flask App
   catalog - directory
      - files:
         README.md - this readme file
         database_setup.py to create database and tables
         __init__.py python program for catalog application
         client_secrets.json configuration file for Google OAuth login
         fb_client_secrets.json configuration file for Facebook OAuth login
         Other files you can leave as it is
      - static directory:
        bootstrap-3.3.7-dist directory for Bootstrap framework
        bootstrap_custom.css for customization of bootstrap for this app
      - template directory:
        Contains all html files for Web Application Pages as below:
            catalog.html
            deleteCategory.html
            deleteItem.html
            editCategory.html
            editItem.html
            flash_message.html
            footer.html
            header.html
            items.html
            login.html
            main.html
            newCategory.html
            newItem.html
            oneItem.html


```

### <a name="resources"></a>4. Resources

- How To Deploy a Flask Application on an Ubuntu VPS
  https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps


