# AWKword - Another Wordle Knockoff

import pandas as pd
from time import sleep
from datetime import datetime as dt

dictionary = pd.read_pickle("dictionary16.zip")
stats = pd.read_pickle("stats.pkl")

alphabet = set('abcdefghijklmnopqrstuvwxyz')

#(Frequency Index, description)
WORD_DIFFICULTY = [(.975,1.0,"top 2.5%"),
                   (.9,1.0,"top 10%"),
                   (.75,1.0, "top 25%"),
                   (.75,.9, "less common")]

#PLAY_MODES [0-2]
PLAY_MODES = [("Easy (no constraints)"),
              ("Hard (match some clues)"),
              ("Extra Hard (match all clues)")]

#(shortest, longest, word_difficulty, play_mode, solution count, time limit in minutes)
LEVELS = [(4, 6, 0, 0, 5, 1.0),
          (4, 6, 0, 1, 5, 1.0),
          (4, 6, 0, 2, 5, 1.0),
          (4, 7, 1, 0, 5, 1.0),
          (4, 7, 1, 1, 5, 1.0),
          (4, 7, 1, 2, 5, 1.0),
          (5, 7, 1, 0, 5, 1.0),
          (5, 7, 1, 1, 5, 1.0),
          (5, 7, 1, 2, 5, 1.0),
          (5, 8, 2, 0, 5, 1.0),
          (5, 8, 2, 1, 5, 1.0),
          (5, 8, 2, 2, 5, 1.0),
          (5, 8, 3, 0, 5, 1.0),
          (5, 8, 3, 1, 5, 1.0),
          (5, 8, 3, 2, 5, 1.0)]

def start_game():
    if len(stats) > 0:  #Let's see where we left off
        start_level = stats.iloc[-1].Level #grab last level played from stats dataframe
        minutes = LEVELS[start_level-1][5] #get minutes requirement for last level played
        solution_count = LEVELS[start_level-1][4] #get solution count requirement for last level played
        solved = len(stats[(stats.Level == start_level) & (stats.Seconds < (minutes*60))])
        if solved >= solution_count:
            start_level += 1
    else:
        start_level = 1

    play_levels(start_level)

def play_levels(start_level):

    for lvl in range((start_level-1),len(LEVELS)):

        level = LEVELS[lvl] #grab the level tuple

        shortest = level[0]
        longest = level[1]
        min_frequency = WORD_DIFFICULTY[level[2]][0]
        max_frequency = WORD_DIFFICULTY[level[2]][1]
        word_desc = WORD_DIFFICULTY[level[2]][2]
        playmode = level[3]
        solution_count = level[4] #number of solutions under time limit needed to advance
        minutes = level[5] #time limit

        current_level = lvl+1
        
        min_FI = dictionary.FI.quantile(min_frequency)
        max_FI = dictionary.FI.quantile(max_frequency)

        targets = dictionary[dictionary.Target & dictionary.FI.between(min_FI, max_FI) & dictionary.Word.str.len().between(shortest,longest)]

        solved = 0
        while solved < solution_count:

            target = targets.sample().iloc[0]
            #if we've randomly picked a word that's been solved, pick another!
            while target.Word in stats.Word.values:
                target = targets.sample().iloc[0]

            #clear screen for effect
            print("\033c\033[3J", end='')
            print("| "+GREEN+"AWK"+RESET+"word - "+GREEN+"A"+RESET+"nother "+GREEN+"W"+RESET+"ordle "+GREEN+"K"+RESET+"nockoff")
            print("|==========================================")
            print("| LEVEL: "+YELLOW+str(current_level)+RESET)
            print("| Word length: "+str(shortest)+" - "+str(longest))
            print("| Answer pool: {:,}".format(len(targets))+" (frequency: "+word_desc+")")
            print("| Play mode: "+PLAY_MODES[playmode])
            print()

            seconds = play(target.Word, shortest, longest, playmode)

            if seconds > 0:   #seconds will be -1 if player entered igiveup!
                stats.loc[len(stats)] = [current_level, target.Word, word_rank(target.FI), seconds]  #append stats for current solution

            solved = len(stats[(stats.Level == (current_level)) & (stats.Seconds < (minutes*60))])

            if solved < solution_count:
                print("| You've solved "+GREEN+str(solved)+RESET+" words under "+str(minutes)+" minutes ("+str(solution_count)+" to advance)")
            else:
                print()
                print(YELLOW+"--> Congratulations!! You have advanced to the next level."+RESET)
            print()
            display_stats(current_level)
            print()

            if input("| Press enter to continue (or 'Q' to quit) ") == 'Q':
                stats.to_pickle("stats.pkl")
                quit()

    print(YELLOW+"--> Congratulations!  You have completed all levels!!!"+RESET)


#########################################################################################################################


#Main logic for providing clues in a result string same length as guess with the following:
#  . = letter not in word / lowercase = letter in word but in wrong place / uppercase = right letter right place
def word_compare(guess, target):
    result = ''

    #Fill result with indicators:  UPPERCASE = right letter right place, otherwise '.'
    for index in range(0,len(guess)):
        letter = guess[index]
        if (index < len(target)) and (target[index] == letter):
            result += letter.upper()
        else:
            result += '.'

    #Insert (lowercase) letters that are in target but wrong place in guess
    for index in range(0,len(guess)):
        letter = guess[index]
        if (result[index] == '.') and (letter in target) and (target.count(letter) > result.lower().count(letter)):
            result = result[:index]+letter.lower()+result[index+1:]

    #Return result as a string
    return result

#Compare locked list with guess - assumes both are lowercase
def lock_conflict(guess, locked):
    for position in range(0,len(locked)):
        if locked[position] != None and (position >= len(guess) or locked[position] != guess[position]):
            return True
    return False

#Return a formatted string for message to user
def display_locked(locked):
    result = ''
    for index in range (0,len(locked)):
        if locked[index] == None:
            result += FAINT_GRAY+'.'
        else:
            result += GREEN+locked[index].upper()
    result += RESET
    return result

#Check to see if any characters in guess where previously ruled out in that same position
def block_conflict(guess, blocked):
    for index in range(0,len(guess)):
        if guess[index] in blocked[index]:
            return True
    return False

#Return a formatted string for message to user
def display_blocked(guess, blocked):
    result = ''
    for index in range (0,len(guess)):
        if guess[index] in blocked[index]:
            result += YELLOW+guess[index]
        else:
            result += FAINT_GRAY+'.'
    result += RESET
    return result

#See if count of each letter in guess does not match the confirmed number of occurrences in target (based on the clues given)
def count_conflict(guess, counts, fixed_counts):
    for letter in guess:
        letter_position = ord(letter) - ord('a')
        if (letter in fixed_counts) and (guess.count(letter) != counts[letter_position]):
            return True
        elif guess.count(letter) < counts[letter_position]:
            return True
    return False

#Return a formatted string for message to user showing where their guess did not meet the count requirements
def display_counts(guess, counts, fixed_counts):
    result = []
    for letter in sorted(list(set(guess))):
        letter_position = ord(letter) - ord('a')
        if (letter in fixed_counts) and (guess.count(letter) != counts[letter_position]):
            result += [YELLOW+letter+RESET+':'+str(counts[letter_position])]
        elif guess.count(letter) < counts[letter_position]:
            result += [YELLOW+letter+RESET+':'+str(counts[letter_position])+'+']
    return ', '.join(result)

#Display clues in text boxes
#Unicode characters (in the form u'\u25XX' below) are elements for box drawing
def display_result(guess, result, longest):
    setFaintGray()
    print(u'\u250c'+u'\u2500\u252c'*(longest-1)+u'\u2500'+u'\u2510')
    print(u'\u2502',end='')
    for index in range(0,longest):
        if index < len(guess):
            r = result[index]
            if r.isupper(): #Print letter as uppercase green
                print(GREEN+r.upper()+FAINT_GRAY+u'\u2502',end='')
            elif r.islower(): #Print letter as lowercase yellow
                print(YELLOW+r+FAINT_GRAY+u'\u2502',end='')
            else:
                print(guess[index]+u'\u2502',end='')
        else:
            print(' '+u'\u2502',end='')
    print()
    print(u'\u2514'+u'\u2500\u2534'*(longest-1)+u'\u2500'+u'\u2518', end='')
    print(RESET,end='') #ANSI reset formatting
    return

def word_rank(FI):
    rank = .99
    while rank > 0:
        if FI > dictionary.FI.quantile(rank):
            return 100-round(rank*100)
        rank -= .01
    return 100

def display_stats(current_level):
    current = stats[stats.Level == current_level] #slice of stats dataframe for current level
    if len(current) < 1: return #no stats to display

    time_limit = LEVELS[current_level-1][5]*60
    print("Level :   Word   :  Rank  :  Time")
    print("--------------------------------------")
    print(" "*(3-len(str(current_level)))+YELLOW+str(current_level)+RESET+" "*5,end='')
    first = current.iloc[0]
    ts = time_string(first.Seconds, time_limit)
    print(first.Word+" "*(13-len(first.Word))+str(first.Rank)+"%"+" "*(7-len(str(first.Rank)))+ts)
    for index in range(1,len(current)):
        row = current.iloc[index]
        ts = time_string(row.Seconds, time_limit)
        print(" "*8+row.Word+" "*(13-len(row.Word))+str(row.Rank)+"%"+" "*(7-len(str(row.Rank)))+ts)

def time_string(seconds, limit):
    result = ''
    if seconds < limit:
        result += GREEN
    m, s = divmod(seconds, 60)
    result += "{:02d}".format(m)+":{:02d}".format(s)
    if seconds < limit:
        result += RESET
    return result


##Utility i/o functions and formatting variables

RESET = "\033[00m"
FAINT_GRAY = "\033[00;2m"
GREEN = "\033[00;92m"
YELLOW = "\033[00;93m"

def setFaintGray(): print(FAINT_GRAY,end='')

def error_message(msg):
    print("\033[F",end='',flush=True) # Cursor up one line
    print("--> "+msg, end='', flush=True)
    sleep(2)
    print("\r"+"\033[K", end="\r", flush=True)


################################################################################
def play(target, shortest, longest, playmode):

    print("Enter a guess:")
    print()

    guess = ''

    ruled_out = set()  #letters that have been ruled out
    confirmed_in = set()  #letters confirmed as in

    fixed_counts = set() #subset of confirmed_in letters with a known exact count (positions may or may not be yet known)
    counts = [0] * 26  #count information for all 26 letters (e.g. 'e' appears 2 or more times and 's' appears exactly once)

    locked = [None] * longest #ordered list of letter positions, filled when guess contains correct letter in correct place
    blocked = [set() for _ in range(longest)] #list of sets, each containing letters confirmed in target, but ruled out for that position

    minimum_length = shortest  #Keep track of this in case target starts with guess (e.g. guess="DRAW" and target="DRAWER")

    valid = dictionary[dictionary.Word.str.len().between(shortest,longest)]

    gaveup = False

    start = dt.now()
    while guess != target:
        guess = input('--> ').lower()
        if guess == 'igiveup!':
            gaveup = True
            if len(valid) < 50:
                print("\033[F\033[2K", end='')
                print(valid.Word.values)
                print('\n'*2)
            guess = target

        if not guess.isalpha():
            error_message("Letters only (no spaces, hyphens or numbers)")
        elif not (shortest <= len(guess) <= longest):
            error_message(str(len(guess))+" characters! Must be between "+str(shortest)+" and "+str(longest))
        elif not dictionary.Word.eq(guess).any():
            error_message("Not in dictionary")

        #Hard mode
        elif (playmode > 0) and lock_conflict(guess, locked):
            error_message("Must match the following:  "+display_locked(locked))
        elif (playmode > 0) and not confirmed_in.issubset(set(guess)):
            error_message("Must contain:  "+','.join(sorted(confirmed_in.difference(set(guess)))))
        elif (playmode > 0) and not ruled_out.isdisjoint(set(guess)):
            error_message("May not contain:  ("+','.join(sorted(ruled_out.intersection(set(guess))))+")")

        #Extra hard mode
        elif (playmode > 1) and block_conflict(guess, blocked):
            error_message("Letters blocked in these positions:  "+display_blocked(guess, blocked))
        elif (playmode > 1) and count_conflict(guess, counts, fixed_counts):
            error_message("Does not match required letter counts:  "+display_counts(guess, counts, fixed_counts))
        elif (playmode > 1) and (len(guess) < minimum_length):
            error_message("Guess must be at least "+str(minimum_length)+" characters long")

        else:  #Acceptable guess!
            result = word_compare(guess, target)
            ruled_out.update(set(guess) - set(target))
            confirmed_in.update(set(result.lower())-{'.'})
            available_letters = alphabet - ruled_out.union(confirmed_in)

            #Update locked and blocked lists
            for i in range(0,len(result)):
                if result[i].isupper():
                    locked[i] = result[i].lower()
                    if (i+1) > minimum_length: minimum_length = (i+1)
                elif result[i].islower():
                    blocked[i].add(result[i])
                elif guess[i] in confirmed_in: #extra occurrences of a confirmed_in letter rule it out for this position
                    blocked[i].add(guess[i])

            #Update minimum_length in the case target starts with guess
            if target != guess and target.startswith(guess):
                minimum_length = max(minimum_length, len(guess) + 1)

            #Update counts and fixed_counts
            hits = set(result.lower()) - {'.'}  #lowercase set of matching letters from guess
            for letter in hits:
                if letter not in fixed_counts:
                    letter_position = ord(letter) - ord('a') #find position 0-25 in counts array
                    if result.lower().count(letter) > counts[letter_position]:
                        counts[letter_position] = result.lower().count(letter)
                    if guess.count(letter) > target.count(letter):
                        fixed_counts.add(letter)

            #Show user list of ruled out and available letters
            if guess != target:
                print("\033[F", end='') # up one line
                print(' '*(longest*2 + 4)+'('+FAINT_GRAY+','.join(sorted(list(ruled_out)))+RESET+') ', end='')
                if len(confirmed_in) > 0: print(YELLOW+','.join(sorted(list(confirmed_in)))+RESET+' |', end='')
                print(' '+','.join(sorted(list(available_letters))))

            print("\033[F"*2, end='') # and up two lines
            display_result(guess,result,longest)

            if guess != target:
                #Reduce valid guesses to those that are consistent with all clues given
                #First filter for confirmed_in, ruled_out and minimum_length
                valid = valid.loc[valid.Word.apply(ruled_out.isdisjoint) & valid.Word.apply(confirmed_in.issubset) & (valid.Word.str.len() >= minimum_length)]
                #then build query for locked, blocked and counts
                q = ""
                for pos in range(0,len(result)):
                    if result[pos].isupper():
                        q += " & (Word.str["+str(pos)+"] == '"+result[pos].lower()+"')"
                    elif result[pos].islower():
                        q += " & (Word.str["+str(pos)+"] != '"+result[pos]+"')"
                    elif guess[pos] in confirmed_in:  #extra occurrences of a confirmed_in letter rule it out for this position
                        q += " & (Word.str["+str(pos)+"] != '"+guess[pos]+"')"
                for letter in confirmed_in:
                    letter_position = ord(letter) - ord('a')
                    if letter in fixed_counts:
                        q += " & (Word.str.count('"+letter+"') == "+str(counts[letter_position])+")"
                    elif counts[letter_position] > 1:  #if counts for a letter equals 1, confirmed_in filter above will catch it
                        q += " & (Word.str.count('"+letter+"') >= "+str(counts[letter_position])+")"
                if len(q) > 0:
                    q = q[3:] #drop the first ' & '
                    valid = valid.query(q, engine='python')
                current = dt.now() - start
                minutes, seconds = divmod(current.seconds, 60)
                matches = "{:,}".format(len(valid))
                print("   Possible matches: "+matches+" "*(15-len(matches))+"Time - {:02d}".format(minutes)+":{:02d}".format(seconds))
                print()

    print('\n')

    if not gaveup:
        delta = dt.now() - start
        minutes, seconds = divmod(delta.seconds, 60)
        print("| Elapsed time - "+GREEN+"{:02d}".format(minutes)+":{:02d}".format(seconds)+RESET)
        return delta.seconds
    else:
        return -1
