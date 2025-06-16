import os

import discord
from discord import app_commands
from dotenv import load_dotenv
import httpx

from . import htbapi


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "User-Agent": "htbpanel-bot/0.1",
    }


class HTBPanelBot(discord.Client):
    def __init__(self, htb_token: str):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.htb_token = htb_token
        self.client = httpx.AsyncClient(headers=headers(htb_token), timeout=30)

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def close(self) -> None:
        await self.client.aclose()
        await super().close()


bot: HTBPanelBot | None = None


@app_commands.command(name="userinfo", description="Show HTB user information")
async def userinfo(interaction: discord.Interaction):
    info = await htbapi.query_user_info(bot.client)
    user = info["user"]
    msg = f"Name: {user['name']}\nID: {user['id']}\nVIP: {user['vip']}"
    await interaction.response.send_message(msg, ephemeral=True)


@app_commands.command(name="machineinfo", description="Get machine information")
@app_commands.describe(name="Machine name")
async def machineinfo(interaction: discord.Interaction, name: str):
    info = await htbapi.query_box_info(bot.client, name)
    msg = (
        f"Name: {info['name']}\n"
        f"Difficulty: {info['difficultyText']}\n"
        f"OS: {info['os']}\n"
        f"IP: {info['ip']}"
    )
    await interaction.response.send_message(msg, ephemeral=True)


@app_commands.command(name="machinestart", description="Start a machine")
@app_commands.describe(machine_id="Machine ID")
async def machinestart(interaction: discord.Interaction, machine_id: int):
    res = await htbapi.machine_action(bot.client, "start", machine_id)
    msg = "Machine started" if res.get("success") else res.get("message", "Error")
    await interaction.response.send_message(msg, ephemeral=True)


@app_commands.command(name="machinestop", description="Stop a machine")
@app_commands.describe(machine_id="Machine ID")
async def machinestop(interaction: discord.Interaction, machine_id: int):
    res = await htbapi.machine_action(bot.client, "stop", machine_id)
    msg = "Machine stopped" if res.get("success") else res.get("message", "Error")
    await interaction.response.send_message(msg, ephemeral=True)


@app_commands.command(name="machinereset", description="Reset a machine")
@app_commands.describe(machine_id="Machine ID")
async def machinereset(interaction: discord.Interaction, machine_id: int):
    res = await htbapi.machine_action(bot.client, "reset", machine_id)
    msg = "Machine reset" if res.get("success") else res.get("message", "Error")
    await interaction.response.send_message(msg, ephemeral=True)


def main() -> None:
    load_dotenv()
    discord_token = os.getenv("DISCORD_TOKEN")
    htb_key = os.getenv("HTB_KEY")
    if not discord_token or not htb_key:
        raise RuntimeError("DISCORD_TOKEN and HTB_KEY must be set in .env")

    global bot
    bot = HTBPanelBot(htb_key)
    bot.tree.add_command(userinfo)
    bot.tree.add_command(machineinfo)
    bot.tree.add_command(machinestart)
    bot.tree.add_command(machinestop)
    bot.tree.add_command(machinereset)

    bot.run(discord_token)


if __name__ == "__main__":
    main()
