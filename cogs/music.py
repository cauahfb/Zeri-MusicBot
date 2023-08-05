import discord
from discord import app_commands
from discord.ext import commands

from youtube_dl import YoutubeDL


class TutorialButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.timeout=600

class music(commands.Cog):
    def __init__(self, client):
        self.client = client
    
        #all the music related stuff
        self.is_playing = False

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = ""

     #searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False

    # infinite loop checking 
    async def play_music(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            
            #try to connect to voice channel if you are not already connected

            if self.vc == "" or not self.vc.is_connected() or self.vc == None:
                self.vc = await self.music_queue[0][1].connect()
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            print(self.music_queue)
            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            self.is_playing = False
            await self.vc.disconnect()

    @app_commands.command(name="help",description="Mostre um comando de ajuda.")
    async def help(self,interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        helptxt = "`/help` - Veja esse guia!\n`/play` - Toque uma música do YouTube!\n`/queue` - Veja a fila de músicas na Playlist\n`/skip` - Pule para a próxima música da fila\n`/stop` - Finaliza a reprodução de músic"
        embedhelp = discord.Embed(
            colour = 1646116,#grey
            title=f'Comandos do {self.client.user.name}',
            description = helptxt
        )
        try:
            embedhelp.set_thumbnail(url=self.client.user.avatar.url)
        except:
            pass
        await interaction.followup.send(embed=embedhelp,view=TutorialButton())


    @app_commands.command(name="play",description="Toca uma música do YouTube.")
    @app_commands.describe(
        search = "Digite o nome da música no YouTube"
    )
    async def play(self, interaction:discord.Interaction,search:str):
        await interaction.response.defer(thinking=True)
        query = search
        
        try:
            voice_channel = interaction.user.voice.channel
        except:
        #if voice_channel is None:
            #you need to be connected so that the bot knows where to go
            embedvc = discord.Embed(
                colour= 1646116,#grey
                description = 'Que tal deixar de ser burro e se conectar em um canal antes?'
            )
            await interaction.followup.send(embed=embedvc)
            return
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                embedvc = discord.Embed(
                    colour= 12255232,#red
                    description = 'Sem chance de achar desse jeito! Aprende a escrever o nome da música pelo menos.'
                )
                await interaction.followup.send(embed=embedvc)
            else:
                embedvc = discord.Embed(
                    colour= 32768,#green
                    description = f"Musiquinhas não resolvem tudo. Mas já que você quer ouvir **{song['title']}** tudo bem!"
                )
                await interaction.followup.send(embed=embedvc,view=TutorialButton())
                self.music_queue.append([song, voice_channel])
                
                if self.is_playing == False:
                    await self.play_music()

    @app_commands.command(name="queue",description="Mostra as atuais músicas da fila.")
    async def q(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        retval = ""
        for i in range(0, len(self.music_queue)):
            retval += f'**{i+1} - **' + self.music_queue[i][0]['title'] + "\n"

        print(retval)
        if retval != "":
            embedvc = discord.Embed(
                colour= 12255232,
                description = f"{retval}"
            )
            await interaction.followup.send(embed=embedvc)
        else:
            embedvc = discord.Embed(
                colour= 1646116,
                description = 'Não existem músicas na fila no momento. Apenas CAKES NAKED CAKES'
            )
            await interaction.followup.send(embed=embedvc)
            
    @app_commands.command(name="stop",description="Finaliza a reprodução de música.")
    @app_commands.default_permissions(manage_channels=True)
    async def parar(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        if self.vc != "" and self.vc:
            self.vc.stop()
            embedvc = discord.Embed(
                colour= 1646116,#ggrey
                description = f"Viado... Acabou com a festa"
            )
        else:
            embedvc = discord.Embed(
                colour= 1646116,
                description = 'Velho eu não to tocando nada e você me mandando PARAR namoral em'
            )
            await interaction.followup.send(embed=embedvc)
            
    @parar.error #Erros para parar
    async def skip_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, commands.MissingPermissions):
            embedvc = discord.Embed(
                colour= 12255232,
                description = f"Você não vai cortar o meu barato!"
            )
            await interaction.followup.send(embed=embedvc)     
        else:
            raise error

    @app_commands.command(name="skip",description="Pula a atual música que está tocando.")
    @app_commands.default_permissions(manage_channels=True)
    async def pular(self, interaction:discord.Interaction):
        await interaction.response.defer(thinking=True)
        if self.vc != "" and self.vc:
            self.vc.stop()
            embedvc = discord.Embed(
                colour= 1646116,#ggrey
                description = f"Você pulou a música."
            )
            #try to play next in the queue if it exists
            await self.play_music()
        else:
            embedvc = discord.Embed(
                colour= 1646116,
                description = 'Caralho eu nem to tocando nada mano'
            )
            await interaction.followup.send(embed=embedvc)

    @pular.error #Erros para kick
    async def skip_error(self,interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, commands.MissingPermissions):
            embedvc = discord.Embed(
                colour= 12255232,
                description = f"Você não manda em mim! ELETROPUTA"
            )
            await interaction.followup.send(embed=embedvc)     
        else:
            raise error

async def setup(client):
    await client.add_cog(music(client))
    