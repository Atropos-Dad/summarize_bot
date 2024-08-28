Summarizer Bot

## Description
This is a tiny lil python discord bot for various LLM based functions inside a discord server. The titular feature summarizes the previous n messages in a channel and tries to summarize the most recently scheduled plans in a channel. It means if your friends have been figuring out times for plans, but the meeting time and place has changed a few times you can use this bot to summarize the plan for you.

There is very little error handling (or protections!) and the bot is not very robust, this is a proof of concept for private discord servers with friends! Uses gemini at the moment, but can be easily swapped out for any other LLM model (or moved to something like litellm). 

## Features
- Plan summarization: The bot can summarize the most recent plans discussed in a channel, making it easier for users to keep track of the details.
- Coding: Can generate small code snippets for you and format with markdown for Discord.
- Supreme Court: Can generate a simulated Supreme Court decision for any question/topic
- Story: can tell you a story based on topic
- Ask: Raw LLM model for any question

## Installation
1. Clone the repository: `https://github.com/Atropos-Dad/summarize_bot.git`
2. Navigate to the project directory: `cd summarize_bot`
3. Install the required dependencies: `pip install -r requirements.txt`

## Usage
1. Fill in the API keys in a .env
2. Run the bot: `python bot.py`
3. ???
4. Summarize :)


## License
This project is licensed under the [MIT License](LICENSE).
