# trivia_tumble_bot
This bot is to be used for answer collation for the trivia game Trivia Tumble.

The admin will:

1. Create a session, with a session ID
2. Start a question, with round number and question number. This will cause the bot to start polling for replies from participants.
3. Close the poll. This will cause the bot to stop polling.
4. The admin will then be able to access a file to read the answers, and score the participants.

The participant should be able to:

1. Join a session based on a session ID.
2. Receive a message when the polling starts, which should contain the round and question number.
3. Receive a message when the polling closes.

Possible QOL things to include:

1. Allow the bot to read a file with scores, and send a message of scores to participants either when the round ends or the participant requests such.

