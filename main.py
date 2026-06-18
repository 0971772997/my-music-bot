import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from keep_alive import keep_alive # Nhúng web server vào bot

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

YTDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} đã sẵn sàng quẩy nhạc!')

@bot.command(name='play')
async def play(ctx, url: str):
    if not ctx.author.voice:
        return await ctx.send("Bạn phải vào một kênh thoại trước!")
    
    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await voice_channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['formats'][0]['url']
            title = info.get('title', 'Nhạc')
            
        ctx.voice_client.stop()
        ctx.voice_client.play(discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS))
        await ctx.send(f"🎵 Đang phát: **{title}**")

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Đã dừng phát nhạc và rời kênh!")

# Bật Web Server
keep_alive()

# Lấy Token từ biến môi trường (an toàn tuyệt đối)
my_secret = os.environ.get('MTUxNzI0ODA0MzI5NDkxNjgwMA.GvMrTn.udwwB-S2ihULIZ_eWjaCW-GujO-WA_6ojOeDsI')
bot.run(my_secret)