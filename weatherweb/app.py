# Made by AlphaaaBot
# this script shows a web page and gets the current weather state from the given city

import os
import pytz
import bcrypt
import folium
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
    def getDateAndTimeFromString(self, datetime_str):
        print(f"Datetime string: {datetime_str}")
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
        print(f"day in method: {day}")
        current_datetime = current_datetime + timedelta(days=int(day))
        print(f"What?: {given_datetime}")
        current_datetime = current_datetime.strftime("%d/%m/%Y")
        print(f"Current date with timedelta added: {current_datetime}")
        print(f"Given date From API: {given_datetime}")
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
        print(weekday_name)
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
    
    def getWeatherInCityForcastAsJSON(self, city):
        url = f"{self.web_api_endpoint_raw_data}/data/2.5/forecast?units=metric&q={city}&appid={self.web_api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
        
        return None
        
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
        data = self.getWeatherInCityForcastAsJSON(city)
        if data != None:
            weather_list = []
            print("---------------------")
            counter = 0
            while counter < int(data["cnt"]):
                #note: need to make sure it has an index for html
                print("\n")
                print(counter)
                print("\n")
                
                weather_dashboard_obj = {}
                
                # timezone
                obj_datetime = self.getDateAndTimeFromString(data["list"][counter]["dt_txt"])
                print(f"Given From API: {obj_datetime["date"]}")
                if self.isDateTimeTheSame(given_datetime=obj_datetime["date"], day=days):
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
                
            print("---------------------\n")
            return weather_list
        
        return None

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
    check = True if "username" in session else False
    print(check)
    if "username" in session:
        return redirect("dashboard")
    else:
        return render_template("login.html")

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
            session['username'] = username
            return redirect(url_for('dashboard'))
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
    """Shows the current Homepage, with fetched api data to current city

    Returns:
        Homepage: if logged in
        Loginpage: if not logged in
    """
    if "username" in session:
        
        fetch_api = API()
        
        weather_maps = [
            {"title": "Temperature", "url": "/static/maps/tempmap.html"},
            {"title": "Cloud Coverage", "url": "/static/maps/cloudmap.html"},
            {"title": "Wind", "url": "/static/maps/windmap.html"},
            {"title": "Sea Level Pressure", "url": "/static/maps/pressuremap.html"},
            {"title": "Precipitation", "url": "/static/maps/precipitationmap.html"},
        ]
        
        if request.method == "POST":
            current_error = False
            
            city_name = request.form['city']
            
            data = fetch_api.getDashboardInfoAsJSON(city=city_name)
            
            if data == None:
                current_error = True
                city_name="Bad Nauheim"
                data = fetch_api.getDashboardInfoAsJSON(city=city_name)
            
            fetch_api.saveAllTilesMapsAsHtml(city_lat=data["lat"], city_lon=data["lon"])
            print("saved map html")
            
            weekDays = fetch_api.getWeekdaysAsList()
            print(weekDays)
            
            if data != None and not current_error:
                return render_template("dashboard.html", username=session["username"], weatherData=data, day=weekDays, city=city_name, weather_maps=weather_maps)
            else:
                data = fetch_api.getDashboardInfoAsJSON(city="Bad Nauheim")
                errorMsg = "City was not found."
                
                fetch_api.saveAllTilesMapsAsHtml(city_lat=data["lat"], city_lon=data["lon"])
                print("saved map html")

                return render_template("dashboard.html", username=session["username"], weatherData=data, day=weekDays, city=city_name, weather_maps=weather_maps, error=errorMsg)
            
        else:
            city_name = ""
            
            if city_name == None or city_name == "":
                city_name = "Bad Nauheim"
            
            data = fetch_api.getDashboardInfoAsJSON(city=city_name)
            print(data)
            
            fetch_api.saveAllTilesMapsAsHtml(city_lat=data["lat"], city_lon=data["lon"])
            print("saved map html")
            
            weekDays = fetch_api.getWeekdaysAsList()
            print(weekDays)
            
            if data != None:
                return render_template("dashboard.html", username=session["username"], weatherData=data, day=weekDays, city=city_name, weather_maps=weather_maps)
            else:
                # setting to default city
                city_name = "Bad Nauheim"
                
                data = fetch_api.getDashboardInfoAsJSON(city=city_name)
                errorMsg = "City was not found."
                
                fetch_api.saveAllTilesMapsAsHtml(city_lat=data["lat"], city_lon=data["lon"])
                print("saved map html")
                
                return render_template("dashboard.html", username=session["username"], weatherData=data, day=weekDays, city=city_name, weather_maps=weather_maps, error=errorMsg)
    else:
        return redirect("login")

@app.route('/dashboardforecast/<city>/<day>', methods=['GET'])
def dashboardforecast(city, day):
    """Shows the current Homepage, with fetched api data for the current day to current city

    Returns:
        Homepage: if logged in
        Loginpage: if not logged in
    """
    if "username" in session:
        
        fetch_api = API()
        
        if request.method == "GET":
            city_name = city
            
            if city_name == None or city_name == "":
                city_name="Bad Nauheim"
            
            data = fetch_api.getDashboardForecastInfoAsJSON(city=city_name, days=day)
            print(data)
            
            weekDays = fetch_api.getWeekdaysAsList()
            print(weekDays)
            
            if int(day) == 0:
                data_today = fetch_api.getDashboardInfoAsJSON(city=city_name)
                return render_template("dashboardforecast.html", username=session["username"], weatherData=data, weatherDataToday=data_today, is_today=True, day=weekDays, city=city_name)
            else:
                return render_template("dashboardforecast.html", username=session["username"], weatherData=data, day=weekDays, city=city_name)
    else:
        return redirect("login")

#########################################################################
# What is this for?
@app.route('/getusers', methods=['GET'])
def get_users():
    """
    Shows all users in a json
    """
    return db.getUsers(), 201, {'ContentType':'application/json'}

#########################################################################

@app.route('/settings', methods=['GET'])
def settings():
    return redirect(url_for("settings"))


@app.route('/logout', methods=['GET'])
def logout():
    """Logs the user out of the site

    Returns:
        Loginpage: Normally
    """
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='127.0.0.1', port=5000, debug=True)
    