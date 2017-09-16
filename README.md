# ZR Manual Search Slack Bot
[lyneca.github.io/zrbot](https://lyneca.github.io/zrbot)  
A slack command bot that searches the Zero Robotics Game Manual

## Installation
Click the Add to Slack button above!

## Usage
- `/zr-manual help` for help
- `/zr-manual list` to list topics
- `/zr-manual [topic]` to search for a topic

### Topics
Topics are searchable by section number and by title.  
`/zr-manual list` lists all topics that are searchable.

### Timeouts
The bot is [currently] hosted on a Heroku free dyno.
This means that if there is no activity after half an hour, the dyno will go to sleep.
If you get timeout errors, just try the command again and it should work.

## Privacy
This bot is a Slack command bot. It is _only_ sent the words that you use after the command.
For example, if you send `/zr-manual fuel`, the server will only be sent the word `fuel`, along with 
some metadata about the team name and the username who used the command. No other information is sent.
