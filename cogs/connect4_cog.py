import discord
from discord.ext import commands

BOARD_WIDTH = 7
BOARD_HEIGHT = 7
EMPTY = "⚪"
PLAYER1 = "🔴"
PLAYER2 = "🟡"

def check_win(board, symbol):
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            if x + 3 < BOARD_WIDTH and all(board[y][x+i] == symbol for i in range(4)):
                return True
            if y + 3 < BOARD_HEIGHT and all(board[y+i][x] == symbol for i in range(4)):
                return True
            if x + 3 < BOARD_WIDTH and y + 3 < BOARD_HEIGHT and all(board[y+i][x+i] == symbol for i in range(4)):
                return True
            if x - 3 >= 0 and y + 3 < BOARD_HEIGHT and all(board[y+i][x-i] == symbol for i in range(4)):
                return True
    return False

def render_board(board):
    return "\n".join("".join(row) for row in board)

class Connect4View(discord.ui.View):
    def __init__(self, ctx, player1, player2, partida_id=None):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.player1 = player1
        self.player2 = player2
        self.current = player1
        self.symbols = {player1.id: PLAYER1, player2.id: PLAYER2}
        self.board = [[EMPTY for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.message = None
        self.finished = False
        self.partida_id = partida_id or f"{player1.id}-{player2.id}-{ctx.channel.id}"

        for i in range(BOARD_WIDTH):
            self.add_item(Connect4Button(i, self))

    async def update_message(self):
        embed = discord.Embed(
            title="Conecta 4",
            description=render_board(self.board),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Turno de: {self.current.display_name} ({self.symbols[self.current.id]})")
        try:
            last_msg = await self.message.channel.fetch_message(self.message.channel.last_message_id)
            if last_msg.id != self.message.id:
                self.message = await self.message.channel.send(embed=embed, view=self if not self.finished else None)
            else:
                await self.message.edit(embed=embed, view=self if not self.finished else None)
        except Exception:
            await self.message.edit(embed=embed, view=self if not self.finished else None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.current.id

    async def place_piece(self, column, interaction):
        for row in reversed(self.board):
            if row[column] == EMPTY:
                row[column] = self.symbols[self.current.id]
                break
        else:
            await interaction.response.send_message("Esa columna está llena.", ephemeral=True)
            return

        if check_win(self.board, self.symbols[self.current.id]):
            self.finished = True
            embed = discord.Embed(
                title="¡Victoria!",
                description=render_board(self.board),
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Ganador: {self.current.display_name} ({self.symbols[self.current.id]})")
            await interaction.response.edit_message(embed=embed, view=None)
            return

        if all(cell != EMPTY for row in self.board for cell in row):
            self.finished = True
            embed = discord.Embed(
                title="Empate",
                description=render_board(self.board),
                color=discord.Color.orange()
            )
            embed.set_footer(text="¡El tablero está lleno!")
            await interaction.response.edit_message(embed=embed, view=None)
            return

        self.current = self.player1 if self.current == self.player2 else self.player2
        await interaction.response.defer()
        await self.update_message()

class Connect4Button(discord.ui.Button):
    def __init__(self, column, parent_view):
        super().__init__(label=str(column+1), style=discord.ButtonStyle.primary)
        self.column = column
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await self.parent_view.place_piece(self.column, interaction)

class Connect4Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}

    @commands.slash_command(name="conecta4", description="Juega al Conecta 4 contra otro usuario.")
    async def conecta4(self, ctx: discord.ApplicationContext,
                      rival: discord.Option(discord.Member, "Elige a tu rival")):
        if rival.bot:
            await ctx.respond("No puedes jugar contra un bot.", ephemeral=True)
            return
        if ctx.author.id == rival.id:
            await ctx.respond("No puedes jugar contra ti mismo.", ephemeral=True)
            return

        partida_id = f"{ctx.author.id}-{rival.id}-{ctx.channel.id}"
        view = Connect4View(ctx, ctx.author, rival, partida_id=partida_id)

        embed = discord.Embed(
            title="Conecta 4",
            description=render_board(view.board),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Turno de: {ctx.author.display_name} ({PLAYER1})")
        msg = await ctx.respond(embed=embed, view=view)
        view.message = await msg.original_response()
        self.active_games[ctx.channel.id] = view

def setup(bot):
    bot.add_cog(Connect4Cog(bot))
