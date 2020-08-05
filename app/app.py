import sys

from flask import Flask, jsonify, request, json, render_template
from flask_cors import CORS
import requests
from array import array
import json
import pymongo
from flask_mail import Mail, Message
from bson.objectid import ObjectId
from datetime import datetime
from datetime import timedelta
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, decode_token
from flask_jwt_extended import create_access_token
from threading import Thread
from jwt import ExpiredSignatureError
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token, decode_token, get_raw_jwt
from bson.json_util import loads, dumps

from app import app
from werkzeug.exceptions import InternalServerError
from resources.errors import SchemaValidationException, InternalServerError, \
    EmailNotExistsError, BadTokenError, UserNotFoundError, UnauthorizedError, UserAlreadyExistsError
from jwt.exceptions import ExpiredSignatureError, DecodeError, \
    InvalidTokenError

app = Flask(__name__, template_folder='../templates')

client = pymongo.MongoClient(
    "mongodb+srv://group27:AWD-Group27@advancedwebservice.i3vir.mongodb.net/awdproject?retryWrites=true&w=majority")
db = client.awdproject

app.config['JWT_SECRET_KEY'] = 'secret'
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'movrev.help@gmail.com',
    "MAIL_PASSWORD": 'MovRev@2020'
}

password_reset_settings = {
    "FRONT_END_URL": 'https://adv-web-project-group27.herokuapp.com/'
}

def make_response(statusCode, body):
    response = {
        "statusCode": statusCode,
        "body": body
    }
    return response

app.config.update(mail_settings)
app.config.update(password_reset_settings)
mail = Mail(app)

CORS(app)


################################ Watchlist (Working) ################################

@app.route('/loadWatchlist/<email>', methods=['GET'])
def loadWatchlist(email):
    print(email)
    watchlist = db.watchlist.find({'email': email}, {'_id': 0})
    watchlist = list(watchlist)
    if len(watchlist) == 0:
        response = make_response(404, json.dumps("No movies in watchlist"))
    else:
        response = make_response(200, json.dumps(watchlist))
    return response



@app.route('/addToWatchlist', methods=['POST'])
def addMovieToWatchlist():
    data = request.json
    email = data['email']
    movieid = data['movieid']
    moviename = data['moviename']
    poster = data['poster']
    year = data['year']
    rating = data['rating']
    if email is None:
        response = make_response(400, json.dumps("Please login!"))
        return response
    movie = db.watchlist.find({'email': email, 'movieid': movieid}, {'_id': 0})
    movie = list(movie)
    if len(movie) == 0:
        db.watchlist.insert_one(
            {'email': email, 'movieid': movieid, 'moviename': moviename, 'poster': poster, 'year': year,
             'rating': rating})
        response = make_response(200, json.dumps("Movie added to watchlist"))
    else:
        response = make_response(409, json.dumps("Movie already added in watchlist"))
    return response



@app.route('/deleteMovie', methods=['DELETE'])
def deleteMoviewFromWatchlist():
    data = request.json
    email = data['email']
    movieid = data['movieid']
    db.watchlist.remove({'email': email, 'movieid': movieid})
    response = make_response(200, json.dumps("Movie removed from watchlist"))
    return response



################################ Support (Working)################################

@app.route('/submitEnquiry', methods=['POST'])
def submitEnquiry():
    data = request.json
    email = data['email']
    message = data['message']
    db.enquiry.insert_one({'email': email, 'message': message})
    msg = Message(subject="Enquiry", sender=app.config.get("MAIL_USERNAME"),
                  recipients=[app.config.get("MAIL_USERNAME")],
                  body="Enquiry email : " + email + "   Message : " + message)
    mail.send(msg)
    response = make_response(200, json.dumps("Enquiry Submitted Successfully"))
    return response


################################ Reviews (Working)################################

@app.route('/loadReviews/<email>', methods=['GET'])
def loadReviews(email):
    reviews = db.reviews.find({'email': email}, {'_id': 0})
    reviewList = list(reviews)
    if len(reviewList) == 0:
        response = make_response(404, json.dumps("No reviews found"))
    else:
        response = make_response(200, json.dumps(reviewList))
    return response



@app.route('/loadAllReviews/<movieid>', methods=['GET'])
def loadAllReviews(movieid):
    reviews = db.reviews.find({'movieid': movieid}, {'_id': 0})
    reviewList = list(reviews)
    if len(reviewList) == 0:
        response = make_response(404, json.dumps("No reviews found"))
    else:
        response = make_response(200, json.dumps(reviewList))
    return response



@app.route('/postReview', methods=['POST'])
def postReview():
    data = request.json
    email = data['email']
    movieid = data['movieid']
    title = data['title']
    reviewtitle = data['reviewtitle']
    rating = data['rating']
    description = data['description']

    review = db.reviews.find({'movieid': movieid, 'email': email}, {'_id': 0})
    review = list(review)

    if len(review) == 0:
        db.reviews.insert_one(
            {'email': email, 'movieid': movieid, 'title': title, 'reviewtitle': reviewtitle, 'rating': rating,
             'description': description})
        response = make_response(200, json.dumps("review Submitted"))
    else:
        response = make_response(409, json.dumps("review already submitted for this movie"))
    return response



@app.route('/updateReview', methods=['PUT'])
def updateReview():
    data = request.json
    email = data['email']
    movieid = data['movieid']
    reviewtitle = data['reviewtitle']
    rating = data['rating']
    description = data['description']
    db.reviews.update_one(
        {'email': email, 'movieid': movieid},
        {"$set": {'reviewtitle': reviewtitle, 'rating': rating, 'description': description}})
    response = make_response(200, json.dumps("review Updated"))
    return response



@app.route('/deleteReview', methods=['DELETE'])
def deleteReview():
    data = request.json
    email = data['email']
    movieid = data['movieid']
    db.reviews.remove({'email': email, 'movieid': movieid})
    response = make_response(200, json.dumps("review Deleted"))
    return response



################################ Top Rated Movies (Working)################################

@app.route('/getTopRatedMovies', methods=['GET'])
def getTopRatedMovies():
    movielist = ['The Shawshank Redemption', 'The Godfather', 'The Dark Knight', 'The Godfather: Part II', 'Hamilton',
                 'The Lord of the Rings: The Return of the King', 'Pulp Fiction', 'Schindler\'s List', '12 Angry Men',
                 'Inception',
                 'Fight Club', 'The Lord of the Rings: The Fellowship of the Ring', 'Forrest Gump',
                 'The Good, the Bad and the Ugly', 'The Lord of the Rings: The Two Towers',
                 'The Matrix', 'Goodfellas', 'Star Wars: Episode V - The Empire Strikes Back',
                 'One Flew Over the Cuckoo\'s Nest', 'Harakiri']
    apiKey = 'eb6b77a0'
    data_URL = 'http://www.omdbapi.com/?apikey=' + apiKey
    moviedetailslist = []

    for movie in movielist:
        params = {'t': movie, 'plot': 'full', 'r': 'json'}
        response = requests.get(data_URL, params=params).json()
        moviedetailslist.append(response)
    response = make_response(200, json.dumps(moviedetailslist))
    return response


@app.route('/getHomeMovies', methods=['GET'])
def getHomeMovies():
    movielist = ['The Old Guard', 'Greyhound', 'Palm Springs', 'Hamilton', '365 Days',
                 'Eurovision Song Contest: The Story of Fire Saga', 'Relic', 'Knives Out', 'The F**k-It List',
                 'Desperados',
                 'Jerry Maguire', 'The Gentlemen', 'Love', 'Once Upon a Time... in Hollywood', 'Twins',
                 'Fatal Affair', 'Archive', 'Doctor Sleep', 'Parasite', 'Joker']
    apiKey = 'eb6b77a0'
    data_URL = 'http://www.omdbapi.com/?apikey=' + apiKey
    moviedetailslist = []

    for movie in movielist:
        params = {'t': movie, 'plot': 'full', 'r': 'json'}
        response = requests.get(data_URL, params=params).json()
        moviedetailslist.append(response)
    response = make_response(200, json.dumps(moviedetailslist))
    return response


################################ Subscription (working) ################################

@app.route('/subscribe', methods=['POST'])
def subscribe_user():
    topRatedMovies = "https://awd-backend.herokuapp.com/getTopRatedMovies"
    useremail = request.get_json()['useremail']
    collection = db.subscribedusers
    useremail = request.get_json()['useremail']
    movies = requests.get(topRatedMovies)
    toprated_movies = movies.json()
    msg = Message('Hello', sender='movrev.help@gmail.com', recipients=[useremail])
    fullstring = ""
    total = ""
    htmlmsg = ""
    toprated_movies = json.loads(toprated_movies['body'])
    for value in toprated_movies:
        fullstring = htmlmsg + "<h5> Movie title </h5><h3>" + str(value["Title"]) + "</h3> <br> <img src='" + str(
            value["Poster"]) + "'/><br> <h5> Rating: </h5> <h1>" + str(value["Metascore"]) + "</h1>"
        total = total + fullstring
    msg.html = "<body> <p>Thank you for your subscription to MovRev and plese find the top rated movies below for the week</p>" + total + "</body>";
    mail.send(msg)
    userSubscriptionEmail = {"useremail": useremail}
    collection.insert_one(userSubscriptionEmail)
    return "Sent"


################################ Blogging and Network ################################

@app.route('/getnetwork', methods=['POST'])
def get_network():
    collection = db.userinfo
    user_id = request.form['userid']
    users_network = collection.find({})
    all_users = []

    for user in users_network:
        del user['_id']
        del user['password']
        del user['address']
        del user['city']
        del user['country']
        del user['postal_code']
        del user['about_me']
        del user['last_modified']
        del user['created']
        all_users.append(user)
    x = json.dumps(all_users)
    return x


@app.route('/getfollowersfollowing', methods=['POST'])
def getfollowersfollowing():
    collection = db.usernetwork
    user_id = request.form['userid']
    users_followers = collection.find({'userid': user_id})
    all_users = []

    for user in users_followers:
        del user['_id']
        all_users.append(user)
    x = json.dumps(all_users)
    return x


@app.route('/saveblog', methods=['POST'])
def save_blog():
    collection = db.userblogs
    user_id = request.form['userid']
    blog_title = request.form['blog_title']
    blog_subtitle = request.form['blog_subtitle']
    blog_content = request.form['blog_content']
    try:
        collection.insert_one({
            'userid': user_id,
            'title': blog_title,
            'subtitle': blog_subtitle,
            'content': blog_content,
        })
        return json.dumps({'status': True})
    except:
        return json.dumps({'status': False})


@app.route('/getuserblogs', methods=['POST'])
def get_user_blogs():
    collection = db.userblogs
    user_id = request.form['userid']
    blogs = collection.find({'userid': user_id})
    retrieved_blogs = []
    for blog in blogs:
        del blog['_id']
        del blog['userid']
        retrieved_blogs.append(blog)
    return json.dumps(retrieved_blogs)


@app.route('/deleteblog', methods=['POST'])
def delete_blog():
    collection = db.userblogs
    user_id = request.form['userid']
    title = request.form['blog_title']
    subtitle = request.form['blog_subtitle']
    try:
        collection.remove({'userid': user_id, 'title': title, 'subtitle': subtitle})
        return json.dumps({'status': True})
    except:
        return json.dumps({'status': False})


@app.route('/getalluserblogs', methods=['POST'])
def get_all_user_blogs():
    collection = db.userblogs
    blogs = collection.find({})
    retrieved_blogs = []
    for blog in blogs:
        del blog['_id']
        retrieved_blogs.append(blog)
    return json.dumps(retrieved_blogs)


################################ Login and Registration ################################

@app.route('/users/register', methods=["POST"])
def register():
    users = db.userinfo
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    email = request.get_json()['email']
    password = bcrypt.generate_password_hash(request.get_json()['password']).decode('utf-8')
    created = datetime.utcnow()
    result = ""

    try:
        user = users.find_one({'email': email})

        if user:
            raise UserAlreadyExistsError("User with email {0} already exists".format(email))
        else:
            user_id = users.insert({
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,
                "address": "",
                "city": "",
                "country": "",
                "postal_code": "",
                "about_me": "",
                "last_modified": "",
                'created': created
            })
            new_user = users.find_one({'_id': user_id})
            data = {'email': new_user['email'] + ' registered'}
            result = jsonify({'result': data})

    except UserAlreadyExistsError as e:
        result = jsonify({"exception": str(e)})
    except Exception as e:
        result = jsonify({"exception": str(e)})
    return result


@app.route('/users/login', methods=['POST'])
def login():
    users = db.userinfo
    email = request.get_json()['email']
    password = request.get_json()['password']
    result = ""

    response = users.find_one({'email': email})

    try:
        if response:
            if bcrypt.check_password_hash(response['password'], password):
                access_token = create_access_token(identity={
                    'first_name': response['first_name'],
                    'last_name': response['last_name'],
                    'email': response['email'],
                    'address': response['address'],
                    'city': response['city'],
                    'country': response['country'],
                    'postal_code': response['postal_code'],
                    'about_me': response['about_me']
                })
                result = jsonify({'token': access_token})
            else:
                raise UnauthorizedError("Invalid username or password")
        else:
            raise UserNotFoundError("User with email {0} does not exist".format(email))
    except UnauthorizedError as e:
        result = jsonify({"exception": str(e)})
    except UserNotFoundError as e:
        result = jsonify({"exception": str(e)})
    except Exception as e:
        result = jsonify({"exception": str(e)})
    return result


@app.route('/users', methods=['GET'])
def users():
    users = db.userinfo
    user = users.find_one()
    print(user)

    if user:
        result = jsonify({
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'address': user['address'],
            'city': user['city'],
            'country': user['country'],
            'postal_code': user['postal_code'],
            'about_me': user['about_me']
        })
    else:
        result = jsonify({"users": "No results found"})
    return result


@app.route('/users/update', methods=['POST'])
def update():
    users = db.userinfo
    email = request.get_json()['email']
    first_name = request.get_json()['first_name']
    last_name = request.get_json()['last_name']
    address = request.get_json()['address']
    city = request.get_json()['city']
    country = request.get_json()['country']
    postal_code = request.get_json()['postal_code']
    about_me = request.get_json()['about_me']
    last_modified = datetime.utcnow()
    result = ""

    response = users.find_one({'email': email})

    if response:
        try:
            users.update(
                {"email": email},
                {
                    "$set": {
                        "first_name": first_name,
                        "last_name": last_name,
                        "address": address,
                        "city": city,
                        "country": country,
                        "postal_code": postal_code,
                        "about_me": about_me,
                        "last_modified": last_modified
                    }
                }
            )
        except Exception as e:
            result = jsonify({"exception": str(e)})
    else:
        result = jsonify({"result": "No records found to update"})

    res = users.find_one({'email': email})
    access_token = create_access_token(identity={
        'first_name': res['first_name'],
        'last_name': res['last_name'],
        'email': res['email'],
        'address': res['address'],
        'city': res['city'],
        'country': res['country'],
        'postal_code': res['postal_code'],
        'about_me': res['about_me']
    })
    result = jsonify({'token': access_token})
    return result


@app.route('/users/forgot', methods=['POST'])
def forgot_password():
    users = db.userinfo
    url = app.config.get("FRONT_END_URL") + 'reset/'
    result = ""
    try:
        email = request.get_json()['email']
        if not email:
            raise SchemaValidationException("Request is missing required fields {0}".format("email"))
        user = users.find_one({'email': email})
        if not user:
            raise EmailNotExistsError("Couldn't find the user with given email address")

        expires = timedelta(hours=2)
        reset_token = create_access_token(str(user['email']), expires_delta=expires)

        send_email('[MovRev] Reset Your Password',
                   sender=app.config.get("MAIL_USERNAME"),
                   recipients=[user['email']],
                   text_body=render_template('/email/reset_password.txt',
                                             url=url + reset_token,
                                             user=user['first_name']),
                   html_body=render_template('email/reset_password.html',
                                             url=url + reset_token,
                                             user=user['first_name']))
        result = jsonify({"result": "Password reset link sent successfully."})
    except SchemaValidationException as e:
        result = jsonify({"exception": str(e)})
    except EmailNotExistsError as e:
        result = jsonify({"exception": str(e)})
    except Exception as e:
        result = jsonify({"exception": str(e)})
    return result


@app.route('/users/reset', methods=['POST'])
def reset_password():
    users = db.userinfo
    result = ""
    try:
        reset_token = request.get_json()['reset_token']
        password = request.get_json()['password']

        if not reset_token or not password:
            raise SchemaValidationException("Request is missing required fields {0} or {1}".
                                            format("reset_token", "password"))

        email = decode_token(reset_token)['identity']
        user = users.find_one({'email': email})
        encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
        last_modified = datetime.utcnow()

        if not user:
            raise UserNotFoundError("User does not exist {0}".format(email))
        users.update(
            {"email": email},
            {
                "$set": {
                    "password": encrypted_password,
                    "last_modified": last_modified
                }
            }
        )

        send_email('[MovRev] Password reset successful',
                   sender=app.config.get("MAIL_USERNAME"),
                   recipients=[user['email']],
                   text_body='Password reset was successful',
                   html_body='<p>Password reset was successful</p>')
        result = jsonify({"result": "Password reset successful"})

    except SchemaValidationException as e:
        result = jsonify({"exception": str(e)})
    except ExpiredSignatureError as e:
        result = jsonify({"exception": str(e)})
    except (DecodeError, InvalidTokenError) as e:
        result = jsonify({"exception": str(e)})
    except UserNotFoundError as e:
        result = jsonify({"exception": str(e)})
    except Exception as e:
        result = jsonify({"exception": str(e)})
    return result


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except ConnectionRefusedError:
            raise InternalServerError("[MAIL SERVER] not working")


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


@app.route('/userhistory', methods=['POST'])
def userhistory():
    collection = db.userhistory
    usertoken = request.get_json()['movHis']['userToken']
    decodetoken = decode_token(usertoken)
    useremail = decodetoken['identity']['email']
    movieId = request.get_json()['movHis']['movieID']
    movieImgSrc = request.get_json()['movHis']['movImgSrc']
    movieRating = request.get_json()['movHis']['movRating']
    movieTitle = request.get_json()['movHis']['movTitle']
    movieGenre = request.get_json()['movHis']['movGenre']
    movieYear = request.get_json()['movHis']['movYear']
    response = collection.find_one({'userEmail': useremail, 'movieID': movieId})
    insertHisMov = {"userEmail": useremail, "movieID": movieId, "movImgSrc": movieImgSrc, "movRating": movieRating,
                    "movTitle": movieTitle, "year": movieYear}
    if (response is None):
        collection.insert_one(insertHisMov)
    return json.dumps({'status': True})


@app.route('/eachuserhistory', methods=['GET'])
def eachuserhistory():
    usertoken = request.args['token']
    decodetoken = decode_token(usertoken)
    useremail = decodetoken['identity']['email']
    collection = db.userhistory
    movies = collection.find({'userEmail': useremail}, {"_id": 0})
    movies = list(movies)
    return json.dumps(movies)


@app.route('/deletemoviehistory', methods=['POST'])
def deletemoviefromhistory():
    collection = db.userhistory
    usertoken = request.get_json()['movHisDel']['userToken']
    decodetoken = decode_token(usertoken)
    useremail = decodetoken['identity']['email']
    movieId = request.get_json()['movHisDel']['movieID']
    try:
        response = collection.remove({"userEmail": useremail, "movieID": movieId})
        return json.dumps({'status': True})
    except:
        return json.dumps({'status': False})
