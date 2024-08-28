import discord
from discord.ext import commands
import asyncio
from litellm import completion
import logging
from textwrap import dedent
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create a logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Set up file logging
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
file_handler = logging.FileHandler(f'logs/messages_{current_time}.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Get the root logger and add the file handler
root_logger = logging.getLogger()
root_logger.addHandler(file_handler)

# Replace with your Discord bot token
TOKEN = os.getenv('DISCORD_API_KEY')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
global_safety_settings=[
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ]


async def send_chunked_message(ctx, message):
    chunks = []
    current_chunk = ""
    
    for line in message.split('\n'):
        if len(current_chunk) + len(line) + 1 > 1900:  # +1 for newline
            chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    for chunk in chunks:
        await ctx.send(chunk)

@bot.event
async def on_ready():
    logging.info(f'{bot.user} has connected to Discord!')

@bot.command(name='summarize')
async def summarize(ctx):
    await ctx.send("Collecting and summarizing messages...")
    
    # Collect the last 200 messages
    messages = []
    async for message in ctx.channel.history(limit=200):
        message_content = f"{message.author.name}: {message.content}"
        messages.append(message_content)
        # Log each message to the file
        logging.debug(f"Message read: {message_content}")
    
    # Reverse the order to have the oldest message first
    messages.reverse()
    
    # Join the messages into a single string
    message_text = "\n".join(messages)
    
    # Log the entire message text
    logging.debug(f"Full message text sent to AI:\n{message_text}")
    
    # Prepare the prompt for the LLM
    prompt = dedent(f"""Summarize the following conversation and provide clear instructions on current plans, including what's happening, where, and when where applicable.
    The conversation may be in-regards to a digital gathering (such as to play a video game) or it may be a physical gathering (going for food).
    You may consider highlighting different elements of the gathering differently based on context (e.g. which game is being played, who's playing)
    You may receive messages unrelated to the gathering, please ignore these.
    As the conversations continues, plans may change, please ensure the summary is as up-to-date as possible, mentioning when elements are still to be decided or are unclear.
    Here's the conversation:
    {message_text}
    Summary and instructions:""")

    try:
        # Use LiteLLM to generate the summary
        response = completion(
            model="gemini/gemini-pro",
            messages=[{"role": "user", "content": prompt}],
            safety_settings=global_safety_settings
        )
        
        summary = response.choices[0].message.content
        
        # Calculate the cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        # Log the summary and cost information
        logging.info(f"Summary generated: {summary}")
        logging.info(f"Cost of request: ${response._hidden_params['response_cost']:.4f} "
                     f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
        
        # Send the summary and cost information back to the Discord channel
        await send_chunked_message(ctx, f"Here's a summary of the current plans:\n\n{summary}")
        await ctx.send(f"Cost of this request: ${response._hidden_params['response_cost']:.4f} "
                       f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
    
    
    except Exception as e:
        error_message = f"An error occurred while summarizing: {str(e)}"
        logging.error(error_message)
        await ctx.send(error_message)


@bot.command(name='codemonkeygo')
async def generate_code(ctx, *, prompt):
    await ctx.send("Generating code based on your request...")
    
    # Prepare the prompt for the LLM
    ai_prompt = dedent(f"""
    Generate code based on the following request:
    {prompt}
    
    Provide a brief explanation of the code if necessary.
    Return the code in a format that can be directly used in Discord's markdown for code blocks.
    """)

    try:
        # Use LiteLLM to generate the code
        response = completion(
            model="gemini/gemini-pro",
            messages=[{"role": "user", "content": ai_prompt}],
            safety_settings=global_safety_settings
        )
        
        code_response = response.choices[0].message.content
        
        # Calculate the cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        # Log the code and cost information
        logging.info(f"Code generated for prompt: {prompt}")
        logging.info(f"Generated response: {code_response}")
        logging.info(f"Cost of request: ${response._hidden_params['response_cost']:.4f} "
                     f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
        
        # Send the code and cost information back to the Discord channel
        await send_chunked_message(ctx, f"Here's the generated code based on your request:\n\n{code_response}")
        await ctx.send(f"Cost of this request: ${response._hidden_params['response_cost']:.4f} "
                       f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
    
    except Exception as e:
        error_message = f"An error occurred while generating code: {str(e)}"
        logging.error(error_message)
        await ctx.send(error_message)    


@bot.command(name='story')
async def generate_story(ctx, *, prompt):
    await ctx.send("Generating a story based on your prompt...")
    
    # Prepare the prompt for the LLM
    ai_prompt = dedent(f"""
    Generate a short story based on the following prompt:
    {prompt}
    
    The story should have a clear beginning, middle, and end. Include vivid descriptions and engaging dialogue if appropriate.
    Feel free to be creative and expand on the prompt in unexpected ways.
    """)

    try:
        # Use LiteLLM to generate the story
        response = completion(
            model="gemini/gemini-pro",
            messages=[{"role": "user", "content": ai_prompt}],
            safety_settings=global_safety_settings
        )
        
        story = response.choices[0].message.content
        
        # Calculate the cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        # Log the story and cost information
        logging.info(f"Story generated for prompt: {prompt}")
        logging.info(f"Generated story: {story}")
        logging.info(f"Cost of request: ${response._hidden_params['response_cost']:.4f} "
                     f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
        
        # Send the story and cost information back to the Discord channel
        await send_chunked_message(ctx, f"Here's a short story based on your prompt:\n\n{story}")
        await ctx.send(f"Cost of this request: ${response._hidden_params['response_cost']:.4f} "
                       f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
    
    except Exception as e:
        error_message = f"An error occurred while generating the story: {str(e)}"
        logging.error(error_message)
        await ctx.send(error_message)

@bot.command(name='ask')
async def ask_question(ctx, *, question):
    await ctx.send("Thinking about your question...")
    
    # Prepare the prompt for the LLM
    ai_prompt = dedent(f"""
    {question}
    """)

    try:
        # Use LiteLLM to generate the answer
        response = completion(
            model="gemini/gemini-pro",
            messages=[{"role": "user", "content": ai_prompt}],
            safety_settings=global_safety_settings
        )
        
        answer = response.choices[0].message.content
        
        # Calculate the cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        # Log the question and answer
        logging.info(f"Question asked: {question}")
        logging.info(f"Generated answer: {answer}")
        logging.info(f"Cost of request: ${response._hidden_params['response_cost']:.4f} "
                     f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
        
        # Send the answer and cost information back to the Discord channel
        await send_chunked_message(ctx,f"Here's the answer to your question:\n\n{answer}")
        await ctx.send(f"Cost of this request: ${response._hidden_params['response_cost']:.4f} "
                       f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
    
    except Exception as e:
        error_message = f"An error occurred while answering the question: {str(e)}"
        logging.error(error_message)
        await ctx.send(error_message)

@bot.command(name='supreme_court')
async def supreme_court_decision(ctx, *, question):
    await ctx.send("Generating a simulated Supreme Court decision based on your question...")
    
    # Prepare the prompt for the LLM
    ai_prompt = dedent(f"""
    Generate a simulated Supreme Court decision for the following legal question:
    {question}

    Your response should include:
    1. A brief introduction to the case and the legal question at hand.
    2. Arguments from both sides (petitioner and respondent), presenting at least two major points for each.
    3. The Court's decision, including:
       - The majority opinion (5-4 split)
       - A concurring opinion
       - A dissenting opinion
    4. The implications of this decision on future cases and society.

    Present a balanced view of the issue, demonstrating the complexity of the legal question and the nuanced perspectives of the Justices. Use legal terminology appropriately but ensure the language is accessible to a general audience.

    Format the decision as follows:
    [Case Name] (Simulated Case)

    Question Presented:
    [Restate the legal question]

    Background:
    [Brief introduction to the case]

    Arguments:
    Petitioner:
    [Present arguments]

    Respondent:
    [Present arguments]

    Decision:
    [State the Court's decision]

    Majority Opinion (delivered by Justice [Name]):
    [Present majority opinion]

    Concurring Opinion (Justice [Name]):
    [Present concurring opinion]

    Dissenting Opinion (Justice [Name]):
    [Present dissenting opinion]

    Implications:
    [Discuss potential implications]
    """)

    try:
        # Use LiteLLM to generate the decision
        response = completion(
            model="gemini/gemini-pro",
            messages=[{"role": "user", "content": ai_prompt}],
            safety_settings=global_safety_settings
        )
        
        decision = response.choices[0].message.content
        
        # Calculate the cost
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        # Log the question and decision
        logging.info(f"Supreme Court question: {question}")
        logging.info(f"Generated decision: {decision}")
        logging.info(f"Cost of request: ${response._hidden_params['response_cost']:.4f} "
                     f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
        
        # Send the decision and cost information back to the Discord channel
        await send_chunked_message(ctx, f"Here's a simulated Supreme Court decision based on your question:\n\n{decision}")
        await ctx.send(f"Cost of this request: ${response._hidden_params['response_cost']:.4f} "
                       f"(Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})")
    
    except Exception as e:
        error_message = f"An error occurred while generating the Supreme Court decision: {str(e)}"
        logging.error(error_message)
        await ctx.send(error_message)
        
async def main():
    try:
        await bot.start(TOKEN)
    except discord.LoginFailure:
        logging.error("Failed to log in. Please check your token.")
    except discord.HTTPException as e:
        logging.error(f"HTTP Exception: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())