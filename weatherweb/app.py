# Made by AlphaaaBot
# this script shows a web page and gets the current weather state from the given city

import os
import pytz
import bcrypt
import folium
import json
import requests
from datetime import datetime, timedelta
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
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.permanent_session_lifetime = timedelta(days=1)
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

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    theme = db.Column(db.String(20), default="light")
    icons = db.Column(db.String(20), default="outline")
    favorite_cities = db.Column(db.Text, nullable=True)
    preferred_units = db.Column(db.String(10), default="metric")
    temperature = db.Column(db.Boolean, default=True)
    cloud = db.Column(db.Boolean, default=True)
    wind = db.Column(db.Boolean, default=True)
    sea = db.Column(db.Boolean, default=True)
    precipitation = db.Column(db.Boolean, default=True)
    
    # relation to user
    user = db.relationship('User', backref=db.backref('settings', uselist=False))
    
    def setFavoriteCities(self, cities):
        self.favorite_cities = json.dumps(cities)

    def getFavoriteCities(self):
        return json.loads(self.favorite_cities) if self.favorite_cities else []

def createUser(username, password):
    new_user = User(username=username)
    new_user.set_password(password=password)
    db.session.add(new_user)
    db.session.commit()
    
    new_settings = UserSettings(user_id=new_user.id)
    db.session.add(new_settings)
    db.session.commit()
    
def addFavoriteCity(username, city_name):
    user = User.query.filter_by(username=username).first()
    user_settings = UserSettings.query.filter_by(user_id=user.id).first()
    
    if user_settings is None:
        user_settings = UserSettings(user_id=user.id, favorite_cities=json.dumps([city_name]))
        db.session.add(user_settings)
    else:
        favorite_cities = user_settings.getFavoriteCities()
        if city_name not in favorite_cities:
            favorite_cities.append(city_name)
            user_settings.setFavoriteCities(favorite_cities)
    
    db.session.commit()

def removeFavoriteCity(username, city_name):
    user = User.query.filter_by(username=username).first()
    user_settings = UserSettings.query.filter_by(user_id=user.id).first()
    
    if user_settings:
        favorite_cities = user_settings.getFavoriteCities()
        if city_name in favorite_cities:
            favorite_cities.remove(city_name)
            user_settings.setFavoriteCities(favorite_cities)
            db.session.commit()

def getAllSettings():
        user = User.query.filter_by(username=session["username"]).first()
        user_settings = UserSettings.query.filter_by(user_id=user.id).first()
        
        settings_list = {}
        
        preferred_units = user_settings.preferred_units
        settings_list.update({"preferred_units":preferred_units})
        theme = user_settings.theme
        settings_list.update({"theme":theme})
        icons_folder = user_settings.icons
        settings_list.update({"icons_folder":icons_folder})
        temperature = user_settings.temperature
        settings_list.update({"temperature":temperature})
        cloud = user_settings.cloud
        settings_list.update({"cloud":cloud})
        wind = user_settings.wind
        settings_list.update({"wind":wind})
        sea = user_settings.sea
        settings_list.update({"sea":sea})
        precipitation = user_settings.precipitation
        settings_list.update({"precipitation":precipitation})
        
        return settings_list

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
        print(f"Map Data Endpoint: {self.web_api_endpoint_map_data}")

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
    def getDateAndTimeFromString(self, datetime_str):
        current_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        current_time = current_datetime.strftime('%H:%M')
        current_date = current_datetime.strftime('%d/%m/%Y')
        obj_datetime = {"date":current_date, "time":current_time}
        return obj_datetime
    
    def getCurrentLocaleTimeAndDate(self, longitude, latitude):
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=longitude, lat=latitude)
        timezone = pytz.timezone(timezone_str)
        current_time = datetime.now(timezone).strftime('%H:%M')
        current_date = datetime.now(timezone).strftime("%d/%m/%Y")
        obj_datetime = {"date":current_date, "time":current_time}
        return obj_datetime
    
    def isDateTimeTheSame(self, given_datetime, day=0):
        current_datetime = datetime.now()
        current_datetime = current_datetime + timedelta(days=int(day))
        current_datetime = current_datetime.strftime("%d/%m/%Y")
        if current_datetime == given_datetime:
            return True
        else:
            return False
    
    def getWeekDayName(self, index=0):
        """This function gives you the current day - or + the index and returns it as a string
        
        Args:
            index (int, optional): index for weekday. Defaults to 0, meaning current day

        Returns:
            str: weekday
        """
        date = datetime.now()
        # get day from List with added index
        index = (date.weekday() + index) % len(self.days)
        weekday_name = self.days[index]
        return weekday_name
    
    def getWeekdaysAsList(self):
        """
        Returns:
            list<string>: weekdays in a list starting with the current day
        """
        date = datetime.now()
        weekDays = []
        i = 0
        for day in self.days:
            index = (date.weekday() + i) % len(self.days)
            weekday_name = self.days[index]
            weekDays.append(weekday_name)
            i += 1
            
        return weekDays
    
    # APICALLS
    def saveTilesMap(self, city_lat, city_lon, layer_name):
        m = folium.Map(location=[city_lat, city_lon], zoom_start=5)
        
        attr_name = 'OpenWeatherMap'
        folium_name = None
        
        # OpenWeatherMap Tile Layer
        match layer_name:
            case 'temp':
                tiles_url = f'{self.web_api_endpoint_map_data}/temp_new/{{z}}/{{x}}/{{y}}.png?appid={self.web_api_key}'
                folium_name = "Weather Temperature"
            case 'cloud':
                tiles_url = f'{self.web_api_endpoint_map_data}/clouds_new/{{z}}/{{x}}/{{y}}.png?appid={self.web_api_key}'
                folium_name = "Weather Cloud"
            case 'wind':
                tiles_url = f'{self.web_api_endpoint_map_data}/wind_new/{{z}}/{{x}}/{{y}}.png?appid={self.web_api_key}'
                folium_name = "Weather Wind"
            case 'pressure':
                tiles_url = f'{self.web_api_endpoint_map_data}/pressure_new/{{z}}/{{x}}/{{y}}.png?appid={self.web_api_key}'
                folium_name = "Weather Pressure"
            case 'precipitation':
                tiles_url = f'{self.web_api_endpoint_map_data}/precipitation_new/{{z}}/{{x}}/{{y}}.png?appid={self.web_api_key}'
                folium_name = "Weather Precipitation"
            
        folium.TileLayer(
            tiles=tiles_url,
            attr=attr_name,
            name=folium_name
        ).add_to(m)
        
        save_name = f"./static/maps/{layer_name}map.html"
        m.save(save_name)
        
    def saveAllTilesMapsAsHtml(self, city_lat, city_lon):
        map_list = ['temp', 'cloud', 'wind', 'pressure', 'precipitation']
        
        for layer_name in map_list:
            self.saveTilesMap(city_lat=city_lat, city_lon=city_lon, layer_name=layer_name)
    
    def getWeatherInCityForcastAsJSON(self, city, preferred_units):
        url = f"{self.web_api_endpoint_raw_data}/data/2.5/forecast?units={preferred_units}&q={city}&appid={self.web_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        
        return None
        
    def getCurrentWeatherInCityAsJSON(self, city, preferred_units):
        url = f"{self.web_api_endpoint_raw_data}/data/2.5/weather?units={preferred_units}&q={city}&appid={self.web_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        
        return None
    
    def getWeatherIconCode(self, city):
        preferred_units = "metric"
        
        if session["username"] != "Guest":
            settings_list = getAllSettings()
            preferred_units = settings_list["preferred_units"]
            
        data = self.getCurrentWeatherInCityAsJSON(city, preferred_units)
        return data["weather"]["icon"] if not data == None else None
    
    def getDashboardInfoAsJSON(self, city):
        preferred_units = "metric"
        
        if session["username"] != "Guest":
            settings_list = getAllSettings()
            preferred_units = settings_list["preferred_units"]
            
        data = self.getCurrentWeatherInCityAsJSON(city, preferred_units)
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
            weather_dashboard_obj.update({"lon":str(data["coord"]["lon"])})
            weather_dashboard_obj.update({"lat":str(data["coord"]["lat"])})
            weather_dashboard_obj.update({"time":str(obj_datetime["time"])})
            weather_dashboard_obj.update({"date":str(obj_datetime["date"])})
            weather_dashboard_obj.update({"timezone":str(data["timezone"])})
            # name
            weather_dashboard_obj.update({"name":str(data["name"])})
        
            return weather_dashboard_obj
        else:
            return None
    
    def getDashboardForecastInfoAsJSON(self, city, days=0):
        preferred_units = "metric"
        
        if session["username"] != "Guest":
            settings_list = getAllSettings()
            preferred_units = settings_list["preferred_units"]
        
        data = self.getWeatherInCityForcastAsJSON(city, preferred_units)
        current_time = datetime.now().strftime('%H:%M')
        
        if data != None:
            weather_list = []
            counter = 0
            while counter < int(data["cnt"]):
                weather_dashboard_obj = {}
                
                is_time_okay = True
                if days == 0:
                    is_time_okay = not current_time > obj_datetime["time"] and days == 0    
                
                # timezone
                obj_datetime = self.getDateAndTimeFromString(data["list"][counter]["dt_txt"])
                if self.isDateTimeTheSame(given_datetime=obj_datetime["date"], day=days) and is_time_okay:
                    weather_dashboard_obj.update({"date":str(obj_datetime["date"])})
                    weather_dashboard_obj.update({"time":str(obj_datetime["time"])})
                    
                    # weather
                    weather_dashboard_obj.update({"icon":str(data["list"][counter]["weather"][0]["icon"])})
                    weather_dashboard_obj.update({"main":str(data["list"][counter]["weather"][0]["main"])})
                    weather_dashboard_obj.update({"description":str(data["list"][counter]["weather"][0]["description"])})
                    
                    # main
                    temp = int(data["list"][counter]["main"]["temp"])
                    feels_like = int(data["list"][counter]["main"]["feels_like"])
                    weather_dashboard_obj.update({"temp":str(temp)})
                    weather_dashboard_obj.update({"feels_like":str(feels_like)})
                    weather_dashboard_obj.update({"humidity":str(data["list"][counter]["main"]["humidity"])})
                    
                    # wind
                    weather_dashboard_obj.update({"speed":str(data["list"][counter]["wind"]["speed"])})
                    
                    # clouds
                    weather_dashboard_obj.update({"all":str(data["list"][counter]["clouds"]["all"])})
                    
                    # sys
                    weather_dashboard_obj.update({"country":str(data["city"]["country"])})
                    weather_dashboard_obj.update({"name":str(data["city"]["name"])})
                    weather_dashboard_obj.update({"lat":str(data["city"]["coord"]["lat"])})
                    weather_dashboard_obj.update({"lon":str(data["city"]["coord"]["lon"])})
                    weather_dashboard_obj.update({"sunrise":str(data["city"]["sunrise"])})
                    weather_dashboard_obj.update({"sunset":str(data["city"]["sunset"])})
                    
                    # name
                    weather_dashboard_obj.update({"name":str(data["city"]["name"])})
                    weather_dashboard_obj.update({"count":str(counter)})
                    
                    
                    weather_list.append(weather_dashboard_obj)
                
                counter+=1    
            return weather_list
        
        return None
    
    def getDashboardForecastForOneOfAllDatesInfoAsJSON(self, city):
        preferred_units = "metric"
        
        if session["username"] != "Guest":
            settings_list = getAllSettings()
            preferred_units = settings_list["preferred_units"]
            
        data = self.getWeatherInCityForcastAsJSON(city, preferred_units)
        if data != None:
            weather_list = []
            counter = 0
            time_counter = 0
            days = 1
            
            while counter < int(data["cnt"]):
                weather_dashboard_obj = {}
                
                # timezone
                obj_datetime = self.getDateAndTimeFromString(data["list"][counter]["dt_txt"])
                if self.isDateTimeTheSame(given_datetime=obj_datetime["date"], day=days):
                    if time_counter == 3:
                        weather_dashboard_obj.update({"date":str(obj_datetime["date"])})
                        weather_dashboard_obj.update({"time":str(obj_datetime["time"])})
                        
                        # weather
                        weather_dashboard_obj.update({"icon":str(data["list"][counter]["weather"][0]["icon"])})
                        weather_dashboard_obj.update({"main":str(data["list"][counter]["weather"][0]["main"])})
                        weather_dashboard_obj.update({"description":str(data["list"][counter]["weather"][0]["description"])})
                        
                        # main
                        temp = int(data["list"][counter]["main"]["temp"])
                        feels_like = int(data["list"][counter]["main"]["feels_like"])
                        weather_dashboard_obj.update({"temp":str(temp)})
                        weather_dashboard_obj.update({"feels_like":str(feels_like)})
                        weather_dashboard_obj.update({"humidity":str(data["list"][counter]["main"]["humidity"])})
                        
                        # wind
                        weather_dashboard_obj.update({"speed":str(data["list"][counter]["wind"]["speed"])})
                        
                        # clouds
                        weather_dashboard_obj.update({"all":str(data["list"][counter]["clouds"]["all"])})
                        
                        # sys
                        weather_dashboard_obj.update({"country":str(data["city"]["country"])})
                        weather_dashboard_obj.update({"name":str(data["city"]["name"])})
                        weather_dashboard_obj.update({"lat":str(data["city"]["coord"]["lat"])})
                        weather_dashboard_obj.update({"lon":str(data["city"]["coord"]["lon"])})
                        weather_dashboard_obj.update({"sunrise":str(data["city"]["sunrise"])})
                        weather_dashboard_obj.update({"sunset":str(data["city"]["sunset"])})
                        
                        # name
                        weather_dashboard_obj.update({"name":str(data["city"]["name"])})
                        weather_dashboard_obj.update({"count":str(counter)})
                        weather_dashboard_obj.update({"day":str(days)})
                        
                        
                        weather_list.append(weather_dashboard_obj)
                        days += 1
                        time_counter = 0
                    else:
                        time_counter += 1
                
                counter+=1
            return weather_list
        
        return None
    
    def getGeolocationCity(self):
        try:
            url = 'http://ipinfo.io/json'
            response = requests.get(url)
            data = response.json()
            return data["city"]
        except:
            return None

    def isCityFavorite(self, city):
        if session["username"] != "Guest":
            user = User.query.filter_by(username=session["username"]).first()
            user_settings = UserSettings.query.filter_by(user_id=user.id).first()
            
            if user_settings:
                favorite_cities = user_settings.getFavoriteCities()
                
                for current_city in favorite_cities:
                    if current_city == city:
                        return True
                    
        return False

######################################################
# ROUTES
######################################################

@app.route('/', methods=['GET'])
def home():
    """Shows the current Homepage if logged in, then shows Loginpage

    Returns:
        Homepage: if logged in
        Loginpage: if not logged in
    """
    if "username" in session:
        return redirect("index")
    else:
        session["username"] = "Guest"
        return redirect("index")

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Shows the current Loginpage, if not already logged in

    Returns:
        Homepage: if logged in
        Loginpage: if not logged in
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["username"] = username
            return redirect(url_for('index'))
        else:
            return render_template("login.html", info="User does not exist or wrong password.")
    else:
        return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Shows the current Registerpage

    Returns:
        Registerpage: if user doesn't exist
        Loginpage: if User creation was successfull
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user:
            return render_template("register.html", info="User already exists!")
        else:
            createUser(username=username, password=password)
            
            session['username'] = username
            return redirect(url_for('login'))
    else:
        return render_template("register.html")

@app.route('/index', methods=['GET'])
def index():
    if "username" not in session:
        return redirect("/")
    
    favorite_cities = []
    city_data = []
    theme = "light"
    icons_folder = "outline"
    preferred_units = "metric"
    
    if session["username"] != "Guest":
        print(session["username"])
        
        user = User.query.filter_by(username=session["username"]).first()
        user_settings = UserSettings.query.filter_by(user_id=user.id).first()
        
        if user_settings:
            settings_list = getAllSettings()
            theme = settings_list["theme"]
            icons_folder = settings_list["icons_folder"]
            preferred_units = settings_list["preferred_units"]
            favorite_cities = user_settings.getFavoriteCities()
            
            fetch_api = API()
            
            for city in favorite_cities:                
                current_weather_data = fetch_api.getDashboardInfoAsJSON(city=city)
                city_data.append(current_weather_data)
    
    return render_template("index.html", favorite_cities=favorite_cities, username=session["username"], weather_data=city_data, icons_folder=icons_folder, preferred_units=preferred_units, theme=theme)

@app.route('/addordeletecity/<city>/<redirect_to>', methods=['POST'])
def addordeletecity(city, redirect_to):
    if "username" not in session:
        return redirect(url_for("login"))
    
    user = User.query.filter_by(username=session["username"]).first()
    user_settings = UserSettings.query.filter_by(user_id=user.id).first()
    
    if user_settings:
        favorite_cities = user_settings.getFavoriteCities()
        print(favorite_cities)
        
        city_exists = False
        for current_city in favorite_cities:
            if current_city == city:
                city_exists = True
                break
        
        if city_exists:
            print(f"removed {city}")
            removeFavoriteCity(username=session["username"], city_name=city)
        else:
            print(f"added {city}")
            addFavoriteCity(username=session["username"], city_name=city)
    
    if redirect_to == "index":
        return redirect(url_for("index"))
    else:
        return redirect(url_for("dashboard", city=city))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first()
    if not user:
        return redirect(url_for("login"))
    
    if request.method == "POST":
        user.settings.theme = request.form["theme"]
        user.settings.preferred_units = request.form["preferred_units"]
        user.settings.icons = request.form["icons"]
        user.settings.temperature = "temperature" in request.form
        user.settings.cloud = "cloud" in request.form
        user.settings.wind = "wind" in request.form
        user.settings.sea = "sea" in request.form
        user.settings.precipitation = "precipitation" in request.form
        db.session.commit()
        return redirect(url_for("settings"))

    return render_template("settings.html", user=user, theme=user.settings.theme)

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboardredirect():
    if request.method == "POST":
        city = request.form["city"]
    else:
        fetch_api = API()
        city = fetch_api.getGeolocationCity()
    
    return redirect(url_for('dashboard', city=city)) if city else redirect(url_for('index'))

@app.route('/dashboard/<city>', methods=['GET'])
def dashboard(city):
    """Shows the current Dashboard, with fetched api data for the current day and forecast to current city

    Returns:
        Homepage: if logged in
        Loginpage: if not logged in
    """
    if "username" not in session:
        return redirect(url_for("login"))

    fetch_api = API()
    
    theme = "light"
    icons_folder = "outline"
    preferred_units = "metric"
    temperature, cloud, wind, sea, precipitation = True, True, True, True, True
    
    if session["username"] != "Guest":
        settings_list = getAllSettings()
        theme = settings_list["theme"]
        icons_folder = settings_list["icons_folder"]
        temperature = settings_list["temperature"]
        cloud = settings_list["cloud"]
        wind = settings_list["wind"]
        sea = settings_list["sea"]
        precipitation = settings_list["precipitation"]
        preferred_units = settings_list["preferred_units"]
    
    maps_list = [temperature, cloud, wind, sea, precipitation]
    
    are_all_maps_turned_off = True
    for map in maps_list:
        if map:
            are_all_maps_turned_off = False
            break
    
    weather_maps = [
        {"title": "Temperature", "url": "/static/maps/tempmap.html", "active": temperature},
        {"title": "Cloud Coverage", "url": "/static/maps/cloudmap.html", "active": cloud},
        {"title": "Wind", "url": "/static/maps/windmap.html", "active": wind},
        {"title": "Sea Level Pressure", "url": "/static/maps/pressuremap.html", "active": sea},
        {"title": "Precipitation", "url": "/static/maps/precipitationmap.html", "active": precipitation},
    ]

    if request.method == "GET":
        data = fetch_api.getDashboardInfoAsJSON(city)
        if not data:
            city = fetch_api.getGeolocationCity() or "Bad Nauheim"
            data = fetch_api.getDashboardInfoAsJSON(city)
            errorMsg = "City was not found and was set to default."
        else:
            errorMsg = None
        
        is_favorite = fetch_api.isCityFavorite(city)
        data_forecast = fetch_api.getDashboardForecastForOneOfAllDatesInfoAsJSON(city)
        weekDays = fetch_api.getWeekdaysAsList()
        fetch_api.saveAllTilesMapsAsHtml(city_lat=data["lat"], city_lon=data["lon"])

        return render_template("dashboard.html", username=session["username"], weatherData=data, weatherDataForecast=data_forecast, day=weekDays, 
                               city=city, weather_maps=weather_maps, error=errorMsg, is_favorite=is_favorite, icons_folder=icons_folder, 
                               preferred_units=preferred_units, theme=theme, are_all_maps_turned_off=are_all_maps_turned_off)

@app.route('/dashboardforecast/<city>/<day>', methods=['GET'])
def dashboardforecast(city, day):
    """Shows the current Dashboardforecast, with fetched api data for the current day to current city

    Returns:
        Homepage: if logged in
        Loginpage: if not logged in
    """
    if "username" not in session:
        return redirect("login")
    
    fetch_api = API()
    
    theme = "light"
    icons_folder = "outline"
    preferred_units = "metric"
    
    if session["username"] != "Guest":
        user = User.query.filter_by(username=session["username"]).first()
        user_settings = UserSettings.query.filter_by(user_id=user.id).first()
        settings_list = getAllSettings()
        theme = settings_list["theme"]
        icons_folder = settings_list["icons_folder"]
        preferred_units = settings_list["preferred_units"]
        
    if request.method == "GET":
        city_name = city
        
        if city_name == None or city_name == "":
            city_name = fetch_api.getGeolocationCity() or "Bad Nauheim"
        
        data = fetch_api.getDashboardForecastInfoAsJSON(city=city_name, days=day)
        
        weekDays = fetch_api.getWeekdaysAsList()
        
        if int(day) == 0:
            data_today = fetch_api.getDashboardInfoAsJSON(city=city_name)
            return render_template("dashboardforecast.html", username=session["username"], weatherData=data, weatherDataToday=data_today, is_today=True, 
                                   day=weekDays, city=city_name, button_pressed=day, icons_folder=icons_folder, preferred_units=preferred_units, theme=theme)
        else:
            return render_template("dashboardforecast.html", username=session["username"], weatherData=data, day=weekDays, city=city_name, 
                                   button_pressed=day, icons_folder=icons_folder, preferred_units=preferred_units, theme=theme)

@app.route('/logout', methods=['GET'])
def logout():
    """Logs the user out of the site

    Returns:
        Loginpage: Normally
    """
    session.pop("username", None)
    return redirect("login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)
    