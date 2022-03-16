# Solve all 15 levels!
Python word game with a terminal text-based interface.  Another Wordle Knockoff... AWKword!

# Installation Requirements:
Python 3 - https://www.python.org/

pandas - https://pandas.pydata.org/

Extract all files above to a single folder and from terminal command line enter:  "python3 awkword.py"

![Screenshot from 2022-03-15 16-47-22](https://user-images.githubusercontent.com/101674931/158484934-eb48f7c7-fb89-4212-ab2a-726753c9a542.png)

# Notes

The dictionary consists of 47,325 words and includes a "frequency index" derived from Google's Ngram data, which they've been kind enough to make available for free.  The frequency index is used as a difficulty metric for target words; less-frequently used words appear in higher game levels.  The dictionary for this game has been filtered to exclude proper nouns (common names, countries, products, etc.).  In addition to Google's Ngram frequency data, other open source dictionaries (WordNet, etc.) were used to filter for commonality and validity.
