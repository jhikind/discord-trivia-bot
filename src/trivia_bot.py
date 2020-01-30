import discord
import json
import requests
import os
import time

from random import randrange
from dotenv import load_dotenv
from textwrap import dedent
from string import ascii_uppercase
from collections import defaultdict
from difflib import SequenceMatcher

import config


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER = os.getenv("DISCORD_SERVER")
output_folder = "server-points"
if not os.path.exists(output_folder):
    os.mkdir(output_folder)
client = discord.Client()


class TriviaClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.points = None
        self.trivia_json = None
        self.category_choice = None
        self.question_content = None
        self.difficulty = Nonecd s
        self.correct_answer = None
        self.incorrect_answers = None
        self.answer_set = None
        self.answer_dict = None
        self.members = None
        self.num_questions = None

    def check_answer(self, answer):
        result = False
        if answer.lower() == self.correct_answer.lower():
            result = True
        elif SequenceMatcher(None, answer, self.correct_answer).ratio() > 0.75:
            result = True
        elif answer.lower() in self.answer_dict.keys() and self.answer_dict[answer.lower()].lower() == self.correct_answer.lower():
            result = True
        return result

    def display_answers(self):
        answer_str = """"""
        self.answer_dict = defaultdict(lambda: str)

        for c in ascii_uppercase:
            if len(self.answer_set) > 0:
                element = self.answer_set.pop()
                self.answer_dict[c.lower()] = element
                answer_str = answer_str + c + ". " + element + "\n"
        return dedent(answer_str)

    def write_points(self, guild_name):
        folder_name = guild_name.replace(" ", "_")
        folder_path = os.path.join(output_folder, folder_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        filename = "points.json"
        file_path = os.path.join(folder_path, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, "w+") as f:
            json.dump(self.points, f)

    def display_points(self, guild_name):
        folder_name = guild_name.replace(" ", "_")
        folder_path = os.path.join(output_folder, folder_name)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        filename = "points.json"
        file_path = os.path.join(output_folder, folder_name, filename)
        found = False
        if os.path.exists(file_path):
            found = True
        if found:
            with open(file_path, "r+") as f:
                self.points = json.load(f)

        else:
            with open(file_path, "w+") as f:
                self.points = dict((member, 0) for member in self.members)
                json.dump(self.points, f)

        points_str = """Points Leaderboard\n\n"""
        for member, points in sorted(
            self.points.items(), key=lambda x: x[1], reverse=True
        ):
            points_str = points_str + member + " : " + str(points) + "\n"
        return points_str

    @staticmethod
    def clean_category(category):
        return category.split(":")[1].strip(" ") if ":" in category else category

    def get_categories(self):
        categories = set()
        for question in self.trivia_json["results"]:
            categories.add(self.clean_category(question["category"]))

        return categories

    def clean_string(self, question):
        question = (
            question.replace("&#039;", "'")
            .replace("&quot;", "'")
            .replace("&eacute;", "e")
            .replace("&ouml;", "o")
            .replace("&amp;","&")
        )
        return question

    def get_question(self, category_choice):
        count = 0
        random_mode = False
        if category_choice.lower() in ["r", "ran", "rand", "random"]:
            randint = randrange(len(self.trivia_json["results"]))
            random_mode = True
        for question in self.trivia_json["results"]:
            if random_mode and count == randint:
                return question
            if category_choice.lower() == self.clean_category(
                question["category"].lower()
            ):
                return question
            if (
                category_choice.lower()
                == self.clean_category(question["category"].lower())[:3]
            ):
                return question

            count += 1
        return None

    def calc_points(self):
        if self.difficulty.lower() == "hard":
            return 2
        elif self.difficulty.lower() == "medium":
            return 1.5
        else:
            return 1

    async def on_message(self, message):
        if not self.members:
            self.members = [member.name for member in message.guild.members]
            self.members.remove("trivia-bot")

        if message.author == client.user:
            return

        if message.content.startswith("!points") or message.content.startswith("!p"):
            await message.channel.send(self.display_points(message.guild.name))

        if (
            message.content.startswith("!answer")
            or message.content.startswith("!ans")
            or message.content.startswith("!a")
        ):
            author = message.author.name
            if self.trivia_json and self.category_choice:

                answer = message.content[message.content.index(" ") + 1 :]
                if self.check_answer(answer):
                    correct = True
                    await message.channel.send("Correct!")
                else:
                    correct = False
                    await message.channel.send(
                        "Sorry, that's not right. The correct answer is {}".format(
                            self.correct_answer
                        )
                    )

                if not self.points:
                    self.display_points(message.guild.name)
                points = self.calc_points()
                if correct:
                    self.points[author] += points
                else:
                    self.points[author] -= points
                self.write_points(message.guild.name)

                await message.channel.send(
                    """
                    Type '!points' to show the leaderboard!
                    """
                )

                self.trivia_json = None
                self.num_questions = None
                self.category_choice = None

            else:
                await message.channel.send(
                    """
                    Type the '!trivia' command first and choose a category!
                    """
                )

        if (
            message.content.startswith("!category")
            or message.content.startswith("!cat")
            or message.content.startswith("!c")
        ):
            if self.trivia_json:
                if not self.category_choice:
                    cat_temp = message.content[message.content.index(" ") + 1 :]

                    question = self.get_question(cat_temp)
                    if question:
                        self.category_choice = cat_temp
                        self.question_content = self.clean_string(question["question"])
                        self.difficulty = question["difficulty"]
                        self.correct_answer = self.clean_string(
                            question["correct_answer"]
                        )
                        self.incorrect_answers = [
                            self.clean_string(question)
                            for question in question["incorrect_answers"]
                        ]

                        self.answer_set = set(
                            [self.correct_answer] + self.incorrect_answers
                        )
                        question_str = dedent('''
Question: {}

{}
Difficulty: {}


NOTE: Please format your response like: '!answer answer_choice' or '!ans answer_choice' or '!a answer_choice'
                                              '''.format(self.question_content, self.display_answers(), self.difficulty))

                        countdown = 3
                        for i in range(3):
                            await message.channel.send("{}".format(countdown - i))
                            time.sleep(1)

                        await message.channel.send(question_str)
                    else:
                        await message.channel.send(
                            "Please choose a valid category from the list!"
                        )

                else:
                    await message.channel.send(
                        """You have already chosen a category, answer the question before requesting another one!"""
                    )

            else:
                await message.channel.send("""Type the '!trivia' command first!""")

        if (
            message.content.startswith("!trivia")
            or message.content.startswith("!tri")
            or message.content.startswith("!t")
        ):
            author = message.author.name
            if not self.trivia_json:
                if len(message.content.split(" ")) > 1:
                    self.num_questions = message.content[
                        message.content.index(" ") + 1 :
                    ]
                else:
                    self.num_questions = 1
                trivia = requests.get("https://opentdb.com/api.php?amount=10")
                self.trivia_json = json.loads(trivia.text)

                categories = self.get_categories()

                choose_cat_str = dedent(
                    """
                    Hello, {}!

                    Please choose a category: {}

                    NOTE: Please format your response like: '!category category_choice' or '!cat category_choice'
                    You can either type the full category name or the first three letters (Video Games -> !cat vid)
                    """.format(
                        author, ", ".join(categories)
                    )
                )

                await message.channel.send(choose_cat_str)
            else:
                if not self.category_choice:
                    await message.channel.send(
                        "{} has already requested a trivia question! Please choose a category.".format(
                            author
                        )
                    )
                else:
                    await message.channel.send(
                        "A question has already been asked! Please answer before requesting another question."
                    )

if __name__ == "__main__":
    trivia_client = TriviaClient()
    trivia_client.run(TOKEN, reconnect=True)
