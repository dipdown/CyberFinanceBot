import time
import pexpect
import psutil

while True:
    # Start the main.py script
    process = pexpect.spawn("python3 main.py")

    # Wait for the script to display the menu and expect user input
    process.expect("Select an action:", timeout=30)  # Adjust the prompt as needed

    # Send the choice "2" and then Enter
    process.sendline("2")

    # Allow the script to run for 1 hour (3600 seconds)
    time.sleep(3600)

    # Terminate the process after 1 hour
    for proc in psutil.process_iter():
        if proc.pid == process.pid:
            proc.terminate()
            break

    # Wait for 5 seconds before restarting the script
    time.sleep(5)
