import nextcord
from nextcord import Interaction, app_commands
from nextcord.ext import commands
import aiohttp
import os
import logging
import logging.handlers
from dotenv import load_dotenv

from cogs.ticket.ticket import ticket_launcher, main
from cogs.settings.suggestions import suggVotes
from cogs.misc.giveaway import giveawayButton
from cogs.misc.poll import pollButtons

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.members = True
        intents.message_content = True

        # Fix: command_prefix should be a string (put '!' in quotes)
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=int(os.getenv("APP_ID"))
        )

        # Collect all cogs dynamically
        cogs = []
        for root, dirs, files in os.walk("cogs"):
            if "__pycache__" in root:
                continue
            folder_name = os.path.basename(root)
            for file_name in files:
                if file_name.endswith(".py"):
                    if folder_name == "cogs":
                        cogs.append(f"cogs.{file_name[:-3]}")
                    else:
                        cogs.append(f"cogs.{folder_name}.{file_name[:-3]}")
        self.initial_extensions = cogs
        self.added = False

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        for cog in self.initial_extensions:
            await self.load_extension(cog)
        await self.tree.sync()
        print("Synced Successfully")

    async def close(self):
        await super().close()
        await self.session.close()

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        if not self.added:
            self.add_view(ticket_launcher())
            self.add_view(main())
            self.add_view(suggVotes())
            self.add_view(pollButtons())
            self.add_view(giveawayButton())
            self.added = True
            await self.change_presence(activity=nextcord.Game(name="/help start"))
        if not os.path.exists("db"):
            os.makedirs("db")

    async def on_message(self, message: nextcord.Message):
        # You can process messages here if needed
        pass

bot = MyBot()
bot.remove_command("help")

# Set up logging
logger = logging.getLogger("nextcord")
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename="discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
handler.setFormatter(formatter)
logger.addHandler(handler)

# App command error handling
@bot.tree.error
async def on_app_command_error(interaction: Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        embed = nextcord.Embed(
            title="Slow it down bro!",
            description=f"Try again in {error.retry_after:.2f}s.",
            colour=nextcord.Colour.light_grey(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif isinstance(error, app_commands.MissingPermissions):
        missing_perm = error.missing_permissions[0].replace("_", " ").title()
        embed = nextcord.Embed(
            title="You're Missing Permissions!",
            description=f"You don't have {missing_perm} permission.",
            colour=nextcord.Colour.light_grey(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif isinstance(error, app_commands.BotMissingPermissions):
        missing_perm = error.missing_permissions[0].replace("_", " ").title()
        embed = nextcord.Embed(
            title="I'm Missing Permissions!",
            description=f"I don't have {missing_perm} permission.",
            colour=nextcord.Colour.light_grey(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    else:
        error_channel = bot.get_channel(int(os.getenv("ERROR_CHANNEL_ID")))
        if error_channel:
            await error_channel.send(f"Error: {str(error)}")
        await interaction.response.send_message(
            "Sorry, an error occurred.\nIf you are facing any issues, you can send your </feedback:1027218853127794780>.",
            ephemeral=True,
        )
        raise error

bot.run(os.getenv("BOT_TOKEN"))
