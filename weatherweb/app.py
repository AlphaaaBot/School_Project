# Made by AlphaaaBot
# this script shows a web page and gets the current weather state from the given city

import os
import pytz
import bcrypt
import requests
from datetime import datetime
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from timezonefinder import TimezoneFinder
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

######################################################
# VARIABLES
######################################################

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

######################################################
# DATABASE
######################################################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = self.getHash(bcrypt.gensalt(), password)
        return self.password_hash

    def check_password(self, password):
        password_bytes = password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, self.password_hash)

    def getHash(self, salt, password):
        password_bytes = password.encode('utf-8')
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        return hashed_password

######################################################
# API
######################################################

class API():
    # Variables
    web_api_key = None
    web_api_endpoint_map_data = None
    web_api_endpoint_raw_data = None
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # INIT
    def __init__(self):
        self.web_api_key = self.getAPIKeyFromEnv()
        self.web_api_endpoint_raw_data = self.getAPIRawDataEndpointFromEnv()
        self.web_api_endpoint_map_data = self.getAPIMapDataEndpointFromEnv()
        print(f"Raw Data Endpoint: {self.web_api_endpoint_raw_data}")

    # ENV
    def getAPIKeyFromEnv(self):
        load_dotenv(".env")
        return os.getenv("web_api_key")

    def getAPIRawDataEndpointFromEnv(self):
        load_dotenv(".env")
        return os.getenv("web_api_endpoint_raw_data")

    def getAPIMapDataEndpointFromEnv(self):
        load_dotenv(".env")
        return os.getenv("web_api_endpoint_map_data")
    
    # DATETIME
    def getCurrentLocaleTimeAndDate(self, longitude, latitude):
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
        timezone = pytz.timezone(timezone_str)
        current_time = datetime.now(timezone).strftime('%H:%M')
        current_date = datetime.now(timezone).strftime("%d/%m/%Y")
        obj_datetime = {"date":current_date, "time":current_time}
        return obj_datetime
    
    def getWeekDayName(self, index=0):
        date = datetime.now()
        # get day from List with added index
        index = (date.weekday() + index) % len(self.days)
        weekday_name = self.days[index]
        print(weekday_name)
        return weekday_name
    
    def getWeekdaysAsList(self):
        date = datetime.now()
        weekDays = []
        i = 0
        for day in self.days:
            print(i)
            index = (date.weekday() + i) % len(self.days)
            weekday_name = self.days[index]
            weekDays.append(weekday_name)
            i += 1
            
        return weekDays
    
    # APICALLS
    def getCurrentWeatherInCityAsJSON(self, city):
        url = f"{self.web_api_endpoint_raw_data}/data/2.5/weather?units=metric&q={city}&appid={self.web_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        
        return None
    
    def getWeatherIconCode(self, city):
        data = self.getCurrentWeatherInCityAsJSON(city)
        return data["weather"]["icon"] if not data == None else None
    
    def getDashboardInfoAsJSON(self, city):
        data = self.getCurrentWeatherInCityAsJSON(city)
        if data != None:
            weather_dashboard_obj = {}
            # weather
            weather_dashboard_obj.update({"icon":str(data["weather"][0]["icon"])})
            weather_dashboard_obj.update({"main":str(data["weather"][0]["main"])})
            weather_dashboard_obj.update({"description":str(data["weather"][0]["description"])})
            # main
            temp = int(data["main"]["temp"])
            feels_like = int(data["main"]["feels_like"])
            weather_dashboard_obj.update({"temp":str(temp)})
            weather_dashboard_obj.update({"feels_like":str(feels_like)})
            weather_dashboard_obj.update({"humidity":str(data["main"]["humidity"])})
            # wind
            weather_dashboard_obj.update({"speed":str(data["wind"]["speed"])})
            # clouds
            weather_dashboard_obj.update({"all":str(data["clouds"]["all"])})
            # sys
            weather_dashboard_obj.update({"country":str(data["sys"]["country"])})
            weather_dashboard_obj.update({"sunrise":str(data["sys"]["sunrise"])})
            weather_dashboard_obj.update({"sunset":str(data["sys"]["sunset"])})
            # timezone
            obj_datetime = self.getCurrentLocaleTimeAndDate(data["coord"]["lon"], data["coord"]["lat"])
            print(f"time: {obj_datetime["time"]}\ndate: {obj_datetime["date"]}")
            weather_dashboard_obj.update({"time":str(obj_datetime["time"])})
            weather_dashboard_obj.update({"date":str(obj_datetime["date"])})
            weather_dashboard_obj.update({"timezone":str(data["timezone"])})
            # name
            weather_dashboard_obj.update({"name":str(data["name"])})
        
            return weather_dashboard_obj
        else:
            return None
    

######################################################
# ROUTES
######################################################

@app.route('/', methods=['GET'])
def home():
    """
    Shows the current Homepage
    """
    check = True if "username" in session else False
    print(check)
    if "username" in session:
        return redirect("dashboard")
    else:
        return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Shows the current Loginpage
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", info="User does not exist or wrong password.")
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Shows the current Registerpage
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user:
            return render_template("register.html", info="User already exists!")
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('login'))
    else:
        return render_template("register.html")

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if "username" in session:
        if request.method == "POST":
            city_name = request.form['city']
            
            if city_name == None or city_name == "":
                city_name="Bad Nauheim"
            
            fetch_api = API()
            data = fetch_api.getDashboardInfoAsJSON(city=city_name)
            print(data)
            
            weekDays = fetch_api.getWeekdaysAsList()
            print(weekDays)
            
            if data != None:
                return render_template("dashboard.html", username=session["username"], weather=data, day=weekDays)
            else:
                data = fetch_api.getDashboardInfoAsJSON(city="Bad Nauheim")
                errorMsg = "City was not found."
                return render_template("dashboard.html", username=session["username"], weather=data, day=weekDays, error=errorMsg)
        else:
            city_name="Bad Nauheim"
            
            fetch_api = API()
            data = fetch_api.getDashboardInfoAsJSON(city=city_name)
            print(data)
            
            weekDays = fetch_api.getWeekdaysAsList()
            print(weekDays)
            
            return render_template("dashboard.html", username=session["username"], weather=data, day=weekDays)
    else:
        return redirect("login")

@app.route('/getusers', methods=['GET'])
def get_users():
    """
    Shows all users in a json
    """
    return db.getUsers(), 201, {'ContentType':'application/json'}

@app.route('/logout', methods=['GET'])
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)
    