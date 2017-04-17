from functools import wraps

from flask import Flask, render_template, url_for, request, redirect, \
    flash, jsonify

from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Category, Item

# Imports for OAuth 2.0
from flask import session as login_session
import random
import string

# Imports for OAuth login providers
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

APP_PATH = '/var/www/catalog/catalog/'
G_CLIENT_SECRETS_PATH = APP_PATH + 'client_secrets.json'
FB_CLIENT_SECRETS_PATH = APP_PATH + 'fb_client_secrets.json'
CLIENT_ID = json.loads(
    open(G_CLIENT_SECRETS_PATH, 'r').read())['web']['client_id']

engine = create_engine('postgresql://catalog:P@ssW0rd@localhost/catalog')
# Bind the engine with the Base class
# Connections between the our Class definitions and corresponding tables
# in our database
Base.metadata.bind = engine
# Link between code execution and the engine we created
DBSession = sessionmaker(bind=engine)
# Session which allows all the commands we want to execute in the database,
# but won't save until a commit is executed
session = DBSession()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login/')
        return f(*args, **kwargs)
    return decorated_function


# Create a state token to prevent request forgery.
# Store it in the session for later validation.
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# For login using Google
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        # Below print is for debug please ignore
        # print "Invalid state parameter, 401"
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(G_CLIENT_SECRETS_PATH, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        # Below print is for debug please ignore
        # print "Failed to upgrade the authorization code, 401."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
           access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode("utf8"))

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        # Below print is for debug please ignore
        # print "Error 500"
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        # Below print is for debug please ignore
        # print "Token's user ID doesn't match given user ID, 401"
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        # Below print is for debug please ignore
        # print "Current user is already connected, 200"
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)

    login_session['user_id'] = user_id

    flash("You are now logged in as %s" % login_session['username'])
    return redirect(url_for('showCatalog'))


# Logout from Google: Revoke a current user's token and reset their
# login_session
@app.route("/gdisconnect/")
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Execute HTTP GET request to revoke current token.
    access_token = credentials
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    response = make_response(
        json.dumps('You have been logged out'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


# Login with Facebook, connect
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open(FB_CLIENT_SECRETS_PATH, 'r').read())['web']
    ['app_id']
    app_secret = json.loads(
        open(FB_CLIENT_SECRETS_PATH, 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=\
    fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to
    # properly logout, let's strip out the information before the
    # equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0\
    &height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("You are now logged in as %s" % login_session['username'])
    return redirect(url_for('showCatalog'))


@app.route('/fbdisconnect/')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % \
          (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out"


# Disconnect i.e. Logout from OAuth login based on provider
@app.route('/disconnect/')
def disconnect():
    if 'provider' in login_session:
        # If logged in with google
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        # If logged in with facebook
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        # Delete login session attributes to completely logout
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in to begin with!")
        return redirect(url_for('showCatalog'))


# Making an API Endpoint (GET Request)
# RESTful API to get all the list of categories
@app.route('/categories.json/')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(Categories=[i.serialize for i in categories])


# RESTful API to get all the list of categories with its respective items
@app.route('/catalog.json/')
def catalogJSON():
    catalog = session.query(Category).all()
    return jsonify(Categories=[i.serializeWithItems for i in catalog])


# RESTful API to get only get all the items irrespective of category
@app.route('/items.json/')
def itemsJSON():
    items = session.query(Item).all()
    return jsonify(Items=[i.serialize for i in items])


# Starting Page of application
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    catalog = session.query(Category).all()
    latestItems = session.query(Item).order_by(desc(Item.created_datetime)).\
        limit(10).all()

    return render_template('catalog.html',
                           login_session=login_session,
                           catalog=catalog,
                           latestItems=latestItems)


# Create a new category
@app.route('/catalog/newCategory/', methods=['GET', 'POST'])
@login_required
def newCategory():
    # if 'username' not in login_session:
    #     return redirect('/login')

    catalog = session.query(Category).all()

    if request.method == 'POST':
        # If category name exists do not create new category
        name = request.form['name']
        for category in catalog:
            if name.lower() == category.name.lower():
                flash("Category %s already exists!" % name)
                return render_template('newCategory.html',
                                       login_session=login_session,
                                       catalog=catalog)

        # Create the category
        newCategory = Category(name=name, user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash("Created New Category: %s!" % newCategory.name)
        return redirect(url_for('showCatalog'))
    else:
        # If request method is GET
        return render_template('newCategory.html',
                               login_session=login_session,
                               catalog=catalog)


# Edit the existing Category
@app.route('/catalog/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    catalog = session.query(Category).all()

    thisCategory = session.query(Category).filter_by(id=category_id).one()

    if thisCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() "\
                "{alert('You are not authorized to edit this category.  "\
                "Please create your own category in order to edit.');}"\
                "</script>"\
                "<body onload='myFunction()'>"

    if request.method == 'POST':
        # If category name already exists do not edit the category
        name = request.form['name']
        for eachCategory in catalog:
            # We compare only with other category names,
            # but not with the same category
            if eachCategory.id != category_id:
                if name.lower() == eachCategory.name.lower():
                    flash("Category %s already exists!" % name)
                    return render_template('editCategory.html',
                                           login_session=login_session,
                                           catalog=catalog,
                                           thisCategory=thisCategory)

        # Edit the category
        thisCategory.name = name
        session.add(thisCategory)
        session.commit()
        flash("Edited Category: %s" % thisCategory.name)
        return redirect(url_for('showCatalog'))
    else:
        # If request method is GET
        return render_template('editCategory.html',
                               login_session=login_session,
                               catalog=catalog,
                               thisCategory=thisCategory)


# Delete the Category
@app.route('/catalog/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    catalog = session.query(Category).all()

    thisCategory = session.query(Category).filter_by(id=category_id).one()

    if thisCategory.user_id != login_session['user_id']:
        return "<script>function myFunction() "\
                "{alert('You are not authorized to delete this category.  "\
                "Please create your own category in order to delete.');}"\
                "</script>"\
                "<body onload='myFunction()'>"

    if request.method == 'POST':
        session.delete(thisCategory)
        session.commit()
        flash("Deleted Category: %s" % thisCategory.name)
        return redirect(url_for('showCatalog'))
    else:
        # If request method is GET
        return render_template('deleteCategory.html',
                               login_session=login_session,
                               catalog=catalog,
                               thisCategory=thisCategory)


# Show items of the specific category
@app.route('/catalog/<int:category_id>/items/')
def showItems(category_id):
    catalog = session.query(Category).all()
    # Get the category row by name
    thisCategory = session.query(Category).filter_by(id=category_id).one()
    # Once you get the category, get all its items filtered by category id
    # category_id is column of item table matching id column of category table
    items = session.query(Item).filter_by(category_id=thisCategory.id)
    return render_template('items.html',
                           login_session=login_session,
                           catalog=catalog,
                           thisCategory=thisCategory,
                           items=items)


# Show one item of a category
@app.route('/catalog/items/<int:item_id>')
def showOneItem(item_id):
    # Get the item by item_id
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('oneItem.html',
                           login_session=login_session,
                           item=item)


# Create new item in the category if it does not exists
@app.route('/catalog/<int:category_id>/item/new/', methods=['GET', 'POST'])
@login_required
def newItem(category_id):
    catalog = session.query(Category).all()

    thisCategory = session.query(Category).filter_by(id=category_id).one()

    if request.method == 'POST':
        # If item title exists do not create new item
        thisCategoryitems = session.query(Item).\
            filter_by(category_id=thisCategory.id)
        title = request.form['title']
        for thisItem in thisCategoryitems:
            if title.lower() == thisItem.title.lower():
                flash("Item %s already exists in %s category!" %
                      (title, thisCategory.name))
                return redirect(url_for('showItems',
                                category_id=thisCategory.id))

        newItem = Item(title=title,
                       description=request.form['description'],
                       category_id=thisCategory.id,
                       user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash("Created New Item: %s!" % newItem.title)
        return redirect(url_for('showItems', category_id=thisCategory.id))
    else:
        return render_template('newItem.html',
                               login_session=login_session,
                               catalog=catalog,
                               thisCategory=thisCategory)


# Edit the item of the category, do not edit if title is changed to
# existing item title.
# Only item created user will be given option to edit
@app.route('/catalog/<int:category_id>/item/<int:item_id>/edit/',
           methods=['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
    catalog = session.query(Category).all()
    thisCategory = session.query(Category).filter_by(id=category_id).\
        one()
    item = session.query(Item).filter_by(id=item_id, category_id=category_id).\
        one()

    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() "\
                "{alert('You are not authorized to edit this item.  "\
                "Please create your own item in order to edit.');}"\
                "</script>"\
                "<body onload='myFunction()'>"

    if request.method == 'POST':
        # If item title exists do not edit the item
        thisCategoryitems = session.query(Item).\
            filter_by(category_id=thisCategory.id)
        title = request.form['title']
        for thisItem in thisCategoryitems:
            # We compare only with other items title, but not with the
            # same item title
            if thisItem.id != item_id:
                if title.lower() == thisItem.title.lower():
                    flash("Item %s already exists in %s category!" %
                          (title, thisCategory.name))
                    return render_template('editItem.html',
                                           login_session=login_session,
                                           catalog=catalog,
                                           thisCategory=thisCategory,
                                           item=item)

        item.title = title
        item.description = request.form['description']
        item.category_id = request.form['new_category_id']
        # print "item.category.id is %s" % item.category_id
        session.add(item)
        session.commit()
        flash("Edited Item: %s" % item.title)
        return redirect(url_for('showOneItem', item_id=item.id))
    else:
        return render_template('editItem.html',
                               login_session=login_session,
                               catalog=catalog,
                               thisCategory=thisCategory,
                               item=item)


# Delete item of the category, only item creator has option to delete
@app.route('/catalog/<int:category_id>/item/<int:item_id>/delete/',
           methods=['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
    catalog = session.query(Category).all()
    thisCategory = session.query(Category).filter_by(id=category_id).one()
    item = session.query(Item).filter_by(id=item_id, category_id=category_id).\
        one()

    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() "\
                "{alert('You are not authorized to delete this item.  "\
                "Please create your own item in order to delete.');}"\
                "</script>"\
                "<body onload='myFunction()'>"

    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Deleted Item: %s" % item.title)
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('deleteItem.html',
                               login_session=login_session,
                               catalog=catalog,
                               thisCategory=thisCategory,
                               item=item)


# Create the user if user email does not existing
def createUser(login_session):
    newUser = User(
                   name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture']
                  )
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Get user info from user id
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Get user id from user email
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'DPXw,YJ9>g$yyuR?'
    app.debug = True
    #app.run(host='0.0.0.0', port=8000)
    app.run()
