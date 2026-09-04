import sqlite3
import discord
from discord.ext import commands
from discord import app_commands, Interaction, ButtonStyle
from discord.ui import Button, View, Modal, TextInput

# ==========================================
# SETUP DATABASE SQLITE
# ==========================================
def init_db():
conn = sqlite3.connect("polizia.db")
cursor = conn.cursor()

# Tabella cittadini
cursor.execute("""
CREATE TABLE IF NOT EXISTS cittadini (
user_id INTEGER PRIMARY KEY,
cittadinanza BOOLEAN DEFAULT 1,
ville INTEGER DEFAULT 0,
patente BOOLEAN DEFAULT 0,
porto_darmi BOOLEAN DEFAULT 0,
stato_fermo BOOLEAN DEFAULT 0,
conto_bancario INTEGER DEFAULT 0,
precedenti TEXT DEFAULT ''
)
""")

# Tabella report ore servizio FDO
cursor.execute("""
CREATE TABLE IF NOT EXISTS ore_servizio (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
username TEXT,
fazione TEXT,
sparatorie INTEGER,
arresti INTEGER,
multe INTEGER,
blitz INTEGER,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

init_db()

# Helper per accedere al DB
def get_cittadino(user_id):
conn = sqlite3.connect("polizia.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM cittadini WHERE user_id = ?", (user_id,))
row = cursor.fetchone()
if not row:
cursor.execute("INSERT INTO cittadini (user_id) VALUES (?)", (user_id,))
conn.commit()
cursor.execute("SELECT * FROM cittadini WHERE user_id = ?", (user_id,))
row = cursor.fetchone()
conn.close()
return row

def update_cittadino(user_id, column, value):
conn = sqlite3.connect("polizia.db")
cursor = conn.cursor()
cursor.execute(f"UPDATE cittadini SET {column} = ? WHERE user_id = ?", (value, user_id))
conn.commit()
conn.close()

def add_precedente(user_id, nota):
row = get_cittadino(user_id)
vecchi_precedenti = row[7] if row[7] else ""
nuovi_precedenti = vecchi_precedenti + f"• {nota}\n"
update_cittadino(user_id, "precedenti", nuovi_precedenti)

# ==========================================
# CONFIGURAZIONE BOT
# ==========================================
PREFIX = "spada comands "
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
print(f"Bot connesso come {bot.user.name}")
try:
synced = await bot.tree.sync()
print(f"Sincronizzati {len(synced)} comandi slash.")
except Exception as e:
print(f"Errore nella sincronizzazione: {e}")

# ==========================================
# INTERFACCE / MODALS / VIEWS FDO
# ==========================================
class ServizioModal(Modal, title="Report Fine Servizio FDO"):
fazione = TextInput(label="Di che fazione fai parte?", placeholder="es. Polizia di Stato, Carabinieri...")
sparatorie = TextInput(label="Quante sparatorie hai fatto?", default="0")
arresti = TextInput(label="Quanti arresti hai fatto?", default="0")
multe = TextInput(label="Quante multe hai fatto?", default="0")
blitz = TextInput(label="Quanti blitz hai fatto?", default="0")

async def on_submit(self, interaction: Interaction):
conn = sqlite3.connect("polizia.db")
cursor = conn.cursor()
cursor.execute("""
INSERT INTO ore_servizio (user_id, username, fazione, sparatorie, arresti, multe, blitz)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
interaction.user.id,
str(interaction.user),
self.fazione.value,
int(self.sparatorie.value if self.sparatorie.value.isdigit() else 0),
int(self.arresti.value if self.arresti.value.isdigit() else 0),
int(self.multe.value if self.multe.value.isdigit() else 0),
int(self.blitz.value if self.blitz.value.isdigit() else 0)
))
conn.commit()
conn.close()

embed = discord.Embed(
title="🔴 Uscita dal Servizio",
description=f"**Agente:** {interaction.user.mention}\n**Fazione:** {self.fazione.value}\nTurno registrato con successo nel database riservato ai Comandanti.",
color=discord.Color.red()
)
await interaction.response.send_message(embed=embed)

class FDOView(View):
def __init__(self):
super().__init__(timeout=None)

@discord.ui.button(label="Entra in Servizio", style=ButtonStyle.success, custom_id="fdo_entra")
async def entra_servizio(self, interaction: Interaction, button: Button):
embed = discord.Embed(
title="🟢 Ingresso in Servizio",
description=f"L'agente {interaction.user.mention} è ora **IN SERVIZIO**.",
color=discord.Color.green()
)
await interaction.response.send_message(embed=embed)

@discord.ui.button(label="Esci dal Servizio", style=ButtonStyle.danger, custom_id="fdo_esce")
async def esci_servizio(self, interaction: Interaction, button: Button):
await interaction.response.send_modal(ServizioModal())

# ==========================================
# INTERFACCE BANCA E IMMOBILIARE
# ==========================================
class BancaView(View):
def __init__(self):
super().__init__(timeout=None)

@discord.ui.button(label="Apri Conto", style=ButtonStyle.primary)
async def apri_conto(self, interaction: Interaction, button: Button):
row = get_cittadino(interaction.user.id)
if row[6] > 0:
await interaction.response.send_message("Hai già un conto bancario attivo!", ephemeral=True)
else:
update_cittadino(interaction.user.id, "conto_bancario", 1000) # Saldo iniziale 1000
await interaction.response.send_message("Conto bancario aperto con successo! Saldo iniziale: 1.000€.", ephemeral=True)

@discord.ui.button(label="Bonifico", style=ButtonStyle.secondary)
async def bonifico(self, interaction: Interaction, button: Button):
await interaction.response.send_message("Per effettuare un bonifico usa il comando: `spada comands bonifico @utente importo`", ephemeral=True)

@discord.ui.button(label="Richiedi Prestito", style=ButtonStyle.secondary)
async def prestito(self, interaction: Interaction, button: Button):
await interaction.response.send_message("Prestito di 5.000€ erogato con successo!", ephemeral=True)

class CasaView(View):
def __init__(self):
super().__init__(timeout=None)

@discord.ui.button(label="Compra Casa", style=ButtonStyle.success)
async def compra_casa(self, interaction: Interaction, button: Button):
row = get_cittadino(interaction.user.id)
nuovo_totale = row[2] + 1
update_cittadino(interaction.user.id, "ville", nuovo_totale)
await interaction.response.send_message(f"Hai acquistato una nuova villa! Ora ne possiedi: **{nuovo_totale}**", ephemeral=True)

@discord.ui.button(label="Vendi Casa", style=ButtonStyle.danger)
async def vendi_casa(self, interaction: Interaction, button: Button):
row = get_cittadino(interaction.user.id)
if row[2] <= 0:
await interaction.response.send_message("Non possiedi alcuna villa da vendere!", ephemeral=True)
else:
nuovo_totale = row[2] - 1
update_cittadino(interaction.user.id, "ville", nuovo_totale)
await interaction.response.send_message(f"Hai venduto una villa. Ora ne possiedi: **{nuovo_totale}**", ephemeral=True)

# ==========================================
# COMANDI CON PREFISSO "spada comands "
# ==========================================

@bot.command(name="database")
async def database(ctx, utente: discord.Member = None):
target = utente or ctx.author
row = get_cittadino(target.id)

cittadinanza = "✅ Presente" if row[1] else "❌ Assente"
ville = row[2]
patente = "✅ Valida" if row[3] else "❌ Non posseduta"
porto_darmi = "✅ Valido" if row[4] else "❌ Non posseduto"
stato_fermo = "🔴 IN STATO DI FERMO" if row[5] else "🟢 Nessun fermo"
conto = f"✅ Attivo ({row[6]}€)" if row[6] > 0 else "❌ Nessun conto"
precedenti = row[7] if row[7] else "Nessun precedente registrato."

embed = discord.Embed(title=f"🚔 Database Polizia - {target.display_name}", color=discord.Color.blue())
embed.add_field(name="Cittadinanza", value=cittadinanza, inline=True)
embed.add_field(name="Ville di proprietà", value=str(ville), inline=True)
embed.add_field(name="Conto Bancario", value=conto, inline=True)
embed.add_field(name="Patente", value=patente, inline=True)
embed.add_field(name="Porto d'Armi", value=porto_darmi, inline=True)
embed.add_field(name="Stato di Fermo", value=stato_fermo, inline=True)
embed.add_field(name="Precedenti Penali / Sanzioni", value=precedenti, inline=False)
embed.set_thumbnail(url=target.display_avatar.url)

await ctx.send(embed=embed)

@bot.command(name="fermo")
async def fermo(ctx, utente: discord.Member, stato: bool):
valore = 1 if stato else 0
update_cittadino(utente.id, "stato_fermo", valore)
txt = "messo in **Stato di Fermo**" if stato else "rimosso dallo **Stato di Fermo**"
await ctx.send(f"L'utente {utente.mention} è stato {txt}.")

@bot.command(name="multa")
async def multa(ctx, utente: discord.Member, importo: int, *, motivo: str):
nota = f"MULTA ({importo}€): {motivo}"
add_precedente(utente.id, nota)

embed = discord.Embed(title="📜 Sanzione Amministrativa (Multa)", color=discord.Color.orange())
embed.add_field(name="Sanzionato", value=utente.mention, inline=True)
embed.add_field(name="Importo", value=f"{importo}€", inline=True)
embed.add_field(name="Motivo", value=motivo, inline=False)
embed.set_footer(text="Questa sanzione è stata inserita nei precedenti penali.")

await ctx.send(embed=embed)

@bot.command(name="arresta")
async def arresta(ctx, utente: discord.Member, tempo_minuti: int, *, motivo: str):
nota = f"ARRESTO ({tempo_minuti} min): {motivo}"
add_precedente(utente.id, nota)
update_cittadino(utente.id, "stato_fermo", 1) # Mette automaticamente anche lo stato di fermo

embed = discord.Embed(title="⚖️ Verbale di Arresto", color=discord.Color.dark_red())
embed.add_field(name="Arrestato", value=utente.mention, inline=True)
embed.add_field(name="Tempo Detenzione", value=f"{tempo_minuti} minuti", inline=True)
embed.add_field(name="Motivo", value=motivo, inline=False)
embed.set_footer(text="L'arresto è stato registrato nel Database e l'utente è in stato di fermo.")

await ctx.send(embed=embed)

@bot.command(name="banca")
async def banca(ctx):
embed = discord.Embed(
title="🏦 Banca Centrale - Servizi Finanziari",
description="Usa i pulsanti sottostanti per gestire il tuo conto corrente, richiedere prestiti o fare bonifici.",
color=discord.Color.gold()
)
await ctx.send(embed=embed, view=BancaView())

@bot.command(name="immobiliare")
async def immobiliare(ctx):
embed = discord.Embed(
title="🏡 Agenzia Immobiliare",
description="Gestisci le tue proprietà residenti. Acquista o vendi le tue ville lussuose.",
color=discord.Color.green()
)
await ctx.send(embed=embed, view=CasaView())

@bot.command(name="fdo")
async def fdo(ctx):
embed = discord.Embed(
title="🛡️ Timbratura Turno Forza dell'Ordine",
description="Clicca su **Entra in Servizio** quando inizi il turno.\nClicca su **Esci dal Servizio** a fine turno per compilare il report d'attività.",
color=discord.Color.dark_blue()
)
await ctx.send(embed=embed, view=FDOView())

# ==========================================
# COMANDO RISERVATO COMANDANTI
# ==========================================
@bot.hybrid_command(name="guarda_ore_servizio", description="Comando riservato ai Comandanti per controllare i turni.")
@commands.has_permissions(administrator=True) # Modifica i permessi se necessario
async def guarda_ore_servizio(ctx, utente: discord.Member = None):
conn = sqlite3.connect("polizia.db")
cursor = conn.cursor()

if utente:
cursor.execute("SELECT * FROM ore_servizio WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (utente.id,))
else:
cursor.execute("SELECT * FROM ore_servizio ORDER BY timestamp DESC LIMIT 10")

rows = cursor.fetchall()
conn.close()

embed = discord.Embed(title="📊 Registro Turni FDO (Riservato Comandanti)", color=discord.Color.purple())

if not rows:
embed.description = "Nessun report turno trovato nel sistema."
else:
for r in rows:
embed.add_field(
name=f"Turno di {r[2]} ({r[8]})",
value=f"**Fazione:** {r[3]}\n🔫 Sparatorie: {r[4]} | ⚖️ Arresti: {r[5]}\n📜 Multe: {r[6]} | 💥 Blitz: {r[7]}",
inline=False
)

await ctx.send(embed=embed)

# ==========================================
# AVVIO BOT
# ==========================================
# Inserisci qui il TOKEN del tuo bot Discord
bot.run("MTU0NTUxNzAyNTA4OTAzNjM1OA.GcXMjj.Zm_i0DoxMRqPhR-9UfbqP7-AeHCdIzWq3atCW0")
