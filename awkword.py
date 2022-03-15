#Wrapper script to check for Python 3
import sys
if sys.version_info[0] < 3:
    print("Python 3 or later is required.")
else:
    import os
    os.system("") #enables ANSI formatting on Windows PowerShell
    import gamecode as game
    game.start_game()
