import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from flask import Flask
from threading import Thread

# ==================== ĐOẠN 1: CẤU HÌNH WEB SERVER KEEP_ALIVE ====================
app = Flask('')

@app.route('/')
def home():
    return "Web Server của Bot đang hoạt động 24/7!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Bật Web Server lên trước
keep_alive()

# ==================== ĐOẠN 2: CẤU HÌNH DISCORD BOT & YOUTUBE ====================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Danh sách hàng chờ chứa các bài hát (Mỗi bài gồm title và url)
music_queue = []

YTDL_OPTIONS = {
    'format': 'bestaudio/best', 
    'noplaylist': True, 
    'quiet': True,
    'default_search': 'ytsearch',
    # Khai báo file cookie để bot tự động đăng nhập né bộ lọc của YouTube
    'cookiefile': 'youtube_cookies.txt' 
}
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} đã sẵn sàng quẩy nhạc!')

# Hàm xử lý tự động phát bài tiếp theo khi bài cũ kết thúc
def play_next(ctx):
    if len(music_queue) > 0:
        next_song = music_queue.pop(0)
        url2 = next_song['url']
        title = next_song['title']
        
        ctx.voice_client.play(discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
        bot.loop.create_task(ctx.send(f"🎵 Đang phát tiếp: **{title}**"))
    else:
        bot.loop.create_task(ctx.send("📭 Hàng chờ đã hết bài rồi!"))

# ==================== ĐOẠN 3: CÁC CÂU LỆNH ĐIỀU KHIỂN NHẠC ====================

@bot.command(name='join')
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("❌ Bạn phải vào một kênh thoại trước!")
    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await voice_channel.connect()
        await ctx.send(f"👋 Đã kết nối vào kênh: **{voice_channel.name}**")

@bot.command(name='play')
async def play(ctx, *, search: str):
    # 1. Kiểm tra người dùng đã vào kênh thoại chưa
    if not ctx.author.voice:
        return await ctx.send("❌ Bạn phải vào một kênh thoại trước!")
    
    # 2. Kết nối vào kênh nếu chưa có trong phòng
    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await voice_channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            try:
                # Tìm kiếm hoặc trích xuất thông tin video
                info = ydl.extract_info(search, download=False)
                # Nếu là kết quả tìm kiếm bằng từ khóa, lấy bài đầu tiên
                if 'entries' in info:
                    info = info['entries'][0]
                
                url2 = info.get('url') or info['formats'][0]['url']
                title = info.get('title', 'Nhạc')
            except Exception as e:
                # Hiện lỗi chi tiết ra Discord để chúng ta dễ dàng "bắt bài" YouTube
                error_msg = str(e).split('\n')[0] # Lấy dòng lỗi đầu tiên cho gọn
                return await ctx.send(f"❌ Lỗi trích xuất nhạc: `{error_msg}`")

        # 3. Xử lý đưa vào hàng chờ phát nhạc
        song = {'url': url2, 'title': title}
        
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            music_queue.append(song)
            await ctx.send(f"⏳ Đã thêm vào hàng chờ: **{title}**")
        else:
            ctx.voice_client.play(discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
            await ctx.send(f"🎵 Đang phát: **{title}**")

@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Đã tạm dừng nhạc!")
    else:
        await ctx.send("❌ Hiện tại bot không phát nhạc.")

@bot.command(name='resume')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Tiếp tục phát nhạc!")
    else:
        await ctx.send("❌ Nhạc không ở trạng thái tạm dừng.")

@bot.command(name='skip')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop() # Lệnh dừng này sẽ tự kích hoạt hàm play_next ở trên
        await ctx.send("⏭️ Đã bỏ qua bài hát hiện tại!")
    else:
        await ctx.send("❌ Không có bài hát nào đang phát để bỏ qua.")

@bot.command(name='stop')
async def stop(ctx):
    global music_queue
    if ctx.voice_client:
        music_queue.clear() # Xóa sạch hàng chờ
        ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        await ctx.send("🛑 Đã dừng phát nhạc, xóa sạch hàng chờ và rời kênh thoại!")

@bot.command(name='leave', aliases=['disconnect'])
async def leave(ctx):
    global music_queue
    if ctx.voice_client:
        music_queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Đã rời khỏi kênh thoại!")

@bot.command(name='queue')
async def queue(ctx):
    if len(music_queue) == 0:
        return await ctx.send("📭 Hàng chờ hiện đang trống!")
    
    list_song = "🎶 **Danh sách hàng chờ tiếp theo:**\n"
    for i, song in enumerate(music_queue, start=1):
        list_song += f"{i}. **{song['title']}**\n"
    await ctx.send(list_song)

# ==================== ĐOẠN 4: KHỞI CHẠY BOT VỚI TOKEN ====================
my_secret = os.environ.get('DISCORD_TOKEN')
bot.run(my_secret)
