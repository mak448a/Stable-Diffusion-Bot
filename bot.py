import discord
from discord import app_commands
from discord.ext import commands
import platform
import aiohttp
import os
import time
import httpx
import urllib.parse
import requests
import random

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

# Load api key
try:
    with open("api_key.txt") as f:
        api_key = f.read()
except FileNotFoundError:
    api_key = "0000000000"
    print("No api key selected. Using anonymous account!")


@bot.event
async def on_ready():
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="Try /imagine"))
    print(f"{bot.user.name} has connected to Discord!")
    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(administrator=True),
        scopes=("bot", "applications.commands")
    )
    print(f"Invite link: {invite_link}")


async def download_image(image_url, save_as):
    async with httpx.AsyncClient() as client:
        response = await client.get(image_url)
    with open(save_as, "wb") as f:
        f.write(response.content)    

@bot.hybrid_command(name="imagine", description="Write an amazing prompt for Stable Diffusion to generate")
async def imagine(ctx, *, prompt: str):
    sanitized = ""
    forbidden = ['"', "'", "`", "\\", "$"]

    for char in prompt:
        if char in forbidden:
            continue
        else:
            sanitized += char

    # Add ephemeral=True to make it only visible by you
    await ctx.send(f"{ctx.user.mention} is generating \"{sanitized}\"")

    # Generate image
    print(f"Generating {sanitized}")

    current_time = time.time()

    if platform.system() == "Windows":
        os.system(f"python AI-Horde-With-Cli/cli_request.py --prompt '{sanitized}'"
                  f" --api_key '{api_key}' -n 4 -f {current_time}.png")
    else:
        os.system(f"python3 AI-Horde-With-Cli/cli_request.py --prompt '{sanitized}'"
                  f" --api_key '{api_key}' -n 4 -f {current_time}.png")

    # Loop until image generates
    while True:
        if os.path.exists(f"0_{current_time}.png"):
            break
        else:
            continue

    for i in range(4):
        with open(f'{i}_{current_time}.png', 'rb') as file:
            picture = discord.File(file)
            await ctx.send(file=picture)
        os.remove(f"{i}_{current_time}.png")
        
    
@bot.hybrid_command(name="polygen", description="Generate image using pollinations")
async def polygen(ctx, *, prompt: str):
    encoded_prompt = urllib.parse.quote(prompt)
    images = []

    temp_message = await ctx.send("Generating images...")  # Send a temporary message

    # Generate four images with the given prompt
    i = 0
    while len(images) < 4:
        seed = random.randint(1, 100000)  # Generate a random seed
        image_url = f'https://image.pollinations.ai/prompt/{encoded_prompt}{seed}'
        response = requests.get(image_url)

        try:
            image_data = response.content

            # Generate a unique filename for each image
            filename = f'{ctx.author.id}_{ctx.message.id}_{i}.png'
            with open(filename, 'wb') as f:
                f.write(image_data)

            images.append(filename)
            i += 1
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            print(f"Error generating image: {e}")

    # Delete the temporary message
    await temp_message.delete()

    if images:
        # Send all image files as attachments in a single message
        image_files = [discord.File(image) for image in images]
        await ctx.send(files=image_files)

        # Delete the local image files
        for image in image_files:
            os.remove(image.filename)
    else:
        await ctx.send("Error generating images. Please try again later.")

    
@bot.hybrid_command(name="dallegen", description="Generate image using DALLE")
async def images(ctx, *, prompt):
    url = "https://imagine.mishal0legit.repl.co/image"
    json_data = {"prompt": prompt}
    
    try:
        temp_message = await ctx.send("Sending post request to end point...")
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_data) as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data.get("image_url")
                    image_name = f"{prompt}.jpeg"
                    if image_url:
                        await download_image(image_url, image_name)
                        with open(image_name, 'rb') as file:
                            await temp_message.edit(content="Finished Image Generation")
                            await ctx.reply(file=discord.File(file))
                        os.remove(image_name)
                    else:
                        await temp_message.edit(content="An error occurred during image generation.")
                else:
                    await temp_message.edit(content="An error occurred with the server request.")
    except aiohttp.ClientError as e:
        await temp_message.edit(content=f"An error occurred while sending the request: {str(e)}")
    except Exception as e:
        await temp_message.edit(content=f"An error occurred: {str(e)}")


try:
    with open("bot_token.txt") as f:
        bot_token = f.read()
except FileNotFoundError:
    print("BOT TOKEN NOT FOUND! PUT YOUR BOT TOKEN IN `bot_token.txt`")
bot.run(bot_token)
