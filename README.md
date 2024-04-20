# Welcome to TriviaKing!

In our root directory you can find:

 - dev - the code of our project
 - docs - the instructions file and ChatGPT conversations

This program was developed for **Python 3.11**, it is highly recommended to run it using that version.

### Submitters:
| name                | Id        |
|---------------------|-----------|
| Gal Kabosh          | 208017889 |
| Shaked Matityahu    | 206961997 |
| Michael Haim Tzahi  | 208612812 |

## Our coolest features
 - To allow the client to tell the difference between types of messages from the client, each TCP message from the server begins with an opcode, which is then translated to respond to the specific message type. The client also uses this once to let the server know whether it's a human or a bot.
 - We do not have constants in our code! Every crucial cosntant that the server or the client run is defined in dictionaries in the dedicated config.py file. The same applies for the questions and answers, defined in their own QandA.py file, for easy modification of the Q&As.
 - We can run as many bots as you'd like! Given a number as an argument, the MultiBot.py file can run that many bots simultaneously!
 - Bots are too stupid or too smart? we can change that! In our config.py file you can set the "level" of the bots from 0 (always wrong) to 10 (always right).
