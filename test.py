#! /usr/bin/env python3

from InquirerPy import inquirer

fav_lang = inquirer.select(
    message = "What's your favorite language:",
    choices = ["Go", "Kotlin", "Python", "Rust", "Java", "JavaScript"]
).execute()