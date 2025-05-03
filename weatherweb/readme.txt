Hier wird Visual Studio Code verwendet.

Schritt 1:

Um die Seite austesten zu können, müssen Sie sich einen API Key von OpenWeatherMap erstellen und dazu einen neuen Account machen.

Link zu openweathermap: https://openweathermap.org/

Schritt 2:

Wir haben den repository installiert und extrahiert. Nun sind wir im Verzeichnis \School_Project.
Erstellen Sie einen [ .venv ] Ordner (Virtual Environment für die Python packages) im Verzeichnis und gehen Sie mit dem Befehl: [ .venv/Scripts/activate ] in den venv scope hinein.
Installieren sie mit dem Befehl: [ pip install -r requirements.txt ] die vorgegebenen requirements, die im Verzeichnis zu finden ist.

Tipp: Hier könnte die Extension [ Python Environment Manager ] nützlich sein.

Schritt 3:

Fügen sie im aktuellen Verzeichnis [ \School_Project ] eine .env hinzu und fügen Sie den unten mitgegebenen Text hinzu. Ersetzen Sie [Insert API Key] mit ihrem API Key.

Text:

web_api_key = [Insert API Key]
web_api_endpoint_raw_data = https://api.openweathermap.org
web_api_endpoint_map_data = https://tile.openweathermap.org/map

Schritt 4:

Starten Sie die Python Datei app.py, im [ \School_Project\weatherweb ] Verzeichnis, mit dem Befehl: [ python app.py ] im Terminal.