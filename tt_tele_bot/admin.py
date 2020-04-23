# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 10:10:38 2020

@author: looshua
"""

import telegram
import logging

from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, ConversationHandler,
                          CallbackQueryHandler, Filters)
from telegram import ReplyKeyboardMarkup

from functools import wraps

import player
from player import PlayerUser

LIST_OF_ADMINS = ["looshua", "marlinacco"]


class AdminUser:
    def __init__(self, update):
        self.username = update.effective_user.username
        self.chat_id = update.effective_user.id


class Session:
    IDLE, OPEN, REVIEW = range(3)

    def __init__(self, update, context):
        # admin management variables
        self.ID = int(context.args[0])
        self.active_admin = AdminUser(update)
        self.admins = [self.active_admin]

        # game management variables
        self.rounds = int(context.args[1])
        self.questions = int(context.args[2])

        self.current_round = 1
        self.current_qn = 1

        self.state = self.IDLE

        # player management variables
        self.players = []

    ''' admin management methods '''

    def check_admin_joined(self, update):
        for user in self.admins:
            if user.chat_id == update.effective_user.id:
                return True
        return False

    def add_admin(self, update):
        joined = self.check_admin_joined(update)
        if not joined:
            # if no active admin, add new joiner as active admin
            if len(self.admins) == 0:
                self.active_admin = AdminUser(update)
                self.admins.append(self.active_admin)

            # otherwise, normally add new joiner to admins
            else:
                self.admins.append(AdminUser(update))

        return not joined

    ''' player management methods '''

    def check_player_joined(self, update, id=None):
        if id is not None:
            for user in self.players:
                if user.username == id:
                    return True, user
            return False, -1

        for user in self.players:
            if user.chat_id == update.effective_user.id:
                return True, user
        return False, -1

    def add_player(self, update):
        joined, player = self.check_player_joined(update)
        if not joined:
            self.players.append(PlayerUser(update))

        return not joined

    def get_round_file(self):
        file_ls = []
        for player in self.players:
            file_ls.append(player.get_round_answers(
                self.questions, self.current_round))

        file_str = "session{}round{}ans.txt".format(
            self.ID, self.current_round)

        if len(file_ls) == 0:
            return file_str, False

        with open(file_str, 'w') as f:
            f.writelines(file_ls)
            f.close()

        return file_str, True


class MainBot:
    SELECTING_ACTION, ACTION, END_GAME = range(3)

    def __init__(self):
        self.sessions = []

        # create handlers
        self.get_session_starter()
        self.get_session_joiner()
        self.get_management_handler()
        self.get_leave_handler()
        self.get_help_handler()
        self.get_score_handler()
        self.get_checkscore_handler()

    ''' wrapper to create admin user commands '''

    def restricted(func):
        @wraps(func)
        def wrapped(self, update, context, *args, **kwargs):
            user_id = update.effective_user.username
            if user_id not in LIST_OF_ADMINS:
                print("Unauthorized access denied for {}.".format(user_id))
                return
            return func(self, update, context, *args, **kwargs)
        return wrapped

    ''' session management functions '''

    def check_session_existing(self, ID):
        ID = int(ID)
        idx = 0
        for session in self.sessions:
            if session.ID == ID:
                return True, session.ID, idx
            idx += 1

        return False, ID, idx

    def get_active_session(self, update, active=True):
        admin_found = False
        session = -1

        if not active:
            for idx in range(len(self.sessions)):
                if len(self.sessions[idx].admins) == -1:
                    break

                for admin in self.sessions[idx].admins:
                    if admin.chat_id == update.effective_user.id:
                        session = self.sessions[idx]
                        admin_found = True
                        break

            return admin_found, session

        for idx in range(len(self.sessions)):
            if self.sessions[idx].active_admin == -1:
                break

            if self.sessions[idx].active_admin.chat_id == update.effective_user.id:
                session = self.sessions[idx]
                admin_found = True
                break

        return admin_found, session

    ''' session creation callbacks '''
    # command callback for session creation

    def start_session(self, update, context):
        print('starting..')

        # check if user is already in a session
        for session in self.sessions:
            if session.check_admin_joined(update):
                update.message.reply_text(
                    text="You are already in session {}. Use /leave to leave your current session.".format(session.ID))

        # if user includes a session ID
        try:
            # check if session ID already exists
            match, ID, idx = self.check_session_existing(context.args[0])

            if match:
                update.message.reply_text(
                    text="Session with ID {} already exists. Use /zajoin <ID> to join session.".format(ID))

            else:
                self.sessions.append(Session(update, context))
                update.message.reply_text(
                    text="Session with ID {} created.".format(ID))

        # user doesnt include a session ID
        except IndexError:
            update.message.reply_text(
                text="ID not given. Use /zastart <ID> <rounds> <questions> to create session.")

        # catch all
        except ValueError:
            update.message.reply_text(
                text="ID should be an integer. Use /zastart <ID> <rounds> <questions> to create session.")

        except Exception as inst:
            print(inst)
            update.message.reply_text(text="Error in command.")

    startSession = restricted(start_session)

    def get_session_starter(self):
        self.session_handler = CommandHandler('zastart', self.startSession)

    # command callback for session joining
    def join_session(self, update, context):
        print('joining..')

        # check if user is already in a session
        for session in self.sessions:
            if session.check_admin_joined(update):
                update.message.reply_text(
                    text="You are already in session {}. Use /leave to leave your current session.".format(session.ID))

        try:
            match, ID, idx = self.check_session_existing(context.args[0])

            if match:
                if self.sessions[idx].add_admin(update):
                    update.message.reply_text(
                        text="You have joined session {}.".format(ID))

                else:
                    update.message.reply_text(
                        text="You have already joined session {}.".format(ID))

            else:
                update.message.reply_text(
                    text="Session ID {} cannot be found. Use /zastart <ID> <rounds> <questions> to create a new session.".format(ID))

        except ValueError:
            update.message.reply_text(
                text="ID should be an integer. Use /zastart <ID> <rounds> <questions> to create a new session, or /zajoin <ID> to join a session.")

        except IndexError:
            update.message.reply_text(
                text="ID not given. Use /zastart <ID> <rounds> <questions> to create a new session, or /zajoin <ID> to join a session.")

    joinSession = restricted(join_session)

    def get_session_joiner(self):
        self.joiner_handler = CommandHandler('zajoin', self.joinSession)

    ''' round management conversation callbacks and handlers '''

    def manage_session(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        manage_text = " You are now managing session {}.\n It is currently at round {}, question {}.".format(
            session.ID, session.current_round, session.current_qn)
        markup = ReplyKeyboardMarkup([['Proceed']], one_time_keyboard=True)

        update.message.reply_text(text=manage_text, reply_markup=markup)

        return self.SELECTING_ACTION

    # main action selection callback, which gives a keyboard for session
    # management depending on its current state
    def select_action(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        keyboard = []
        if session.state == session.IDLE:
            # if not at the end of a round, freely navigate
            if session.current_qn <= session.questions:
                keyboard.append(['Open Q', 'Open review'])
                second_row = []
                if session.current_qn > 1:
                    second_row.append("Prev. Q")
                second_row.append("Next Q")
                keyboard.append(second_row)
        elif session.state == session.OPEN:
            keyboard.append(["Close Q"])
        elif session.state == session.REVIEW:
            keyboard.append(["Close review"])

        keyboard.append(["Transfer"])

        markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        manage_text = "You are currently in session {} at round {}, question {}.".format(
            session.ID, session.current_round, session.current_qn)

        update.message.reply_text(text=manage_text, reply_markup=markup)
        return self.ACTION

    # next, previous question / round callbacks
    def inc_qn(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        if session.current_qn < session.questions:
            session.current_qn += 1
            markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
            update.message.reply_text("Go to Q{}.".format(
                session.current_qn), reply_markup=markup)

            return self.SELECTING_ACTION
        else:
            keyboard = [["Next round"], ["Open review"]]
            markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            update.message.reply_text("You are at the last question of round {}. Go to next round?".format(
                session.current_round), reply_markup=markup)

            return self.ACTION

    def dec_qn(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        if session.current_qn > 1:
            session.current_qn -= 1
            markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
            update.message.reply_text("Go back to Q{}.".format(
                session.current_qn), reply_markup=markup)

            return self.SELECTING_ACTION
        else:
            markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
            update.message.reply_text("Already at Q1 of round {}.".format(
                session.current_round), reply_markup=markup)

            return self.SELECTING_ACTION

    def inc_round(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        # generate JSON file with user : answers
        file_str, written = session.get_round_file()
        if written:
            for admin in session.admins:
                context.bot.send_document(chat_id=admin.chat_id,
                                          document=open(file_str, 'rb'))
        else:
            update.message.reply_text("Error generating answer file.")

            return self.SELECTING_ACTION

        # broadcast points for previous rounds, and increment round
        for player in session.players:
            context.bot.send_message(chat_id=player.chat_id,
                                     text="Round {} has just ended. You were at {} points. Please wait for the admins to mark your answers.".format(session.current_round, player.score))

        if session.current_round < session.rounds:
            session.current_round += 1
            session.current_qn = 1
            markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
            update.message.reply_text("Entering round {}.".format(
                session.current_round), reply_markup=markup)

            return self.SELECTING_ACTION
        else:
            markup = ReplyKeyboardMarkup(
                [["End game"]], one_time_keyboard=True)
            update.message.reply_text("You have finished the last round. Make sure you update the scores and call /zascore to check the scores before ending the game!".format(
                session.current_round), reply_markup=markup)

            return self.END_GAME

    # open and closing of answering callbacks
    def open_qn(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        # open session and broadcast opening
        session.state = Session.OPEN

        for player in session.players:
            context.bot.send_message(chat_id=player.chat_id, text="Q{} of round {} is now open. Enter your answers.".format(
                session.current_qn, session.current_round), )

        markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
        update.message.reply_text("Q{} of round {} has been opened. If there is a bonus, just add it on top of the answer to the base question.".format(
            session.current_qn, session.current_round), reply_markup=markup)

        return self.SELECTING_ACTION

    def close_qn(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        # open session and broadcast opening
        session.state = Session.IDLE

        for player in session.players:
            context.bot.send_message(chat_id=player.chat_id, text="Q{} of round {} is now closed. Further answers will be ignored.".format(
                session.current_qn, session.current_round))

        markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
        update.message.reply_text("Q{} of round {} has been closed.".format(
            session.current_qn, session.current_round), reply_markup=markup)

        return self.SELECTING_ACTION

    def open_review(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        # open session and broadcast opening
        session.state = Session.REVIEW
        for player in session.players:
            context.bot.send_message(chat_id=player.chat_id,
                                     text="Review of round {} is now open. Send your answers in the format <Q#> <answer> e.g. 1 cow. Use /check to look at your current answers.".format(
                                         session.current_round))

        markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
        update.message.reply_text(text="Review of round {} has been opened.".format(
            session.current_round), reply_markup=markup)

        return self.SELECTING_ACTION

    def close_review(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        # open session and broadcast opening
        session.state = Session.IDLE

        for player in session.players:
            context.bot.send_message(chat_id=player.chat_id,
                                     text="Review of round {} is now closed. Further answers will be ignored.".format(session.current_round))

        markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
        update.message.reply_text("Review of round {} has been closed.".format(
            session.current_round), reply_markup=markup)

        return self.SELECTING_ACTION

    def transfer(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        # transfer control and end conversation
        for admin in session.admins:
            if admin.chat_id != update.effective_user.id:
                session.active_admin = admin
                update.message.reply_text(
                    "Control has been transferred to {}.".format(session.active_admin.username))

                return ConversationHandler.END

        # retain control and return to main action callback
        markup = ReplyKeyboardMarkup([["Proceed"]], one_time_keyboard=True)
        update.message.reply_text(
            "You are the only active admin! You can't transfer control!", reply_markup=markup)

        return self.SELECTING_ACTION

    # ending the game
    def end_session(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        # broadcast points for previous rounds, and increment round
        for player in session.players:
            context.bot.send_message(chat_id=player.chat_id,
                                     text="The session has ended! You were at {} points! This may not be the final score, so do wait for your admins to confirm it.".format(player.score))

        for idx in range(len(self.sessions)):
            if self.sessions[idx].ID == session.ID:
                self.sessions.pop(idx)

        update.message.reply_text("Session has ended.")

        return ConversationHandler.END

    manageSession = restricted(manage_session)

    def get_management_handler(self):
        self.management_handler = ConversationHandler(
            entry_points=[CommandHandler('zamanage', self.manageSession)],

            states={
                self.SELECTING_ACTION: [
                    MessageHandler(Filters.regex(
                        '(Proceed)'), self.select_action)
                ],

                self.ACTION: [
                    MessageHandler(Filters.regex(
                        '(Next Q)'), self.inc_qn),
                    MessageHandler(Filters.regex(
                        '(Prev. Q)'), self.dec_qn),
                    MessageHandler(Filters.regex(
                        '(Next round)'), self.inc_round),
                    MessageHandler(Filters.regex(
                        '(Open Q)'), self.open_qn),
                    MessageHandler(Filters.regex(
                        '(Close Q)'), self.close_qn),
                    MessageHandler(Filters.regex(
                        '(Open review)'), self.open_review),
                    MessageHandler(Filters.regex(
                        '(Close review)'), self. close_review),
                    MessageHandler(Filters.regex(
                        '(Transfer)'), self.transfer)
                ],

                self.END_GAME: [MessageHandler(
                    Filters.regex('(End game)'), self.end_session),
                ]

            },

            fallbacks=[]
        )

    ''' leave callback '''

    def leave_sessions(self, update, handler):
        # check if user is already in a session
        for session in self.sessions:
            for idx in range(len(session.admins)):
                if session.admins[idx].chat_id == update.effective_user.id:
                    admin = session.admins[idx]

                    # remove this admin
                    session.admins.pop(idx)

                    # check if admin is also active admin
                    if session.active_admin.chat_id == admin.chat_id:
                        if len(session.admins) != 0:
                            session.active_admin = session.admins[0]
                        else:
                            session.active_admin = -1

        update.message.reply_text("You have left all sessions.")
        return ConversationHandler.END

    leaveSession = restricted(leave_sessions)

    def get_leave_handler(self):
        self.leave_handler = CommandHandler('zaleave', self.leaveSession)

    ''' score check callback '''
    def check_score(self, update, handler):
        # check if user is already in a session
        for session in self.sessions:
            for idx in range(len(session.admins)):
                if session.admins[idx].chat_id == update.effective_user.id:
                    score_str = 'Scores for session {}:\n'.format(session.ID)

                    for player in session.players:
                        score_str += "{}: {}\n".format(player.username, player.score)

                    update.message.reply_text(score_str)

    checkScore = restricted(check_score)

    def get_checkscore_handler(self):
        self.checkscore_handler = CommandHandler('zascore', self.checkScore)

    ''' help callback '''

    def get_help(self, update, handler):
        update.message.reply_text(
            "Help for admin commands.\n"
            "* commands * \n"
            "/zastart <ID> <rounds> <questions> - starts a session \n"
            "/zajoin <ID> - joins a session \n"
            "/zamanage - manage a session you are currently an active admin in \n"
            "/zaleave - leave all sessions \n"
            "/zascore - check scores for all sessions you are in.\n"
            "\n"
            "* managing sessions *\n"
            "Use the buttons to navigate between questions and rounds \n"
            "Use 'Transfer' to pass control to another admin\n"
            "Drag and drop score files to update scores\n"
        )

    getHelp = restricted(get_help)

    def get_help_handler(self):
        self.help_handler = CommandHandler('zahelp', self.getHelp)

    ''' file to score update callback '''

    def update_scores(self, update, context):
        # check if user is already in a session
        found, session = self.get_active_session(update, False)

        if not found:
            update.message.reply_text(
                "You are currently not an active admin of any session. Please create a session with /zastart, or wait for control to be transferred.")
            return ConversationHandler.END

        score_file = update.message.document.get_file()
        try:
            score_filename = score_file.download()

            with open(score_filename, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    entries = line.split('\t')
                    player_name = entries[0]
                    player_found, player = session.check_player_joined(
                        update, player_name)
                    if player_found:
                        player.score += int(entries[-1])

            update.message.reply_text("Document parsed, scores updated.")

        except Exception as inst:
            print(inst)
            update.message.reply_text("Error parsing document.")

    updateScores = restricted(update_scores)

    def get_score_handler(self):
        self.score_handler = MessageHandler(
            Filters.document, self.updateScores)

    def add_handlers(self, dp):
        dp.add_handler(self.help_handler)
        dp.add_handler(self.leave_handler)
        dp.add_handler(self.session_handler)
        dp.add_handler(self.joiner_handler)
        dp.add_handler(self.checkscore_handler)
        dp.add_handler(self.score_handler)
        dp.add_handler(self.management_handler)
