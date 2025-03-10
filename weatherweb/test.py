from datetime import datetime, timedelta

# Create a datetime object
#date = datetime.now().strftime("%d/%m/%Y")
date = datetime.now()

print(date.strftime("%d/%m/%Y"))

date = date + timedelta(days=4)

print(date.strftime("%d/%m/%Y"))