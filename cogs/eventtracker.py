import discord
from discord.ext import commands
import sqlite3
import re
from typing import Union, Optional
from datetime import timedelta
import csv
from io import StringIO

# Init DB
conn = sqlite3.connect('bot.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        message_id INTEGER PRIMARY KEY,
        role_id INTEGER DEFAULT 0,
        event_id INTEGAR DEFAULT 0,
        channel_id INTEGAR DEFAULT 0,
        limits INTEGAR DEFAULT 0)
''')
conn.commit()

class Buttons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="RSVP", style=discord.ButtonStyle.green, custom_id="rsvp")
    async def rsvp_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        result = get_event_info_from_message_id(interaction.message.id)
        role_id = result[0]
        event_id = result[1]
        limit = result[2]

        event = discord.utils.get(interaction.guild.scheduled_events, id=event_id)
        event_name = re.sub("\[.*?\] ", "", event.name)
        remove = r'\[\*\*RSVP HERE\*\*\]\(.*?\)(?:\n)?|\*\*THIS EVENT IS FULL\. DO NOT RSVP\.\*\*(?:\n)?'
        event_description = re.sub(remove, "", event.description)

        role = discord.utils.get(interaction.guild.roles, id=role_id)
        role_int = len(role.members)

        if role in interaction.user.roles:
            await interaction.response.send_message(content=f"You have already RSVPed for {event_name}.", ephemeral=True)
            return
        if role_int >= limit and limit != 0:
            await interaction.response.send_message(content=f"RSVP for {event_name} unsuccessful because the event is full.", ephemeral=True)
            return
        
        await interaction.user.add_roles(role)
        role_int += 1
        await interaction.response.send_message(content=f"You have successfully RSVPed for {event_name}.", ephemeral=True)

        if limit == 0:
            await event.edit(name = event_name, description = f"[**RSVP HERE**]({interaction.message.jump_url})\n" + event_description)    
        elif role_int >= limit:
            event_name = f"[FULL] " + event_name
            await event.edit(name = event_name, description = "**THIS EVENT IS FULL. DO NOT RSVP.**\n" + event_description)
        elif role_int < limit:
            event_name = f"[{role_int}/{limit}] " + event_name
            await event.edit(name = event_name, description = f"[**RSVP HERE**]({interaction.message.jump_url})\n" + event_description)

        embed = make_embed(event, limit, event_name, role_int)
        await interaction.message.edit(embed=embed)
            

    @discord.ui.button(label="UN-RSVP", style=discord.ButtonStyle.red, custom_id="unrsvp")
    async def unrsvp_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        result = get_event_info_from_message_id(interaction.message.id)
        role_id = result[0]
        event_id = result[1]
        limit = result[2]

        event = discord.utils.get(interaction.guild.scheduled_events, id=event_id)
        event_name = re.sub("\[.*?\] ", "", event.name)
        remove = r'\[\*\*RSVP HERE\*\*\]\(.*?\)(?:\n)?|\*\*THIS EVENT IS FULL\. DO NOT RSVP\.\*\*(?:\n)?'
        event_description = re.sub(remove, "", event.description)

        role = discord.utils.get(interaction.guild.roles, id=role_id)
        role_int = len(role.members)

        if role not in interaction.user.roles:
            await interaction.response.send_message(content="No changes have been made because you haven't RSVP'ed.", ephemeral=True)
            return

        await interaction.user.remove_roles(role)
        role_int -= 1
        await interaction.response.send_message(content=f"You have successfully un-RSVPed for {event_name}.", ephemeral=True)

        if limit == 0:
            await event.edit(name = event_name, description = f"[**RSVP HERE**]({interaction.message.jump_url})\n" + event_description)    
        elif role_int >= limit:
            event_name = f"[FULL] " + event_name
            await event.edit(name = event_name, description = "**THIS EVENT IS FULL. DO NOT RSVP.**\n" + event_description)
        elif role_int < limit:
            event_name = f"[{role_int}/{limit}] " + event_name
            await event.edit(name = event_name, description = f"[**RSVP HERE**]({interaction.message.jump_url})\n" + event_description)

        embed = make_embed(event, limit, event_name, role_int)
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="List Attendees", style=discord.ButtonStyle.grey, custom_id="listattendees")
    async def list_users_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        result = get_event_info_from_message_id(interaction.message.id)
        role_id = result[0]
        event_id = result[1]

        event = discord.utils.get(interaction.guild.scheduled_events, id=event_id)
        event_name = re.sub("\[.*?\] ", "", event.name)

        role = discord.utils.get(interaction.guild.roles, id=role_id)
        member_int = len(role.members)

        if len(role.members) == 0:
            await interaction.response.send_message(content="No attendees yet.", ephemeral=True)
        else:
            member_list = "\n- ".join(str(member.mention) for member in role.members)
            await interaction.response.send_message(content=f"**Members attending {event_name}**\n\n- " + member_list + f"\n\nMember Count: {member_int}", ephemeral=True)


# Discord commands
class EventTracking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_load(self):
        self.bot.add_view(Buttons())
        print("Initialized event tracking cog")

    @commands.command(aliases=['createevent', 'makeevent', 'createvent', 'makevent'])
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def setupevent(self, ctx, event: Union[discord.ScheduledEvent, discord.Invite] = None, limit: int = None, channel: discord.TextChannel = None):
        if event is None:
            await ctx.send("!setupevent (event) (limit) (#channel)")
            return
        if limit is None or limit < 0:
            await ctx.send("Error: Invalid number used as the limit")
            return
        if channel is None:
            await ctx.send("Error: No channel has been selected")
            return
        if event.guild != ctx.guild:
            await ctx.send("Error: Invalid event")
            return
        if hasattr(event, "scheduled_event"):
            event = event.scheduled_event
        
        event_id = event.id
        event_name = event.name
        event_description = event.description
        event_check = check_event(event_id)

        if event_check != 0:
            await ctx.send("This event was already setup")
            return

        if limit != 0:
            event_name = f"[0/{limit}] " + event_name
            await event.edit(name = event_name)
        
        embed = make_embed(event, limit, event_name)
        message = await channel.send(embed=embed, view=Buttons())

        guild = ctx.guild

        role_name = f"[EVENT]: {event_name}"
        await guild.create_role(name=role_name)
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        await event.edit(description = f"[**RSVP HERE**]({message.jump_url})\n" + event_description)
        
        setup_event(message.id, role.id, event_id, channel.id, limit)
        await ctx.send("Event has been setup")

    @commands.command(aliases=['fixevent'])
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def updateevent(self, ctx, event: Union[discord.ScheduledEvent, discord.Invite] = None, limit: Optional[int] = None):
        if event is None:
            await ctx.send("!updateevent (event)")
            return
        if event.guild != ctx.guild:
            await ctx.send("Error: Invalid event")
            return
        if hasattr(event, "scheduled_event"):
            event = event.scheduled_event
        
        event_id = event.id
        event_check = check_event(event_id)

        if event_check == 0:
            await ctx.send("This event is not setup")
            return

        result = get_event_info_from_event_id(event_id)
        message_id = result[0]
        channel_id = result[1]
        role_id = result[2]

        if limit is not None:
            change_limit(message_id, limit)
            limit = limit
        if limit is None:
            limit = result[3]

        role = discord.utils.get(ctx.guild.roles, id=role_id)
        role_int = len(role.members)

        event_name = re.sub("\[.*?\] ", "", event.name)
        remove = r'\[\*\*RSVP HERE\*\*\]\(.*?\)(?:\n)?|\*\*THIS EVENT IS FULL\. DO NOT RSVP\.\*\*(?:\n)?'
        event_description = re.sub(remove, '', event.description)
        
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)

        if limit == 0:
            await event.edit(name = event_name, description = f"[**RSVP HERE**]({message.jump_url})\n" + event_description)
        elif role_int >= limit:
            event_name = f"[FULL] " + event_name
            await event.edit(name = event_name, description = "**THIS EVENT IS FULL. DO NOT RSVP.**\n" + event_description)
        elif role_int < limit:
            event_name = f"[{role_int}/{limit}] " + event_name
            await event.edit(name = event_name, description = f"[**RSVP HERE**]({message.jump_url})\n" + event_description)

        embed = make_embed(event, limit, event_name, role_int)
        await message.edit(embed=embed)
        await ctx.send("Event has been updated")

    @commands.command(aliases=['deleteevent', 'removevent', 'deletevent'])
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def removeevent(self, ctx, event: Union[discord.ScheduledEvent, discord.Invite] = None):
        if event is None:
            await ctx.send("!removeevent (event)")
            return
        if event.guild != ctx.guild:
            await ctx.send("Error: Invalid event")
            return
        if hasattr(event, "scheduled_event"):
            event = event.scheduled_event
        
        event_id = event.id
        event_check = check_event(event_id)

        if event_check == 0:
            await ctx.send("This event was never setup")
            return
        result = get_event_info_from_event_id(event_id)

        message_id = result[0]
        channel_id = result[1]
        role_id = result[2]

        event_name = re.sub("\[.*?\] ", "", event.name)
        remove = r'\[\*\*RSVP HERE\*\*\]\(.*?\)(?:\n)?|\*\*THIS EVENT IS FULL\. DO NOT RSVP\.\*\*(?:\n)?'
        event_description = re.sub(remove, '', event.description)
        await event.edit(name = event_name, description = event_description)

        try:
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
        except:
            pass

        try:
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            await role.delete()
        except:
            pass

        remove_event(message_id)
        await ctx.send("Event deleted succesfully")

    @commands.command()
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def forceremoveevent(self, ctx, event: int = None):
        if event is None:
            await ctx.send("!forceremoveevent (event)")
            return
        
        try:
            result = get_event_info_from_event_id(event)
            message_id = result[0]
            channel_id = result[1]
            role_id = result[2]
        except:
            await ctx.send("Event doesn't exist")
            return
        
        try:
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
        except:
            pass

        try:
            role = discord.utils.get(ctx.guild.roles, id=role_id)
            await role.delete()
        except:
            pass

        remove_event(message_id)
        await ctx.send("Event deleted succesfully")

    @commands.command()
    @commands.has_permissions(manage_events=True)
    @commands.bot_has_permissions(manage_events=True, manage_roles=True)
    async def exportcsv(self, ctx, event: Union[discord.ScheduledEvent, discord.Invite] = None):
        if event is None:
            await ctx.send("!exportcsv (event)")
            return
        if event.guild != ctx.guild:
            await ctx.send("Error: Invalid event")
            return
        if hasattr(event, "scheduled_event"):
            event = event.scheduled_event

        event_id = event.id
        event_check = check_event(event_id)

        if event_check == 0:
            await ctx.send("This event is not setup")
            return
        
        result = get_event_info_from_event_id(event_id)
        role_id = result[2]

        event_name = re.sub("\[.*?\] ", "", event.name)

        role = discord.utils.get(ctx.guild.roles, id=role_id)

        firstrow = ['Attendee', 'Attended', 'Paid', 'Method of Payment']

        file = StringIO()
        write = csv.writer(file)

        write.writerow(firstrow)
        for x in role.members:
            write.writerow([x.name])

        file.seek(0)

        await ctx.send(file=discord.File(fp=file, filename=f"{event_name} Spreadsheet Log.csv"))
        
    async def cog_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.BadUnionArgument):
            await ctx.send("Error: You didn't provide a valid event")
        elif isinstance(error, discord.ext.commands.errors.ChannelNotFound):
            await ctx.send("Error: You didn't provide a valid channel")
        elif isinstance(error, discord.ext.commands.errors.BadArgument):
            await ctx.send("Error: Invalid number used as the limit")
        # elif isinstance(error, discord.ext.commands.errors.CommandInvokeError):
        #     await ctx.send("Error: ID not found")
        else:
            raise error
        
    @commands.Cog.listener()
    @commands.bot_has_permissions(manage_events=True)
    async def on_scheduled_event_create(self, event):
        auto_create_event = check_auto_create_event(event.guild.id)
        if auto_create_event == 0:
            return
        
        event_id = event.id
        event_name = event.name
        event_description = event.description
        
        channel = self.bot.get_channel(auto_create_event)

        limit_str = re.search(r"\[(.*?)\]", event_name)

        if limit_str:
            limit = limit_str.group(1)
        else:
            limit = 0

        event_name = re.sub("\[.*?\] ", "", event.name)

        if limit != 0:
            event_name = f"[0/{limit}] " + event_name
        await event.edit(name = event_name)
        
        embed = make_embed(event, limit, event_name)
        message = await channel.send(embed=embed, view=Buttons())

        guild = event.guild

        role_name = f"[EVENT]: {event_name}"
        await guild.create_role(name=role_name)
        role = discord.utils.get(event.guild.roles, name=role_name)

        await event.edit(description = f"[**RSVP HERE**]({message.jump_url})\n" + event_description)
        
        setup_event(message.id, role.id, event_id, channel.id, limit)

    @commands.Cog.listener()
    @commands.bot_has_permissions(manage_events=True)
    async def on_scheduled_event_delete(self, event):
        auto_event_delete = check_auto_delete_event(event.guild.id)
        if auto_event_delete == 0:
            return

        event_id = event.id
        event_check = check_event(event_id)

        if event_check == 0:
            return
        result = get_event_info_from_event_id(event_id)

        message_id = result[0]
        channel_id = result[1]
        role_id = result[2]

        try:
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
        except:
            pass

        try:
            role = discord.utils.get(event.guild.roles, id=role_id)
            await role.delete()
        except:
            pass

        remove_event(message_id)

    @commands.Cog.listener()
    @commands.bot_has_permissions(manage_events=True)
    async def on_scheduled_event_update(self, event, after):
        if after.status != discord.EventStatus.completed and after.status != discord.EventStatus.cancelled:
            return
        
        auto_event_delete = check_auto_delete_event(event.guild.id)
        if auto_event_delete == 0:
            return

        event_id = event.id
        event_check = check_event(event_id)

        if event_check == 0:
            return
        result = get_event_info_from_event_id(event_id)

        message_id = result[0]
        channel_id = result[1]
        role_id = result[2]
        channel = self.bot.get_channel(channel_id)

        auto_archive_event = check_auto_archive_event(event.guild.id)

        try:
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)
            if after.status == discord.EventStatus.completed and auto_archive_event != 0:
                archive_channel = self.bot.get_channel(auto_archive_event)
                await archive_channel.send("Event Archived:", embed=message.embeds[0])
            await message.delete()
        except:
            pass

        try:
            role = discord.utils.get(event.guild.roles, id=role_id)
            if after.status == discord.EventStatus.completed and auto_archive_event != 0:
                member_list = "\n- ".join(str(member.mention) for member in role.members)
                await archive_channel.send(member_list + f"\n\nMember Count: {len(role.members)}")
                firstrow = ['Attendee', 'Attended', 'Paid', 'Method of Payment']

                file = StringIO()
                write = csv.writer(file)

                write.writerow(firstrow)
                for x in role.members:
                    write.writerow([x.name])

                file.seek(0)

                await archive_channel.send(file=discord.File(fp=file, filename=f"{event.name} Spreadsheet Log.csv"))
            await role.delete()
        except:
            pass

        remove_event(message_id)




def check_event(event_id):
    cursor.execute('SELECT role_id FROM events WHERE event_id = ?', (event_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def get_event_info_from_event_id(event_id):
    cursor.execute('SELECT message_id, channel_id, role_id, limits FROM events WHERE event_id = ?', (event_id,))
    result = cursor.fetchone()
    return result if result else 0

def get_event_info_from_message_id(message_id):
    cursor.execute('SELECT role_id, event_id, limits FROM events WHERE message_id = ?', (message_id,))
    result = cursor.fetchone()
    return result if result else 0

def remove_event(message_id):
    cursor.execute('DELETE FROM events WHERE message_id = ?', (message_id,))
    conn.commit()

def setup_event(message_id, role_id, event_id, channel_id, limit):
    cursor.execute('INSERT OR IGNORE INTO events (message_id, role_id, event_id, channel_id, limits) VALUES (?, ?, ?, ?, ?)', (message_id, role_id, event_id, channel_id, limit))
    conn.commit()

def change_limit(message_id, limit):
    cursor.execute('UPDATE events SET limits=? WHERE message_id=?', (limit, message_id))
    conn.commit()

def check_auto_create_event(guild_id):
    cursor.execute('SELECT auto_create_event FROM settings WHERE guild_id = ?', (guild_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def check_auto_delete_event(guild_id):
    cursor.execute('SELECT auto_delete_event FROM settings WHERE guild_id = ?', (guild_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def check_auto_archive_event(guild_id):
    cursor.execute('SELECT auto_archive_event FROM settings WHERE guild_id = ?', (guild_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def make_embed(event, limit, event_name, members=0):
    remove = r'\[\*\*RSVP HERE\*\*\]\(.*?\)(?:\n)?|\*\*THIS EVENT IS FULL\. DO NOT RSVP\.\*\*(?:\n)?'
    event_description = re.sub(remove, '', event.description)

    embed = discord.Embed(title=event_name, description=event_description, url=event.url)

    # People who leave the server causes the bot to error out with the user
    # This is a simple fix for it (maybe ill make it more neat later)
    try:
        embed.set_author(name=event.creator, icon_url=event.creator.avatar)
    except:
        pass

    start_time = f"<t:{int(event.start_time.timestamp())}:F>"

    if event.end_time == None:
        embed.add_field(name="Time", value=f"{start_time}")
    elif event.end_time - event.start_time < timedelta(hours=12):
        end_time = f"<t:{int(event.end_time.timestamp())}:t>"
        embed.add_field(name="Time", value=f"{start_time}\nto {end_time}")
    elif event.end_time - event.start_time >= timedelta(hours=12):
        end_time = f"<t:{int(event.end_time.timestamp())}:F>"
        embed.add_field(name="Time", value=f"{start_time}\nto {end_time}")
    
    if event.location != None:
        event_location = re.sub(r' ', '%20', event.location)
        maps_url = f"https://www.google.com/maps/search/?api=1&query={event_location}"
        embed.add_field(name="Location", value=f"[{event.location}]({maps_url})")
    
    if limit != 0:
        embed.add_field(name="Max People", value=f"{members}/{limit}")
        
    return embed

async def setup(bot):
    await bot.add_cog(EventTracking(bot))