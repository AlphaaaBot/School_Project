Schritt 1:

Um die Seite austesten zu können, müssen Sie sich einen API Key von OpenWeatherMap erstellen und dazu einen neuen Account machen.

Link zu openweathermap: https://openweathermap.org/

Schritt 2:

Erstellen Sie eine .venv datei und installieren sie mit dem Befehl: [ pip install -r requirements.txt ] die vorgegebenen requirements, die im Verzeichnis zu finden ist.

Schritt 3:

Fügen sie im aktuellen Verzeichnis eine .env hinzu und fügen Sie den unten mitgegebenen Text hinzu. Ersetzen Sie [Insert API Key] mit ihrem API Key.

Text:

web_api_key = [Insert API Key]
web_api_endpoint_raw_data = https://api.openweathermap.org
web_api_endpoint_map_data = https://map.openweathermap.org

Schritt 4:

Starten Sie die Python Datei app.py mit dem Befehl im weatherweb Verzeichnis: [ python app.py ]