import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import random
import re
import os
from server import run_server
import threading

my_secret = os.environ['DISCORD_KEY']
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Supress warnings do youtube_dl
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'proxy': 'http://43.130.58.145:13001',
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(title)s.%(ext)s',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
}

ffmpeg_options = {'options': '-vn'}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                   data=data)


@bot.command(name='play',
             help='Toca uma música do YouTube: !play <link ou nome>')
async def play(ctx, *, url):
    if not ctx.author.voice:
        await ctx.send("Você precisa estar em um canal de voz!")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.stop()
        ctx.voice_client.play(player,
                              after=lambda e: print(f'Erro: {e}')
                              if e else None)

    await ctx.send(f'🎶 Tocando agora: **{player.title}**')


@bot.command(name='skip', help='Pula a música atual')
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send('⏭️ Música pulada.')
    else:
        await ctx.send('❌ Não há música tocando para pular.')


@bot.command(name='stop', help='Para a música e sai do canal de voz')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send('⏹️ Parando música e saindo do canal de voz.')
    else:
        await ctx.send('❌ O bot não está em um canal de voz.')


@bot.command(name='iniciativa')
async def iniciativa(ctx, *, entrada):
    """
    Rola iniciativa para personagens no formato: Nomex2+3 (quantidade de dados + bônus)
    Ex: Guerreirox1+2 Magox2+4 Ladinox1+3
    """
    padrao = r'(\w+)X(\d+)\+(-?\d+)'  # NomexQtdDados+Bônus
    personagens = re.findall(padrao, entrada)

    if not personagens:
        await ctx.send("Formato inválido! Use: NomeX2+3 NomeX1+1 etc.")
        return

    resultados = []
    for nome, qtd_dados, bonus in personagens:
        qtd_dados = int(qtd_dados)
        bonus = int(bonus)

        dados = [random.randint(1, 20) for _ in range(qtd_dados)]
        melhor = max(dados)
        total = melhor + bonus

        resultados.append((nome, qtd_dados, dados, bonus, total))

    # Ordenar do maior para o menor total
    resultados.sort(key=lambda x: x[4], reverse=True)

    # Criar resposta formatada
    resposta = "**🎲 Ordem de Iniciativa:**\n"
    for i, (nome, qtd_dados, dados, bonus, total) in enumerate(resultados, 1):
        dados_str = " / ".join(str(d) for d in dados)
        resposta += f"{i}. **{nome}**: {qtd_dados}d20({dados_str}) + {bonus} = {total}\n"

    await ctx.send(resposta)

@bot.command()
async def roll(ctx, *, arg):
    # Regex para algo tipo: "3d20 +5", "2d6-1", "4d8", etc.
    match = re.match(r"(\d+)d(\d+)(\s*([+-])\s*(\d+))?", arg.replace(" ", ""))
    if not match:
        await ctx.send("Formato inválido! Use: `!roll XdY +Z` (ex: `!roll 3d20 +5`)")
        return

    num_dice = int(match.group(1))
    dice_size = int(match.group(2))
    modifier_sign = match.group(4)
    modifier_value = int(match.group(5)) if match.group(5) else 0
    modifier = modifier_value if modifier_sign == '+' else -modifier_value

    rolls = [random.randint(1, dice_size) for _ in range(num_dice)]
    highest = max(rolls)
    total = highest + modifier

    response = (
        f"🎲 Rolagens: {rolls}\n"
        f"🔝 Maior dado: {highest}\n"
        f"➕ Modificador: {'+' if modifier >= 0 else ''}{modifier}\n"
        f"✅ Resultado final: {total}"
    )
    await ctx.send(response)


@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')


flask_thread = threading.Thread(target=run_server)
flask_thread.start()

bot.run(my_secret)
