Here is your complete, fully cleaned, and finalized **`app.py`** file! 

I have gone through and removed all the duplicate code blocks, fixed the `target_id` swiping bug, implemented the side-by-side buttons on the new instructions panel, and ensured the AI override logic is perfectly integrated. 

You can completely delete everything in your current `app.py` and replace it entirely with this code:

```python
import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

import database
import analyzer

load_dotenv()

# Memory for UI states
watchlist_db = {}
undo_history = {} 

def get_ticket_channel(guild, user_id):
    config = database.get_config(guild.id)
    if not config or not config.get("match_category_id"): return None
    category = guild.get_channel(int(config["match_category_id"]))
    if not category: return None
    
    for channel in category.text_channels:
        if not channel.name.startswith("ticket-"): continue
        for target, overwrite in channel.overwrites.items():
            if isinstance(target, discord.Member) and target.id == user_id:
                return channel
    return None

# ---------------------------------------------------------
# BOT CORE INITIALIZATION
# ---------------------------------------------------------
class MatchmakingBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        
    async def setup_hook(self):
        await self.add_cog(MatchManager(self))
        # Persist Views across restarts
        self.add_view(TicketDashboardView()) 
        self.add_view(CommunityToolsView()) 
        self.add_view(SupportTicketView())
        self.add_view(AppActionView())
        self.add_view(MatchmakingPanelView())
        
        await self.tree.sync()
        print("Bot is online. Commands synced.")

bot = MatchmakingBot()

# ---------------------------------------------------------
# UI & MODALS
# ---------------------------------------------------------
class FlagModal(discord.ui.Modal, title='Report Profile'):
    reason = discord.ui.TextInput(label='Why are you reporting this user?', style=discord.TextStyle.paragraph, required=True)
    def __init__(self, target_id):
        super().__init__()
        self.target_id = target_id
    async def on_submit(self, interaction: discord.Interaction):
        config = database.get_config(interaction.guild.id)
        if config and config.get("staff_channel_id"):
            chan = interaction.guild.get_channel(int(config["staff_channel_id"]))
            staff_role_id = config.get("staff_role_id")
            ping = f"<@&{staff_role_id}> " if staff_role_id else ""
            if chan: 
                await chan.send(f"{ping}🚨 **PROFILE REPORT:** {interaction.user.mention} flagged <@{self.target_id}>.\n**Reason:** {self.reason.value}")
        await interaction.response.send_message("✅ Your report has been securely sent to the staff.", ephemeral=True)

class EditProfileModal(discord.ui.Modal, title='Update Your Intro'):
    intro = discord.ui.TextInput(label='Paste Your New Intro Here', style=discord.TextStyle.paragraph, required=True, max_length=3000)
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("⏳ Re-analyzing your profile...", ephemeral=True)
        try:
            parsed_data = analyzer.analyze_intro(self.intro.value)
            if parsed_data.get("is_toxic"):
                return await interaction.followup.send(f"🛑 Your edit was flagged for toxicity: {parsed_data.get('toxic_reason')}. Profile not updated.", ephemeral=True)
            
            config = database.get_config(interaction.guild.id)
            min_age = config.get("min_age", 13) if config else 13
            if parsed_data.get("age", 0) < min_age: 
                return await interaction.followup.send(f"You must be {min_age} or older.", ephemeral=True)
            
            database.save_profile(interaction.user.id, interaction.guild.id, parsed_data, self.intro.value)
            await interaction.followup.send("✅ Profile updated successfully!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send("❌ Analysis failed. Please check your intro format.", ephemeral=True)

class MyProfileView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label='✏️ Edit Intro', style=discord.ButtonStyle.primary)
    async def edit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditProfileModal())

class TicketDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label='🆘 Request Staff Help', style=discord.ButtonStyle.danger, custom_id='ticket_help_btn')
    async def help_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = database.get_config(interaction.guild.id)
        if config and config.get("staff_channel_id"):
            staff_chan = interaction.guild.get_channel(int(config["staff_channel_id"]))
            if staff_chan: 
                await staff_chan.send(f"🚨 **TICKET HELP REQUEST:** {interaction.user.mention} needs assistance in {interaction.channel.mention}!")
        await interaction.response.send_message("✅ Staff have been notified. Someone will be with you shortly! 🍃", ephemeral=True)

    @discord.ui.button(label='🗑️ Delete Dashboard', style=discord.ButtonStyle.secondary, custom_id='ticket_close_btn')
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.name.startswith("underage-") or interaction.channel.name.startswith("flagged-"):
            return await interaction.response.send_message("❌ This ticket is locked for staff review.", ephemeral=True)
        await interaction.response.send_message("🗑️ Deleting in 3 seconds...", ephemeral=True)
        try: database.delete_profile(interaction.user.id, interaction.guild.id)
        except: pass
        await asyncio.sleep(3)
        await interaction.channel.delete()

class MatchmakingPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label='💖 Open Matchmaking Dashboard', style=discord.ButtonStyle.success, custom_id='btn_open_match_ticket')
    async def open_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # 0. Check Watchlist for Ticket Bans
        guild_id = str(interaction.guild.id)
        if guild_id in watchlist_db and interaction.user.id in watchlist_db[guild_id]:
            if watchlist_db[guild_id][interaction.user.id].get("ticket_ban"):
                return await interaction.followup.send("🛑 **Action Denied:** You have been restricted from opening matchmaking tickets by the moderation team.", ephemeral=True)
        
        active_pair = database.get_user_pairing(interaction.user.id, interaction.guild.id)
        if active_pair:
            return await interaction.followup.send(
                "🛑 **Action Denied:** You are already in an active match! "
                "You must unpair before you can start a new matchmaking journey.", 
                ephemeral=True
            )

        existing_ticket = get_ticket_channel(interaction.guild, interaction.user.id)
        if existing_ticket:
            return await interaction.followup.send(f"⚠️ You already have an open ticket: {existing_ticket.mention}", ephemeral=True)

        config = database.get_config(interaction.guild.id)
        if not config or not config.get("match_category_id"):
            return await interaction.followup.send("❌ Matchmaking is not set up on this server.", ephemeral=True)

        cat = interaction.guild.get_channel(int(config["match_category_id"]))
        if not cat:
            return await interaction.followup.send("❌ Matchmaking category not found.", ephemeral=True)

        ticket = await cat.create_text_channel(name=f"ticket-{interaction.user.name}")
        
        await ticket.set_permissions(interaction.user, read_messages=True, send_messages=True)
        await ticket.set_permissions(interaction.guild.default_role, read_messages=False)

        intro_channel_mention = "<#123456789012345678>" 
        
        embed = discord.Embed(
            title="✨ Welcome to your Matchmaking Dashboard! ✨",
            description=(
                "We're so excited to help you find your perfect match! 💖\n\n"
                "**📜 How to get started:**\n"
                f"**1.** Head over to {intro_channel_mention} to read the rules and grab the intro template.\n"
                "**2.** Paste your filled-out intro directly into this channel.\n"
                "**3.** Our AI Cupid will process it and start showing you profiles!\n\n"
                "**💔 Want to end a match later?**\n"
                "If you ever need to close your cafe and end a match, just return to the main instructions channel and click the **💔 Request Unpair** button."
            ),
            color=discord.Color.from_rgb(180, 230, 180) # Soft, pastel sage green 🌿
        )
        embed.set_footer(text="Have fun and happy swiping! 🌸")

        await ticket.send(content=f"Welcome {interaction.user.mention}!", embed=embed, view=TicketDashboardView())
        await interaction.followup.send(f"✅ Created: {ticket.mention}", ephemeral=True)

    @discord.ui.button(label='💔 Request Unpair', style=discord.ButtonStyle.danger, custom_id='btn_request_unpair')
    async def request_unpair_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        # Fetch the active pairing from the database
        pair_info = database.get_user_pairing(interaction.user.id, interaction.guild.id)
        if not pair_info: 
            return await interaction.followup.send("❌ You don't have an active match right now!", ephemeral=True)
            
        # Determine who the partner is
        partner_id = pair_info.get('user2_id') if str(pair_info.get('user1_id')) == str(interaction.user.id) else pair_info.get('user1_id')
        
        # Calculate the exact time the pair was made
        try:
            dt = datetime.fromisoformat(pair_info.get('start_time').replace('Z', '+00:00'))
            unix_time = int(dt.timestamp())
        except: 
            unix_time = int(time.time())
        
        # Fetch category config to organize the ticket cleanly
        config = database.get_config(interaction.guild.id)
        ticket_category_id = config.get("ticket_category_id") if config else None
        category = interaction.guild.get_channel(int(ticket_category_id)) if ticket_category_id else None
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), 
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), 
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        ticket_channel = await interaction.guild.create_text_channel(
            name=f"unpair-{interaction.user.name}", 
            category=category,
            overwrites=overwrites
        )
        
        # Build the cozy, clear embed with the pairing details
        embed = discord.Embed(
            title="💔 Unpair Request", 
            description=(
                "Hi there! Sometimes connections just don't work out, and that's perfectly okay. 🌱\n\n"
                "Please leave a brief message letting us know why you'd like to end the match. A staff member will be here shortly to close your cafe safely."
            ), 
            color=discord.Color.from_rgb(255, 182, 193) # Soft pastel pink
        )
        
        # Display the specific pairing information requested
        embed.add_field(name="👤 Requesting User", value=interaction.user.mention, inline=True)
        embed.add_field(name="💞 Current Partner", value=f"<@{partner_id}>", inline=True)
        embed.add_field(name="⏱️ Paired For", value=f"<t:{unix_time}:R> (Since <t:{unix_time}:f>)", inline=False)
        
        await ticket_channel.send(content=f"Welcome {interaction.user.mention}, staff will review your request shortly.", embed=embed, view=SupportTicketView())
        await interaction.followup.send(f"✅ Your unpair request ticket has been created! Please go to {ticket_channel.mention}", ephemeral=True)


class StaffApprovalView(discord.ui.View):
    def __init__(self, user_id, parsed_data, raw_intro, ticket_channel_id):
        super().__init__(timeout=None)
        self.user_id, self.parsed_data, self.raw_intro, self.ticket_channel_id = user_id, parsed_data, raw_intro, ticket_channel_id

    @discord.ui.button(label='✅ Approve Profile', style=discord.ButtonStyle.success)
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        database.save_profile(self.user_id, interaction.guild.id, self.parsed_data, self.raw_intro)
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content=f"✅ **Approved** by {interaction.user.mention}", view=self)
        ticket = interaction.guild.get_channel(self.ticket_channel_id)
        if ticket:
            await ticket.send(f"🎉 <@{self.user_id}>, your profile was **approved**! Finding matches...")
            view = SwipeView(self.user_id, None, interaction.guild.id)
            await view.show_next_init(ticket)

    @discord.ui.button(label='❌ Reject', style=discord.ButtonStyle.danger)
    async def reject_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content=f"❌ **Rejected** by {interaction.user.mention}", view=self)
        ticket = interaction.guild.get_channel(self.ticket_channel_id)
        if ticket: await ticket.send(f"⛔ <@{self.user_id}>, your profile was **rejected**. Please edit and try again.")

class AppActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label='✅ Accept', style=discord.ButtonStyle.success, custom_id='app_accept_btn')
    async def accept_app(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = int(interaction.message.embeds[0].footer.text.split(": ")[1])
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content=f"✅ **Accepted** by {interaction.user.mention}", view=self)
        try:
            applicant = await interaction.guild.fetch_member(user_id)
            await applicant.send(f"🎉 Your staff application for **{interaction.guild.name}** was ACCEPTED! Congrats! Please wait for more info from the team.")
        except: pass

    @discord.ui.button(label='❌ Reject', style=discord.ButtonStyle.danger, custom_id='app_reject_btn')
    async def reject_app(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = int(interaction.message.embeds[0].footer.text.split(": ")[1])
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content=f"❌ **Rejected** by {interaction.user.mention}", view=self)
        try:
            applicant = await interaction.guild.fetch_member(user_id)
            await applicant.send(f"⛔ Update: Your staff application for **{interaction.guild.name}** was declined. Thank you for applying!")
        except: pass

class StaffAppModal(discord.ui.Modal, title='Staff Application'):
    def __init__(self, guild_id):
        super().__init__()
        self.guild_id = guild_id
        config = database.get_config(guild_id)
        self.questions = config.get("app_questions", ["Why do you want to be staff?", "What is your timezone?"])
        for i, question in enumerate(self.questions[:5]):
            self.add_item(discord.ui.TextInput(label=question[:45], style=discord.TextStyle.paragraph, required=True, custom_id=f"app_q_{i}"))
    async def on_submit(self, interaction: discord.Interaction):
        config = database.get_config(self.guild_id)
        log_chan = interaction.guild.get_channel(int(config.get("app_log_channel_id")))
        embed = discord.Embed(title=f"📋 New Staff App: {interaction.user.name}", color=discord.Color.blue())
        for item in self.children: embed.add_field(name=item.label, value=item.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id}")
        await log_chan.send(embed=embed, view=AppActionView())
        await interaction.response.send_message("✅ Application submitted!", ephemeral=True)

class SupportTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label='🔒 Close Ticket', style=discord.ButtonStyle.danger, custom_id='close_support_btn')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Closing in 3 seconds...", ephemeral=False)
        await asyncio.sleep(3)
        await interaction.channel.delete()

class CommunityToolsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label='🎫 Open Support Ticket', style=discord.ButtonStyle.primary, custom_id='btn_open_support')
    async def open_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = database.get_config(interaction.guild.id)
        category = interaction.guild.get_channel(int(config["ticket_category_id"]))
        overwrites = {interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        ticket_channel = await category.create_text_channel(name=f"support-{interaction.user.name.lower()}", overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
        await ticket_channel.send(f"Welcome {interaction.user.mention}! Describe your issue.", view=SupportTicketView())

    @discord.ui.button(label='📋 Apply for Staff', style=discord.ButtonStyle.success, custom_id='btn_apply_staff')
    async def apply_staff_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StaffAppModal(interaction.guild.id))

class CafeActionView(discord.ui.View):
    def __init__(self, user1_id, user2_id):
        super().__init__(timeout=None)
        self.user1_id = user1_id
        self.user2_id = user2_id

    @discord.ui.button(label='❤️ Keep Cafe Open', style=discord.ButtonStyle.success, custom_id='cafe_keep_btn')
    async def keep_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.user1_id, self.user2_id]:
            return await interaction.response.send_message("Only the matched users can vote!", ephemeral=True)
        await interaction.response.send_message(f"✅ {interaction.user.mention} voted to keep the cafe open!")

    @discord.ui.button(label='💔 Close Cafe', style=discord.ButtonStyle.danger, custom_id='cafe_close_btn')
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.user1_id, self.user2_id]:
            return await interaction.response.send_message("Only the matched users can vote!", ephemeral=True)
            
        await interaction.response.send_message(f"🔒 {interaction.user.mention} decided to end the match. This cafe will close shortly.")
        database.end_pairing(self.user1_id, self.user2_id, interaction.guild.id)
        
        await asyncio.sleep(10)
        await interaction.channel.delete()

# ---------------------------------------------------------
# CAFE CREATION HELPER
# ---------------------------------------------------------
async def create_cafe_channel(guild: discord.Guild, user1: discord.Member, user2: discord.Member):
    config = database.get_config(guild.id)
    if not config: return
    
    # 1. Public Announcement
    pairs_channel_id = config.get("pairs_channel_id")
    if pairs_channel_id and str(pairs_channel_id).isdigit():
        pairs_channel = guild.get_channel(int(pairs_channel_id))
        if pairs_channel:
            await pairs_channel.send(f"💖 **New Match!** {user1.mention} and {user2.mention} have been paired! ☕")

    # 2. Cafe Creation
    cafe_category_id = config.get("cafe_category_id")
    if cafe_category_id and str(cafe_category_id).isdigit():
        cafe_category = guild.get_channel(int(cafe_category_id))
        if cafe_category:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user1: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                user2: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            staff_role_id = config.get("staff_role_id")
            if staff_role_id and str(staff_role_id).isdigit():
                staff_role = guild.get_role(int(staff_role_id))
                if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            cafe_channel = await cafe_category.create_text_channel(
                name=f"☕-cafe-{user1.name}-{user2.name}",
                overwrites=overwrites,
                topic="Your 24-hour private cafe. Be respectful and have fun!"
            )
            
            # 3. AI Icebreaker Logic
            profile1 = database.get_profile(user1.id, guild.id)
            profile2 = database.get_profile(user2.id, guild.id)
            
            likes1 = profile1.get('likes', []) if profile1 else ["Nothing listed"]
            likes2 = profile2.get('likes', []) if profile2 else ["Nothing listed"]
            
            icebreaker_text = analyzer.generate_icebreaker(likes1, likes2)

            embed = discord.Embed(
                title="☕ Welcome to your Private Cafe!",
                description=f"You have **24 hours** to chat and see if you vibe. Before the timer runs out, click the buttons below to decide if you want to stay matched!",
                color=discord.Color.purple()
            )
            embed.add_field(name="🤖 Cupid's Icebreaker:", value=f"*{icebreaker_text}*")
            
            await cafe_channel.send(content=f"{user1.mention} {user2.mention}", embed=embed, view=CafeActionView(user1.id, user2.id))

# ---------------------------------------------------------
# SWIPE DECK
# ---------------------------------------------------------
class SwipeView(discord.ui.View):
    def __init__(self, uid, tid, gid):
        super().__init__(timeout=None)
        self.uid, self.tid, self.gid = uid, tid, gid

    async def show_next_init(self, channel, is_alert=False):
        matches = database.get_strict_matches(self.uid, self.gid)
        if not matches:
            if not is_alert: await channel.send("📭 **No more matches right now!**")
            return
        next_user = matches[0]
        self.tid = next_user['user_id']
        embed = discord.Embed(title=f"Match: {next_user.get('name')} ({next_user.get('age')})", description=f"**Intro:**\n{next_user.get('raw_intro')}", color=discord.Color.blue())
        await channel.send(embed=embed, view=self)

    async def show_next(self, interaction):
        matches = database.get_strict_matches(self.uid, self.gid)
        if not matches: 
            return await interaction.response.edit_message(content="📭 No more matches.", embed=None, view=None)
        next_user = matches[0]
        self.tid = next_user['user_id']
        embed = discord.Embed(title=f"Match: {next_user.get('name')} ({next_user.get('age')})", description=f"**Intro:**\n{next_user.get('raw_intro')}", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='✅ Express Interest', style=discord.ButtonStyle.success)
    async def interest(self, interaction, button):
        # 1. Save the ID of the person we are currently swiping on!
        target_id = self.tid 
        
        is_match = database.record_swipe(self.uid, target_id, self.gid, True)
        
        if is_match:
            database.create_pairing(self.uid, target_id, self.gid)
            
            await interaction.response.edit_message(content="🎉 **IT'S A MATCH!** Setting up your private cafe now. This dashboard will self-destruct in 5 seconds to keep the server clean!", embed=None, view=None)
            
            user1 = interaction.guild.get_member(int(self.uid)) or await interaction.guild.fetch_member(int(self.uid))
            user2 = interaction.guild.get_member(int(target_id)) or await interaction.guild.fetch_member(int(target_id))
            
            if user1 and user2:
                asyncio.create_task(create_cafe_channel(interaction.guild, user1, user2))
            
            await asyncio.sleep(5)
            try:
                await interaction.channel.delete()
            except:
                pass
        else:
            matches = database.get_strict_matches(self.uid, self.gid)
            if not matches: 
                return await interaction.response.edit_message(
                    content="✅ **Liked!** They have been notified.\n\n📭 **No other compatible profiles right now. When we find one, it will be sent here!** 🐾", 
                    embed=None, 
                    view=None
                )
            
            # 2. Edit the CURRENT message to lock it in and remove the buttons
            await interaction.response.edit_message(content="✅ *Liked! They have been notified. Looking for a new profile...*", view=None)

            # 3. Send notification to the person we JUST liked (using target_id)
            target_ticket = get_ticket_channel(interaction.guild, int(target_id))
            if target_ticket:
                swiper_profile = database.get_profile(self.uid, self.gid)
                if swiper_profile:
                    notify_embed = discord.Embed(
                        title=f"🔔 Someone is interested in you!",
                        description=f"**{swiper_profile.get('name')} ({swiper_profile.get('age')})** swiped right! Do you want to match back?\n\n**Intro:**\n{swiper_profile.get('raw_intro')}",
                        color=discord.Color.gold()
                    )
                    # Note: We pass target_id here so the view knows who is who!
                    view = SwipeView(uid=target_id, tid=self.uid, gid=self.gid)
                    await target_ticket.send(content=f"Hey <@{target_id}>, you have a new match request!", embed=notify_embed, view=view)

            # 4. Prepare and send the NEXT profile
            next_user = matches[0]
            self.tid = next_user['user_id']
            embed = discord.Embed(
                title=f"Match: {next_user.get('name')} ({next_user.get('age')})", 
                description=f"**Intro:**\n{next_user.get('raw_intro')}", 
                color=discord.Color.from_rgb(180, 230, 255) # Soft pastel blue
            )
            
            await interaction.channel.send(embed=embed, view=self)

    @discord.ui.button(label='❌ Pass', style=discord.ButtonStyle.danger)
    async def deny(self, interaction, button):
        # Record the left swipe
        database.record_swipe(self.uid, self.tid, self.gid, False)
        
        # Check for new matches
        matches = database.get_strict_matches(self.uid, self.gid)
        
        if not matches: 
            return await interaction.response.edit_message(
                content="❌ **Passed!**\n\n📭 **No other compatible profiles right now. When we find one, it will be sent here!** 🌱", 
                embed=None, 
                view=None
            )
        
        # 1. Edit the CURRENT message to show it was passed and remove the buttons
        await interaction.response.edit_message(
            content="❌ *Passed! Okay, looking for a new profile...*", 
            view=None
        )
        
        # 2. Prepare the NEXT profile
        next_user = matches[0]
        self.tid = next_user['user_id']
        embed = discord.Embed(
            title=f"Match: {next_user.get('name')} ({next_user.get('age')})", 
            description=f"**Intro:**\n{next_user.get('raw_intro')}", 
            color=discord.Color.from_rgb(180, 230, 255) # Soft pastel blue
        )
        
        # 3. Send the NEXT profile as a brand NEW message
        await interaction.channel.send(embed=embed, view=self)

    @discord.ui.button(label='✅ Vouch', style=discord.ButtonStyle.secondary)
    async def vouch(self, interaction, button):
        database.add_vouch(self.tid, self.gid)
        await interaction.response.send_message(f"✅ You gave a green flag to this profile! 🐾", ephemeral=True)

    @discord.ui.button(label='🚩 Report', style=discord.ButtonStyle.secondary)
    async def report(self, interaction, button):
        await interaction.response.send_modal(FlagModal(target_id=self.tid))

# ---------------------------------------------------------
# AUTOMATION COG (Handles Messages & Timers)
# ---------------------------------------------------------
class MatchManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cleanup_loop.start()
        self.auto_discover_loop.start()
        self.game_timer_loop.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild: return
        config = database.get_config(message.guild.id)
        if not config or str(message.channel.category_id) != config.get("match_category_id"): return
        
        # Check for standard "AGE" or the specific aesthetic "ᴀɢᴇ"
        if "➤" in message.content and ("AGE" in message.content.upper() or "ᴀɢᴇ" in message.content):
            await message.add_reaction("⏳")
            parsed = analyzer.analyze_intro(message.content)
            
            # Setup Server Watchlist Key
            guild_id = str(message.guild.id)
            if guild_id not in watchlist_db: watchlist_db[guild_id] = {}

            # Check if staff has manually overridden the AI for this user
            is_whitelisted = watchlist_db[guild_id].get(message.author.id, {}).get("whitelisted", False)

            # Handle Toxicity (Only if they aren't whitelisted!)
            if parsed.get("is_toxic") and not is_whitelisted:
                watchlist_db[guild_id][message.author.id] = {"note": f"AUTO-FLAG: {parsed.get('toxic_reason')}", "ticket_ban": True}
                await message.reply(f"🛑 Flagged for toxicity: {parsed.get('toxic_reason')}")
                await message.channel.edit(name=f"flagged-{message.author.name}")
                
                # PING STAFF FOR TOXICITY
                staff_chan_id = config.get("staff_channel_id")
                staff_role_id = config.get("staff_role_id")
                ping = f"<@&{staff_role_id}> " if staff_role_id else ""
                
                if staff_chan_id:
                    staff_chan = message.guild.get_channel(int(staff_chan_id))
                    if staff_chan:
                        await staff_chan.send(f"🚨 {ping}**TOXICITY ALERT:** {message.author.mention} was auto-flagged. Reason: {parsed.get('toxic_reason')}. Ticket: {message.channel.mention}")
                return
            
            # Handle Underage
            user_age = parsed.get("age", 0)
            if user_age < 13:
                watchlist_db[guild_id][message.author.id] = {"note": f"AUTO-FLAG: Underage ({user_age})", "ticket_ban": True}
                await message.channel.edit(name=f"underage-{message.author.name}")
                await message.channel.set_permissions(message.author, send_messages=False)
                
                # PING STAFF FOR UNDERAGE
                staff_chan_id = config.get("staff_channel_id")
                staff_role_id = config.get("staff_role_id")
                ping = f"<@&{staff_role_id}> " if staff_role_id else ""
                
                if staff_chan_id:
                    staff_chan = message.guild.get_channel(int(staff_chan_id))
                    if staff_chan:
                        await staff_chan.send(f"⚠️ {ping}**UNDERAGE ALERT:** {message.author.mention} submitted a profile with age **{user_age}**. Ticket: {message.channel.mention}")
                        
                return await message.reply("🛑 **Access Denied:** You must be 13 or older. This ticket is now locked. Staff have been alerted.")

            # Normal Save
            database.save_profile(message.author.id, message.guild.id, parsed, message.content)
            await message.reply("✅ Profile saved! Swiping starts now.")
            view = SwipeView(message.author.id, None, message.guild.id)
            await view.show_next_init(message.channel)

    @tasks.loop(minutes=10)
    async def auto_discover_loop(self): pass
    @tasks.loop(hours=12)
    async def cleanup_loop(self): pass
    @tasks.loop(hours=1)
    async def game_timer_loop(self): pass

# ---------------------------------------------------------
# COMMANDS
# ---------------------------------------------------------
@bot.tree.command(name="setup", description="Admin: Configure all Channels and Roles")
@app_commands.describe(
    tickets_category="Category for active swiping tickets",
    cafe_category="Category for private ☕ dates",
    support_category="Category where Support Tickets are created",
    pairs="Channel for pair announcements", 
    unpairs="Channel for unpair logs",
    timer="Game Timer Channel", 
    staff_logs="Staff/Help Logs (Toxicity alerts go here)",
    app_logs="Where Staff Applications are sent for review",
    staff_role="The Cupid/Staff Role (Used for pings and unpair access)",
    support_role="The role that can see Support Tickets",
    paired_role="Paired Role", 
    unpaired_role="Unpaired Role"
)
@app_commands.default_permissions(administrator=True)
async def admin_setup(
    interaction: discord.Interaction, 
    tickets_category: discord.CategoryChannel, 
    cafe_category: discord.CategoryChannel, 
    support_category: discord.CategoryChannel,
    pairs: discord.TextChannel, 
    unpairs: discord.TextChannel, 
    timer: discord.TextChannel, 
    staff_logs: discord.TextChannel, 
    app_logs: discord.TextChannel,
    staff_role: discord.Role, 
    support_role: discord.Role,
    paired_role: discord.Role, 
    unpaired_role: discord.Role
):
    config_data = {
        "match_category_id": str(tickets_category.id), 
        "cafe_category_id": str(cafe_category.id), 
        "ticket_category_id": str(support_category.id), 
        "pairs_channel_id": str(pairs.id), 
        "unpairs_channel_id": str(unpairs.id), 
        "timer_channel_id": str(timer.id), 
        "staff_channel_id": str(staff_logs.id), 
        "app_log_channel_id": str(app_logs.id), 
        "staff_role_id": str(staff_role.id), 
        "ticket_support_role_id": str(support_role.id), 
        "paired_role_id": str(paired_role.id), 
        "unpaired_role_id": str(unpaired_role.id)
    }
    
    success = database.update_config(interaction.guild.id, config_data)
    if success:
        await interaction.response.send_message("⚙️ Configured successfully! Everything is now linked.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Failed to save setup to the database.", ephemeral=True)

@bot.tree.command(name="watchlist-add", description="Staff: Watch a user and optionally ban from tickets")
@app_commands.describe(ticket_ban="Set to True to prevent them from opening tickets")
@app_commands.default_permissions(manage_messages=True)
async def add_wl(interaction: discord.Interaction, target: discord.User, note: str, ticket_ban: bool = False):
    guild_id = str(interaction.guild.id)
    if guild_id not in watchlist_db: watchlist_db[guild_id] = {}
    
    watchlist_db[guild_id][target.id] = {"note": note, "ticket_ban": ticket_ban}
    
    status = "🚫 Ticket Banned" if ticket_ban else "👀 Watched"
    await interaction.response.send_message(f"✅ {target.mention} added to watchlist. Status: **{status}**", ephemeral=True)

@bot.tree.command(name="watchlist", description="Staff: View the server watchlist")
@app_commands.default_permissions(manage_messages=True)
async def view_wl(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in watchlist_db or not watchlist_db[guild_id]: 
        return await interaction.response.send_message("The watchlist is currently empty.", ephemeral=True)
    
    msg = "**🚨 Server Watchlist:**\n"
    for tid, data in watchlist_db[guild_id].items():
        ban_status = "🚫 [BANNED]" if data.get("ticket_ban") else "👀 [WATCHED]"
        msg += f"• <@{tid}> {ban_status}: {data['note']}\n"
        
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="watchlist-remove", description="Staff: Remove a user from the watchlist")
@app_commands.default_permissions(manage_messages=True)
async def remove_wl(interaction: discord.Interaction, target: discord.User):
    guild_id = str(interaction.guild.id)
    if guild_id in watchlist_db and target.id in watchlist_db[guild_id]:
        del watchlist_db[guild_id][target.id]
        await interaction.response.send_message(f"✅ Removed {target.mention} from the watchlist.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ {target.mention} is not on the watchlist.", ephemeral=True)

@bot.tree.command(name="open-ticket", description="Start your journey")
async def open_ticket(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    # 0. Check Watchlist for Ticket Bans
    guild_id = str(interaction.guild.id)
    if guild_id in watchlist_db and interaction.user.id in watchlist_db[guild_id]:
        if watchlist_db[guild_id][interaction.user.id].get("ticket_ban"):
            return await interaction.followup.send("🛑 **Action Denied:** You have been restricted from opening matchmaking tickets by the moderation team.", ephemeral=True)
            
    active_pair = database.get_user_pairing(interaction.user.id, interaction.guild.id)
    if active_pair:
        return await interaction.followup.send(
            "🛑 **Action Denied:** You are already in an active match! "
            "You must unpair before you can start a new matchmaking journey.", 
            ephemeral=True
        )

    existing_ticket = get_ticket_channel(interaction.guild, interaction.user.id)
    if existing_ticket:
        return await interaction.followup.send(f"⚠️ You already have an open ticket: {existing_ticket.mention}", ephemeral=True)

    config = database.get_config(interaction.guild.id)
    if not config or not config.get("match_category_id"):
        return await interaction.followup.send("❌ Matchmaking is not set up on this server.", ephemeral=True)

    cat = interaction.guild.get_channel(int(config["match_category_id"]))
    if not cat:
        return await interaction.followup.send("❌ Matchmaking category not found.", ephemeral=True)

    ticket = await cat.create_text_channel(name=f"ticket-{interaction.user.name}")
    
    await ticket.set_permissions(interaction.user, read_messages=True, send_messages=True)
    await ticket.set_permissions(interaction.guild.default_role, read_messages=False)

    # Cohesive, friendly instruction embed
    intro_channel_mention = "<#123456789012345678>" 
    
    embed = discord.Embed(
        title="✨ Welcome to your Matchmaking Dashboard! ✨",
        description=(
            "We're so excited to help you find your perfect match! 💖\n\n"
            "**📜 How to get started:**\n"
            f"**1.** Head over to {intro_channel_mention} to read the rules and grab the intro template.\n"
            "**2.** Paste your filled-out intro directly into this channel.\n"
            "**3.** Our AI Cupid will process it and start showing you profiles!\n\n"
            "**💔 Want to end a match later?**\n"
            "If you ever need to close your cafe and end a match, just return to the main instructions channel and click the **💔 Request Unpair** button."
        ),
        color=discord.Color.from_rgb(180, 230, 180) # Soft, pastel sage green 🌿
    )
    embed.set_footer(text="Have fun and happy matching! 🌸")

    await ticket.send(content=f"Welcome {interaction.user.mention}!", embed=embed, view=TicketDashboardView())
    await interaction.followup.send(f"✅ Created: {ticket.mention}", ephemeral=True)

@bot.tree.command(name="my-profile", description="View your profile and matchmaking stats")
async def my_profile(interaction: discord.Interaction):
    data = database.get_profile(interaction.user.id, interaction.guild.id)
    if not data:
        return await interaction.response.send_message("❌ You don't have a profile yet! Use /open-ticket to start.", ephemeral=True)
    
    vouches = data.get('vouches', 0)
    embed = discord.Embed(title=f"👤 {data.get('name')}'s Dashboard", color=discord.Color.green())
    embed.add_field(name="Age", value=str(data.get('age')), inline=True)
    embed.add_field(name="Community Rating", value=f"✅ {vouches} Green Flags", inline=True)
    embed.add_field(name="Discord Account Age", value=f"<t:{int(interaction.user.created_at.timestamp())}:R>", inline=False)
    embed.add_field(name="Your Current Intro", value=f"```{data.get('raw_intro', 'No intro provided.')}```", inline=False)
    
    await interaction.response.send_message(embed=embed, view=MyProfileView(), ephemeral=True)

@bot.tree.command(name="vouch", description="Give a Green Flag")
async def vouch_user(interaction: discord.Interaction, match: discord.User):
    database.add_vouch(match.id, interaction.guild.id)
    await interaction.response.send_message("✅ Vouched!")

@bot.tree.command(name="pair", description="Cupid: Manually pair two users")
@app_commands.default_permissions(manage_messages=True)
async def manual_pair(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    await interaction.response.defer(ephemeral=True)
    config = database.get_config(interaction.guild.id)
    if not config: return await interaction.followup.send("❌ Server not configured.")
    database.create_pairing(user1.id, user2.id, interaction.guild.id)
    await create_cafe_channel(interaction.guild, user1, user2)
    await interaction.followup.send(f"🏹 Successfully paired {user1.name} & {user2.name}! Private cafe created.", ephemeral=True)

@bot.tree.command(name="unpair", description="Staff: Manually break a pair")
@app_commands.default_permissions(manage_messages=True)
async def manual_unpair(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    await interaction.response.defer(ephemeral=True)
    database.end_pairing(user1.id, user2.id, interaction.guild.id)
    config = database.get_config(interaction.guild.id)
    if not config: return await interaction.followup.send("❌ Server not configured.", ephemeral=True)
        
    unpairs_channel_id = config.get("unpairs_channel_id")
    warning_msg = ""
    
    if unpairs_channel_id and str(unpairs_channel_id).isdigit():
        try:
            unpairs_channel = interaction.guild.get_channel(int(unpairs_channel_id))
            if unpairs_channel: await unpairs_channel.send(f"💔 **Match Ended:** The pairing between {user1.mention} and {user2.mention} has been broken.")
            else: warning_msg = "\n⚠️ *Warning: Could not find the Unpairs channel.*"
        except Exception as e:
            print(f"Unpair Announcement Error: {e}")

    cafe_category_id = config.get("cafe_category_id")
    if cafe_category_id and str(cafe_category_id).isdigit():
        cafe_category = interaction.guild.get_channel(int(cafe_category_id))
        if cafe_category:
            for channel in cafe_category.text_channels:
                if user1 in channel.members and user2 in channel.members:
                    await channel.delete(reason="Manual unpair requested by staff.")
                    break
    await interaction.followup.send(f"💔 Successfully unpaired {user1.name} & {user2.name}.{warning_msg}", ephemeral=True)

@bot.tree.command(name="time-left", description="Check match time")
async def time_left(interaction: discord.Interaction):
    await interaction.response.send_message(f"Time remaining check...", ephemeral=True)

@bot.tree.command(name="spawn-community-panel", description="Drop support panel")
@app_commands.default_permissions(administrator=True)
async def spawn_panel(interaction: discord.Interaction):
    await interaction.channel.send("🛠️ Community Tools", view=CommunityToolsView())
    await interaction.response.send_message("✅ Spawned.", ephemeral=True)

@bot.tree.command(name="spawn-instructions", description="Admin: Drop the cozy instructions panel and entry buttons")
@app_commands.default_permissions(administrator=True)
async def spawn_instructions_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🐾 Matchmaking Guide & Rules",
        description=(
            "Welcome to the Matchmaking zone! We are so excited to help you find your perfect match. Here is exactly how everything works: 🌱\n\n"
            "**1️⃣ Open Your Dashboard**\n"
            "Click the **💖 Open Matchmaking Dashboard** button below. This creates a private channel just for you.\n\n"
            "**2️⃣ Submit Your Intro**\n"
            "Paste your filled-out intro into your private ticket. Our AI Cupid will read it and start lining up compatible profiles for you to look at!\n\n"
            "**3️⃣ Swipe & Match**\n"
            "Profiles will appear one at a time. Click **✅ Express Interest** if you like their vibe, or **❌ Pass** to keep looking. "
            "If both of you like each other, it's a Match! 🎉\n\n"
            "**4️⃣ The Private Cafe ☕**\n"
            "When you match, a private 24-hour channel (your 'Cafe') will magically appear. It's a safe space just for the two of you to chat, answer the AI icebreaker, and see if you click.\n\n"
            "**💔 Need to end a match?**\n"
            "Not feeling it? No worries at all! Just click the **💔 Request Unpair** button below, and our team will quietly and safely close the cafe for you."
        ),
        color=discord.Color.from_rgb(255, 182, 193) # Soft pastel pink 🌸
    )
    
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/8208/8208226.png") 
    embed.set_footer(text="Ready to find your match? Click a button below! ✨")

    await interaction.channel.send(embed=embed, view=MatchmakingPanelView())
    await interaction.response.send_message("✅ Cozy instructions panel spawned successfully!", ephemeral=True)

@bot.tree.command(name="investigate", description="Staff: Run a background check on a user")
@app_commands.default_permissions(manage_messages=True)
async def investigate_user(interaction: discord.Interaction, target: discord.Member):
    # Defer the response immediately since database checks might take a second
    await interaction.response.defer(ephemeral=True)
    
    # 1. Check Discord Age
    # This uses Discord's native formatting to show relative time (e.g., "2 days ago")
    created_ts = int(target.created_at.timestamp())
    account_age_str = f"<t:{created_ts}:d> (<t:{created_ts}:R>)"
    
    # 2. Check Watchlist Status
    # Scan the entire server's watchlist memory to see if ANY staff member flagged them
    watchlist_notes = []
    for key, users in watchlist_db.items():
        if key.startswith(str(interaction.guild.id)):
            if target.id in users:
                staff_id = key.split('_')[1]
                watchlist_notes.append(f"🚩 Flagged by <@{staff_id}>: {users[target.id]}")
    
    wl_status = "\n".join(watchlist_notes) if watchlist_notes else "✅ Clear (Not on any watchlist)"
    
    # 3. Check Active Matches
    pair_info = database.get_user_pairing(target.id, interaction.guild.id)
    if pair_info:
        partner_id = pair_info['user2_id'] if str(pair_info['user1_id']) == str(target.id) else pair_info['user1_id']
        match_status = f"☕ Currently paired in a Cafe with <@{partner_id}>"
    else:
        match_status = "📭 No active matches."
        
    # Build a tech-chic, highly readable Embed
    embed = discord.Embed(title=f"🔍 Investigation Report: {target.display_name}", color=discord.Color.purple())
    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(name="📅 Account Created", value=account_age_str, inline=False)
    embed.add_field(name="🛡️ Watchlist Status", value=wl_status, inline=False)
    embed.add_field(name="☕ Active Matches", value=match_status, inline=False)
    
    embed.set_footer(text=f"User ID: {target.id} | Requested by {interaction.user.name}")
    
    # Send it privately to the staff member
    await interaction.followup.send(embed=embed, ephemeral=True)
    
@bot.tree.command(name="help", description="List commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🏹 Matchmaker Bot Commands", 
        description="For more info please visit https://starry-jupiter.github.io/RedPandaBotSite/", 
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="🛠️ Admin Commands", 
        value="`/setup` - Configure all channels and roles.\n`/spawn-community-panel` - Drop the support ticket and staff app buttons in a channel.\n`/spawn-instructions` - Drop the instructions panel with entry buttons.", 
        inline=False
    )
    
    embed.add_field(
        name="💖 Player Commands", 
        value="`/open-ticket` - Start your swiping journey.\n`/my-profile` - View and edit your matchmaking intro.\n`/time-left` - Check how much time is left with your match.\n`/request-unpair` - Open a ticket to unpair from your match.", 
        inline=False
    )
    
    embed.add_field(
        name="🛡️ Staff Commands", 
        value="`/pair` - Manually pair two users.\n`/unpair` - Manually break a pairing.\n`/watchlist-add`, `/watchlist-remove`, & `/watchlist` - Keep track of suspicious users.\n`/override-flag` - Override an AI flag and restore a user's ticket.\n`/investigate` - View user history and current match.", 
        inline=False
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="request-unpair", description="Open a ticket to request unpairing from your match.")
async def request_unpair_ticket_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    pair_info = database.get_user_pairing(interaction.user.id, interaction.guild.id)
    if not pair_info: 
        return await interaction.followup.send("❌ You don't have an active match to unpair from!", ephemeral=True)
        
    partner_id = pair_info.get('user2_id') if str(pair_info.get('user1_id')) == str(interaction.user.id) else pair_info.get('user1_id')
    
    try:
        dt = datetime.fromisoformat(pair_info.get('start_time').replace('Z', '+00:00'))
        unix_time = int(dt.timestamp())
    except: 
        unix_time = int(time.time())
    
    config = database.get_config(interaction.guild.id)
    ticket_category_id = config.get("ticket_category_id") if config else None
    category = interaction.guild.get_channel(int(ticket_category_id)) if ticket_category_id else None
    
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False), 
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True), 
        interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    ticket_channel = await interaction.guild.create_text_channel(
        name=f"unpair-{interaction.user.name}", 
        category=category,
        overwrites=overwrites
    )
    
    embed = discord.Embed(
        title="💔 Unpair Request", 
        description=(
            "Hi there! Sometimes connections just don't work out, and that's perfectly okay. 🌱\n\n"
            "Please leave a brief message letting us know why you'd like to end the match. A staff member will be here shortly to close your cafe safely."
        ), 
        color=discord.Color.from_rgb(255, 182, 193)
    )
    embed.add_field(name="👤 Requesting User", value=interaction.user.mention, inline=True)
    embed.add_field(name="💞 Current Partner", value=f"<@{partner_id}>", inline=True)
    embed.add_field(name="⏱️ Paired For", value=f"<t:{unix_time}:R> (Since <t:{unix_time}:f>)", inline=False)
    
    await ticket_channel.send(content=f"Welcome {interaction.user.mention}, staff will review your request shortly.", embed=embed, view=SupportTicketView())
    await interaction.followup.send(f"✅ Your unpair request ticket has been created! Please go to {ticket_channel.mention}", ephemeral=True)

@bot.tree.command(name="override-flag", description="Staff: Override an AI flag and restore a user's ticket")
@app_commands.default_permissions(manage_messages=True)
async def override_flag(interaction: discord.Interaction, target: discord.Member):
    guild_id = str(interaction.guild.id)
    if guild_id not in watchlist_db: watchlist_db[guild_id] = {}
    
    # Remove the ticket ban and add a special 'whitelisted' flag
    watchlist_db[guild_id][target.id] = {
        "note": "Staff Whitelisted (AI Override)", 
        "ticket_ban": False, 
        "whitelisted": True
    }
    
    # Try to find their flagged ticket automatically
    channel_name = f"flagged-{target.name.lower()}"
    ticket_channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)
    
    if ticket_channel:
        # Revert the name back to a standard ticket
        await ticket_channel.edit(name=f"ticket-{target.name.lower()}")
        # Ensure they have permission to type again
        await ticket_channel.set_permissions(target, send_messages=True, read_messages=True)
        # Send a cute, friendly notification inside their ticket
        await ticket_channel.send(f"✨ **Good news!** {target.mention}, a staff member has cleared your flag. You can now send your intro again and the AI will let it through! 🍃")
        
    await interaction.response.send_message(f"✅ AI flag successfully overridden for {target.mention}. They are now whitelisted and their ticket has been restored! 🐾", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    for guild in bot.guilds:
        server_data = database.get_config(guild.id)
        if server_data and 'max_match_time' not in server_data:
            database.update_config(guild.id, {"max_match_time": 48}) 

if __name__ == "__main__":
    print("⚠️ You are running app.py directly. Use 'python run_bot.py' instead.")
```
