# TriviaTumbleBot (@TriviaTumbleBot on Telegram)
This bot is designed for answer collation for Trivia Tumble via Telegram, inspired by Quizarium.

---

## Using the bot as an admin
There are two stages to the administration:
1. Starting / joining a session
Each session can only have 1 active admin, to prevent double pressing buttons and generally confusing behaviour if too many people are controlling the session at once. Starting can be called with `/zastart <session ID> <rounds> <questions>`, and joining can be done by `/zajoin <session ID>`
  
2. Managing a session
To enter the managing state, the admin needs to be an active admin of a session. The entry point to this conversation is `/zamanage`.

When managing the session, the admin can:
  1. Navigate between questions and rounds
  2. Open and close questions / reviews
  3. Get scores and update scores

Questions and reviews need to be open to enable answering by participants.

At the end of each round, the bot will generate an answer file, which is a tab delimited txt file. This can be opened using good ol trusty Notepad, or Excel (or OpenOffice Calc), and the scores have to be entered manually at the end of the line for each player. Scores will then be updated by sending the bot the updated score file.

---

## Using the bot as a player
Being a player is thankfully much simpler.

Players simply have to use `/join <session ID>` to join a session, and wait for admins to open or close questions and reviews. When they are open, players just have to type their answers in. However, for the review, players have to precede their answers with the number of the question they want to change their current answer to, e.g. `6 Madagascar`

Players can use the `/check` and `/score` commands to check their answers for the current round and to check their total score respectively.

