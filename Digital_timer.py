import time  # Importing time module for using sleep to create the countdown effect

# Prompt user to enter the duration of the timer (e.g., "10 sec", "5 min", "1 hr")
a = input("Timer duration (e.g., '10 sec', '5 min', '1 hr'): ").lower().strip()

# Split the input into two parts: number and time unit
parts = a.split()

# Validate input: must be exactly 2 parts and first part should be a digit
if len(parts) != 2 or not parts[0].isdigit():
    print("Invalid input format. Use formats like '10 sec', '5 min', or '1 hr'.")
    exit()

# Extract the numeric part and convert it to integer
b = int(parts[0])

# Extract the time unit (sec, min, or hr)
unit = parts[1]

# Convert input time to total seconds based on the unit
if unit == "sec":
    total_seconds = b
elif unit == "min":
    total_seconds = b * 60
elif unit == "hr":
    total_seconds = b * 3600
else:
    # Handle invalid time unit
    print("Invalid time unit. Use 'sec', 'min', or 'hr'.")
    exit()

# Countdown loop: starts from total_seconds and counts down to 1
for y in range(total_seconds, 0, -1):
    # Calculate hours, minutes, and seconds from remaining time
    hr = y // 3600
    min = (y % 3600) // 60
    sec = y % 60
    
    # Display time in hh:mm:ss format, overwriting the previous line with '\r'
    print(f"{hr:02}:{min:02}:{sec:02}", end="\r")
    
    # Wait for 1 second before continuing the countdown
    time.sleep(1)

# Print final message when countdown is complete
print("\nTIME'S UP")
