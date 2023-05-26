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
from imaginepy import AsyncImagine, Style, Ratio

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

# Load api key
try:
    with open("api_key.txt") as f:
        api_key = f.read()
except FileNotFoundError:
    api_key = "0000000000"
    print("No api key selected. Using anonymous account!")

# Imaginepy function
async def generate_image(image_prompt, style_value, ratio_value):
    imagine = AsyncImagine()
    filename = str(uuid.uuid4()) + ".png"
    style_enum = Style[style_value]
    ratio_enum = Ratio[ratio_value]
    img_data = await imagine.sdprem(
        prompt=image_prompt,
        style=style_enum,
        ratio=ratio_enum
    )
    if img_data is None:
        print("An error occurred while generating the image.")
        return

    try:
        with open(filename, mode="wb") as img_file:
            img_file.write(img_data)
    except Exception as e:
        print(f"An error occurred while writing the image to file: {e}")
        return None
    
    await imagine.close()

    return filename


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

    
@bot.hybrid_command(name="imagine", description="Generate image")
@app_commands.choices(style=[
    app_commands.Choice(name='Imagine V4 Beta', value='IMAGINE_V4_Beta'),
    app_commands.Choice(name='Realistic', value='REALISTIC'),
    app_commands.Choice(name='Anime', value='ANIME_V2'),
    app_commands.Choice(name='Disney', value='DISNEY'),
    app_commands.Choice(name='Studio Ghibli', value='STUDIO_GHIBLI'),
    app_commands.Choice(name='Graffiti', value='GRAFFITI'),
    app_commands.Choice(name='Medieval', value='MEDIEVAL'),
    app_commands.Choice(name='Fantasy', value='FANTASY'),
    app_commands.Choice(name='Neon', value='NEON'),
    app_commands.Choice(name='Cyberpunk', value='CYBERPUNK'),
    app_commands.Choice(name='Landscape', value='LANDSCAPE'),
    app_commands.Choice(name='Japanese Art', value='JAPANESE_ART'),
    app_commands.Choice(name='Steampunk', value='STEAMPUNK'),
    app_commands.Choice(name='Sketch', value='SKETCH'),
    app_commands.Choice(name='Comic Book', value='COMIC_BOOK'),
    app_commands.Choice(name='Imagine V4 creative', value='V4_CREATIVE'),
    app_commands.Choice(name='Imagine V3', value='IMAGINE_V3'),
    app_commands.Choice(name='Cosmic', value='COMIC_V2'),
    app_commands.Choice(name='Logo', value='LOGO'),
    app_commands.Choice(name='Pixel art', value='PIXEL_ART'),
    app_commands.Choice(name='Interior', value='INTERIOR'),
    app_commands.Choice(name='Mystical', value='MYSTICAL'),
    app_commands.Choice(name='Super realism', value='SURREALISM'),
    app_commands.Choice(name='Minecraft', value='MINECRAFT'),
    app_commands.Choice(name='Dystopian', value='DYSTOPIAN')
])
@app_commands.choices(ratio=[
    app_commands.Choice(name='1x1', value='RATIO_1X1'),
    app_commands.Choice(name='9x16', value='RATIO_9X16'),
    app_commands.Choice(name='16x9', value='RATIO_16X9'),
    app_commands.Choice(name='4x3', value='RATIO_4X3'),
    app_commands.Choice(name='3x2', value='RATIO_3X2')
])
async def imagine(ctx, prompt: str, style: app_commands.Choice[str], ratio: app_commands.Choice[str]):
    temp_message = await ctx.send("https://cdn.discordapp.com/emojis/1075796965515853955.gif?size=96&quality=lossless")
    filename = await generate_image(prompt, style.value, ratio.value)
    await ctx.send(content=f"Here is the generated image for {ctx.author.mention} \n- Prompt : `{prompt}`\n- Style :`{style.name}`", file=discord.File(filename))
    os.remove(filename)
    await temp_message.edit(content=f"Finished Image Generation")

try:
    with open("bot_token.txt") as f:
        bot_token = f.read()
except FileNotFoundError:
    print("BOT TOKEN NOT FOUND! PUT YOUR BOT TOKEN IN `bot_token.txt`")
bot.run(bot_token)