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

llm_setup = {
    "model": os.getenv('LLM_MODEL', 'ollama/llama3.1:latest'),
    "api_base": os.getenv('LLM_API_BASE', 'http://localhost:11434'),
}

# local_llm_setup = {
#     "model": "gemini/gemini-pro",
#     "safety_settings": global_safety_settings
# }

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

async def process_llm_response(response, ctx, prompt_info):
    # Extract response content
    result = response.choices[0].message.content

    # Calculate the cost
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens

    if 'response_cost' in response._hidden_params and response._hidden_params['response_cost'] is not None:
        cost = response._hidden_params['response_cost']
        cost_string = f"Cost of request: ${cost:.4f} "
    else:
        cost = 0
        cost_string = "This was run __locally__, and **no money** was sent to google :) "

    result_string = "-# " + cost_string + f" (Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens})"

    # Log the result and cost information
    logging.info(f"{prompt_info} generated: {result}")
    logging.info(result_string)

    # Send the result and cost information back to the Discord channel
    await send_chunked_message(ctx, f"Here's {prompt_info}:\n\n{result}")
    await ctx.send(result_string)

async def handle_exception(e, ctx, action):
    error_message = f"An error occurred while {action}: {str(e)}"
    logging.error(error_message)
    await ctx.send(error_message)

@bot.command(name='summarize')
async def summarize(ctx):
    await ctx.send("Collecting and summarizing messages...")
    
    # Collect messages
    messages = []
    async for message in ctx.channel.history(limit=200):
        message_content = f"{message.author.name}: {message.content}"
        messages.append(message_content)
        logging.debug(f"Message read: {message_content}")
    
    messages.reverse()
    message_text = "\n".join(messages)
    logging.debug(f"Full message text sent to AI:\n{message_text}")
    
    # Prepare the prompt
    prompt = dedent(f"""Summarize the following conversation and provide clear instructions on current plans, including what's happening, where, and when where applicable.
    The conversation may be in regards to a digital gathering (such as to play a video game) or it may be a physical gathering (going for food).
    You may consider highlighting different elements of the gathering differently based on context (e.g., which game is being played, who's playing).
    You may receive messages unrelated to the gathering, please ignore these.
    As the conversations continue, plans may change, please ensure the summary is as up-to-date as possible, mentioning when elements are still to be decided or are unclear.
    Here's the conversation:
    {message_text}
    Summary and instructions:""")
    
    try:
        # Use LiteLLM to generate the summary
        response = completion(
            model=llm_setup["model"],
            messages=[{"role": "user", "content": prompt}],
            safety_settings=global_safety_settings,
            api_base=llm_setup["api_base"]
        )
        
        # Process the response
        await process_llm_response(response, ctx, "a summary of the current plans")
        
    except Exception as e:
        await handle_exception(e, ctx, "summarizing")

@bot.command(name='codemonkeygo')
async def generate_code(ctx, *, prompt):
    await ctx.send("Generating code based on your request...")
    
    ai_prompt = dedent(f"""
    Generate code based on the following request:
    {prompt}
    
    Provide a brief explanation of the code if necessary.
    Return the code in a format that can be directly used in Discord's markdown for code blocks.
    """)
    
    try:
        response = completion(
            model=llm_setup["model"],
            messages=[{"role": "user", "content": ai_prompt}],
            safety_settings=global_safety_settings,
            api_base=llm_setup["api_base"]
        )
        
        await process_llm_response(response, ctx, "the generated code based on your request")
        
    except Exception as e:
        await handle_exception(e, ctx, "generating code")

@bot.command(name='story')
async def generate_story(ctx, *, prompt):
    await ctx.send("Generating a story based on your prompt...")
    
    ai_prompt = dedent(f"""
    Generate a short story based on the following prompt:
    {prompt}
    
    The story should have a clear beginning, middle, and end. Include vivid descriptions and engaging dialogue if appropriate.
    Feel free to be creative and expand on the prompt in unexpected ways.
    """)
    
    try:
        response = completion(
            model=llm_setup["model"],
            messages=[{"role": "user", "content": ai_prompt}],
            safety_settings=global_safety_settings,
            api_base=llm_setup["api_base"]
        )
        
        await process_llm_response(response, ctx, "a short story based on your prompt")
        
    except Exception as e:
        await handle_exception(e, ctx, "generating the story")

@bot.command(name='ask')
async def ask_question(ctx, *, question):
    await ctx.send("Thinking about your question...")
    
    prompt = dedent(f"{question}")
    
    try:
        response = completion(
            model=llm_setup["model"],
            messages=[{"role": "user", "content": prompt}],
            safety_settings=global_safety_settings,
            api_base=llm_setup["api_base"]
        )
        
        await process_llm_response(response, ctx, "the answer to your question")
        
    except Exception as e:
        await handle_exception(e, ctx, "answering the question")

@bot.command(name='supreme_court')
async def supreme_court_decision(ctx, *, question):
    await ctx.send("Generating a simulated Supreme Court decision based on your question...")
    
    prompt = dedent(f"""
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
        response = completion(
            model=llm_setup["model"],
            messages=[{"role": "user", "content": prompt}],
            safety_settings=global_safety_settings,
            api_base=llm_setup["api_base"]
        )
        
        await process_llm_response(response, ctx, "the simulated Supreme Court decision")
        
    except Exception as e:
        await handle_exception(e, ctx, "generating the Supreme Court decision")
        
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