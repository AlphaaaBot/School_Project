from datetime import datetime

# Create a datetime object
date = datetime.now()

# Define a list of weekday names
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Get the weekday name
print(f"Day number: {date.weekday()}")

weekDays = []
i = 0
for day in days:
    print(i)
    index = (date.weekday() + i) % len(days)
    weekday_name = days[index]
    weekDays.append(weekday_name)
    i += 1

print(weekDays)