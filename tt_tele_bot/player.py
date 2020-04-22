# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 18:09:54 2020

@author: looshua
"""

import telegram
import logging

from telegram.ext import (Updater, CommandHandler,
                          MessageHandler, ConversationHandler,
                          CallbackQueryHandler, Filters)
from telegram import ReplyKeyboardMarkup


class PlayerUser:
    def __init__(self, update):
        try:
            self.username = update.effective_user.username
            print(update.effective_user)
        except:
            self.username = update.effective_user.first_name

        self.chat_id = update.effective_user.id

        self.score = 0
        self.answers = {}
        self.review_qn = -1

    def get_round_answers(self, n_questions, c_round):
        ret_line = str(self.username) + "\t"
        if str(c_round) in self.answers.keys():
            round_dict = self.answers[str(c_round)]
            for num in range(1, n_questions + 1):
                if str(num) in round_dict.keys():
                    ans = round_dict[str(num)]
                    ret_line += "{} \t".format(ans)
                else:
                    ret_line += "\t"
        ret_line += "\n"

        return ret_line


class PlayerBot:
    PLAY, REVIEW = range(2)

    def __init__(self, main_bot):
        self.main_bot = main_bot

        self.get_player_conv_handler()
        self.get_check_handler()
        self.get_help_handler()
        self.get_leave_handler()

    def get_active_session(self, update):
        player_found = False
        session = -1
        player = -1

        for psession in self.main_bot.sessions:
            for pplayer in psession.players:
                if pplayer.chat_id == update.effective_user.id:
                    session = psession
                    player = pplayer
                    player_found = True
                    break
            if player_found:
                break

        return player_found, session, player

    ''' play session callbacks '''

    def join_session(self, update, context):
        # check if the player is already active
        player_active, session, player = self.get_active_session(update)
        if player_active:
            update.message.reply_text(
                "You have already joined session {}! Use /leave to leave the session".format(session.ID))
            return ConversationHandler.END

        # check if session exists
        try:
            found, ID, idx = self.main_bot.check_session_existing(
                context.args[0])

            if found:
                self.main_bot.sessions[idx].add_player(update)
                update.message.reply_text(
                    "You have joined session {}.".format(ID))

                return self.PLAY

            else:
                self.main_bot.sessions[idx].add_player(update)
                update.message.reply_text(
                    "Session {} has not been created. Please wait for admins to create the session.".format(ID))\

                return ConversationHandler.END

        except (ValueError, IndexError):
            update.message.reply_text(
                text="You have entered an invalid session ID. Use /join <ID> to join a session.")

            return ConversationHandler.END

    def answer_qn(self, update, context):
        # check if the player is already active
        player_active, session, player = self.get_active_session(update)
        if not player_active:
            update.message.reply_text(
                "You are not currently in a session!")
            return ConversationHandler.END

        # if session is currently idle, map back to itself to await a state change
        if session.state == session.IDLE:
            return self.PLAY

        if session.state == session.REVIEW:
            ans_ls = update.message.text.split(' ')

            try:
                q_num = int(ans_ls[0])
                if q_num < 1 or q_num > session.questions:
                    raise ValueError

                if q_num > session.current_qn:
                    update.message.reply_text(
                        text="Please only review answers for questions we've gone through.")

                    return self.PLAY

                nanswer = ""
                for word in ans_ls[1:]:
                    nanswer += (word + " ")

                round_dict = player.answers[str(session.current_round)]
                round_dict[str(q_num)] = nanswer

                update.message.reply_text(
                    text="Answer recorded. Use /check to check your answers for the round.")

                return self.PLAY

            except (ValueError, IndexError):
                update.message.reply_text(
                    "Could not parse your answer. Please answer the review question in the format <Q#> <answer> e.g. 1 cow.")

                return self.PLAY

        # in an open state, accept the next text that comes in as a answer
        elif session.state == session.OPEN:
            nanswer = update.message.text
            if str(session.current_round) not in player.answers:
                player.answers[str(session.current_round)] = {}

            round_dict = player.answers[str(session.current_round)]
            round_dict[str(session.current_qn)] = nanswer

            update.message.reply_text(
                text="Answer recorded. Use /check to check your answers for the round.")

            return self.PLAY

    ''' leave callback '''

    def leave_session(self, update, context):
        player_found, session, player = self.get_active_session(update)
        if not player_found:
            update.message.reply_text(
                "You are not currently in a session!")
            return ConversationHandler.END

        for idx in range(len(session.players)):
            if session.players[idx].chat_id == player.chat_id:
                session.players.pop(idx)
                break

        update.message.reply_text("You have left the session.")
        return ConversationHandler.END

    ''' checker callbacks '''

    def check_answers(self, update, context):
        # check if the player is already active
        player_active, session, player = self.get_active_session(update)
        if not player_active:
            update.message.reply_text(
                "You are not currently in a session!")
            return ConversationHandler.END

        try:
            ans_dict = player.answers[str(session.current_round)]
        except KeyError:
            update.message.reply_text(
                text="You have not entered any answers for this round yet.")
            return self.PLAY

        reply = "Your answers for round {} are: \n".format(
            session.current_round)

        sorted_qns = sorted([int(qn) for qn in ans_dict.keys()])
        for qn in sorted_qns:
            line = "{}. {} \n".format(qn, ans_dict[str(qn)])
            reply += line

        update.message.reply_text(text=reply)

    def get_check_handler(self):
        self.check_handler = CommandHandler('check', self.check_answers)

    def check_score(self, update, context):
        # check if the player is already active
        player_active, session, player = self.get_active_session(update)
        if not player_active:
            update.message.reply_text(
                "You are not currently in a session!")
            return ConversationHandler.END

        update.message.reply_text(
            "Your current score is {}.".format(player.score))

    def get_score_handler(self):
        self.score_handler = CommandHandler('score', self.check_score)

    def get_player_conv_handler(self):
        self.conv_handler = ConversationHandler(
            entry_points=[CommandHandler('join', self.join_session)],

            states={
                self.PLAY: [
                    CommandHandler('score', self.check_score),

                    CommandHandler('check', self.check_answers),

                    CommandHandler('leave', self.leave_session),

                    MessageHandler(
                        (Filters.text & (~Filters.command)), self.answer_qn)
                ]
            },

            fallbacks=[]

        )

    ''' help callback '''

    def get_help(self, update, context):
        update.message.reply_text(
            "* commands *\n"
            "/join <ID> - joins a session\n"
            "/leave - leave all sessions\n"
            "\n"
            "* answering questions *\n"
            "Wait for admins to open answering sessions, then simply key in your answers.\n"
            "For reviews, make sure your answer is preceded by the "
            "question number you want to review, e.g. 1 big bad wolf\n"
        )

    def get_help_handler(self):
        self.help_handler = CommandHandler('help', self.get_help)

    def get_leave_handler(self):
        self.leave_handler = CommandHandler('leave', self.leave_session)

    def add_handlers(self, dp):
        dp.add_handler(self.help_handler)
        dp.add_handler(self.conv_handler)
