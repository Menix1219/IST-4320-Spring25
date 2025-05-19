import time

def main():
    # Step 1: Ask for the reminder message.
    message = input("What shall I remind you about? ")

    # Step 2: Ask for the number of minutes to wait.
    minutes_input = input("In how many minutes? ")

    try:
        # Convert the input into a float (you can allow fractional minutes too)
        minutes = float(minutes_input)
    except ValueError:
        print("Please enter a valid number for minutes.")
        return

    # Step 3: Convert minutes to seconds.
    seconds = minutes * 60
    print(f"Reminder set! I will remind you about '{message}' in {minutes} minute(s).")

    # Step 4: Wait for the specified amount of time.
    time.sleep(seconds)

    # Step 5: Display the reminder.
    print("\n--- Reminder ---")
    print(message)
    print("----------------")

if __name__ == '__main__':
    main()
