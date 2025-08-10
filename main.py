import nextcord
from nextcord import Interaction, app_commands
from nextcord.ext import commands
import aiohttp
from cogs.ticket.ticket import ticket_launcher, main
from cogs.settings.suggestions import suggVotes
from cogs.misc.giveaway import giveawayButton
from cogs.misc.poll import pollButtons
import logging
import logging.handlers
import os
from dotenv import load_dotenv

load_dotenv()

# MyBot Class
class MyBot(commands.Bot):
    def __init__(self):
        intents = nextcord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=!, intents=intents, application_id=int(os.getenv("APP_ID")))
        # Adding cogs
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
        await self.tree.sync()  # Sync app commands
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
            await bot.change_presence(activity=nextcord.Game(name="/help start"))  # Setting `Playing` status
        if not os.path.exists("db"):
            os.makedirs("db")  # Create db dir if not there

    async def on_message(self, message: nextcord.Message):
        pass

bot = MyBot()
bot.remove_command("help")

# Logging stuff
logger = logging.getLogger("nextcord")
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename="discord.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,  # Rotate through 5 files
)
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Errors handling
@bot.tree.error
async def on_app_command_error(
    interaction: Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CommandOnCooldown):
        cool_error = nextcord.Embed(
            title="Slow it down bro!",
            description=f"Try again in {error.retry_after:.2f}s.",
            colour=nextcord.Colour.light_grey(),
        )
        await interaction.response.send_message(embed=cool_error, ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        missing_perm = error.missing_permissions[0].replace("_", " ").title()
        per_error = nextcord.Embed(
            title="You're Missing Permissions!",
            description=f"You don't have {missing_perm} permission.",
            colour=nextcord.Colour.light_grey(),
        )
        await interaction.response.send_message(embed=per_error, ephemeral=True)
    elif isinstance(error, app_commands.BotMissingPermissions):
        missing_perm = error.missing_permissions[0].replace("_", " ").title()
        per_error = nextcord.Embed(
            title="I'm Missing Permissions!",
            description=f"I don't have {missing_perm} permission.",
            colour=nextcord.Colour.light_grey(),
        )
        await interaction.response.send_message(embed=per_error, ephemeral=True)
    else:
        error_channel = bot.get_channel(int(os.getenv("ERROR_CHANNEL_ID")))
        await error_channel.send(str(error))
        await interaction.response.send_message(
            "Sorry, an error had occured.\nIf you are facing any issues with me you can always send your </feedback:1027218853127794780>.",
            ephemeral=True,
        )
        raise error

bot.run(os.getenv("BOT_TOKEN"))

