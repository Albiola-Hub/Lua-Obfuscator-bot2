import discord
from discord import app_commands
from discord.ext import commands
import random
import os
from dotenv import load_dotenv

# ═══════════════════════════════════════
#  LOAD ENVIRONMENT VARIABLES
# ═══════════════════════════════════════

load_dotenv()

# ═══════════════════════════════════════
#  BOT SETUP
# ═══════════════════════════════════════

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ═══════════════════════════════════════
#  OBFUSCATION ENGINE
# ═══════════════════════════════════════

LUA_GLOBALS = set([
    "print","warn","error","assert","pcall","xpcall","ipairs","pairs","next",
    "select","type","tostring","tonumber","unpack","require","rawget","rawset",
    "rawequal","setmetatable","getmetatable","load","loadstring","game","workspace",
    "script","wait","spawn","delay","tick","time","typeof","_G","shared","task",
    "math","string","table","coroutine","bit32","os","Instance","Vector3","Vector2",
    "CFrame","Color3","BrickColor","Enum","UDim","UDim2","TweenInfo","Players",
    "RunService","UserInputService","TweenService","ReplicatedStorage","Lighting",
    "StarterGui","CoreGui","HttpService","SoundService","LocalPlayer","Character",
    "Humanoid","WalkSpeed","JumpPower","HumanoidRootPart","PlayerGui",
    "FindFirstChild","WaitForChild","GetService","Clone","Destroy","Parent","Name",
    "ClassName","IsA","GetChildren","GetDescendants","Position","Size",
    "Transparency","Color","Text","Font","Visible","Enabled","Value",
    "Heartbeat","RenderStepped","Stepped","Changed","Connect","Fire","Wait",
    "true","false","nil",
])

LUA_KEYWORDS = set([
    "and","break","do","else","elseif","end","false","for","function","goto",
    "if","in","local","nil","not","or","repeat","return","then","true","until","while"
])

CONFUSING = ["I","l","i","L","O","o","Q","0"]

def gen_var(index, level):
    if level == 1:
        return f"_{index:x}"
    length = 6 if level == 2 else 10
    name = "_"
    for i in range(length):
        ci = (index * 7 + i * 13 + index // 3) % len(CONFUSING)
        name += CONFUSING[ci]
    return name + str(index)

def remove_comments(code):
    import re
    code = re.sub(r'--\[\[.*?\]\]', '', code, flags=re.DOTALL)
    code = re.sub(r'--[^\n]*', '', code)
    return code

def xor_encode(bytes_list, key):
    return [b ^ ((key + i * 3) % 256) for i, b in enumerate(bytes_list)]

def str_to_bytes(s):
    return [ord(c) for c in s]

def generate_junk(level, count):
    parts = []
    for i in range(count):
        v = gen_var(5000 + i, level)
        n = random.randint(0, 9999)
        templates = [
            f"local {v}={n}",
            f"local {v}=type(nil)",
            f"local {v}={{}}",
            f"local {v}=(function()return {n} end)()",
        ]
        parts.append(templates[i % len(templates)])
    return " ".join(parts)

XOR_FUNC = """local function _xor(a,b)
if bit32 then return bit32.bxor(a,b) end
local r,p=0,1
for _=1,8 do
local x,y=a%2,b%2
if x~=y then r=r+p end
a,b=math.floor(a/2),math.floor(b/2)
p=p*2
end
return r
end"""

def obfuscate_l1(code):
    r = remove_comments(code)
    r = "\n".join(line.strip() for line in r.splitlines() if line.strip())
    return f"-- Protected by Sttar Albiola\n{r}"

def obfuscate_l2(code):
    r = remove_comments(code)
    r = " ".join(r.split()).strip()

    key = random.randint(50, 250)
    encoded = xor_encode(str_to_bytes(r), key)

    dv = gen_var(100, 2)
    kv = gen_var(101, 2)
    rv = gen_var(103, 2)
    iv = gen_var(104, 2)
    fv = gen_var(105, 2)
    junk = generate_junk(2, 3)
    data = ",".join(map(str, encoded))

    return (
        f"-- Protected by Sttar Albiola (L2)\n"
        f"{junk}\n"
        f"{XOR_FUNC}\n"
        f"local {dv}={{{data}}}\n"
        f"local {kv}={key}\n"
        f"local {rv}=''\n"
        f"for {iv}=1,#{dv} do\n"
        f"{rv}={rv}..string.char(_xor({dv}[{iv}],({kv}+({iv}-1)*3)%256))\n"
        f"end\n"
        f"local {fv}=loadstring({rv})\n"
        f"if {fv} then {fv}() end"
    )

def obfuscate_l3(code):
    r = remove_comments(code)
    r = " ".join(r.split()).strip()

    k1 = random.randint(30, 230)
    k2 = random.randint(30, 230)
    k3 = random.randint(30, 230)

    b = str_to_bytes(r)
    enc = xor_encode(xor_encode(xor_encode(b, k1), k2), k3)

    def v(n): return gen_var(300 + n, 3)

    sizes = [37, 41, 29, 47, 31, 43, 53]
    chunks, idx, ci = [], 0, 0
    while idx < len(enc):
        s = sizes[ci % len(sizes)]
        chunks.append(enc[idx:idx+s])
        idx += s
        ci += 1

    junk_lines = "\n".join(
        f"local {v(100+i)}={random.randint(0,9999)}" for i in range(5)
    )
    chunk_lines = "\n".join(
        f"local {v(500+i)}={{{','.join(map(str,chunk))}}}"
        for i, chunk in enumerate(chunks)
    )
    assemble = "\n".join(
        f"for _j=1,#{v(500+i)} do {v(1)}[#{v(1)}+1]={v(500+i)}[_j] end"
        for i in range(len(chunks))
    )

    return (
        f"-- Protected by Sttar Albiola (L3)\n"
        f"-- Anti-decompile protection enabled\n"
        f"do\n"
        f"{junk_lines}\n"
        f"{XOR_FUNC}\n"
        f"{chunk_lines}\n"
        f"local {v(1)}={{}}\n"
        f"{assemble}\n"
        f"local {v(2)},{v(3)},{v(4)}={k3},{k2},{k1}\n"
        f"local {v(5)}={{}}\n"
        f"for _i=1,#{v(1)} do\n"
        f"{v(5)}[_i]=_xor({v(1)}[_i],({v(2)}+(_i-1)*3)%256)\n"
        f"end\n"
        f"local {v(7)}={{}}\n"
        f"for _i=1,#{v(5)} do\n"
        f"{v(7)}[_i]=_xor({v(5)}[_i],({v(3)}+(_i-1)*3)%256)\n"
        f"end\n"
        f"local {v(8)}=''\n"
        f"for _i=1,#{v(7)} do\n"
        f"{v(8)}={v(8)}..string.char(_xor({v(7)}[_i],({v(4)}+(_i-1)*3)%256))\n"
        f"end\n"
        f"local _fn=loadstring({v(8)})\n"
        f"if type(_fn)=='function' then pcall(_fn) end\n"
        f"end"
    )

def obfuscate(code, level):
    code = code.strip()
    if not code:
        return "-- Empty script"
    if level == 1:
        return obfuscate_l1(code)
    elif level == 2:
        return obfuscate_l2(code)
    elif level == 3:
        return obfuscate_l3(code)
    return obfuscate_l2(code)

# ═══════════════════════════════════════
#  SLASH COMMANDS
# ═══════════════════════════════════════

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user} | Slash commands synced!")

@bot.tree.command(name="obfuscate", description="I-obfuscate ang iyong Lua script")
@app_commands.describe(
    script="Ang Lua script na i-o-obfuscate",
    level="Protection level (1 = Basic, 2 = Strong, 3 = Maximum)"
)
@app_commands.choices(level=[
    app_commands.Choice(name="Level 1 — Basic (variable renaming)", value=1),
    app_commands.Choice(name="Level 2 — Strong (XOR encoding + junk code)", value=2),
    app_commands.Choice(name="Level 3 — Maximum (triple XOR + anti-decompile)", value=3),
])
async def obfuscate_cmd(interaction: discord.Interaction, script: str, level: int = 2):
    await interaction.response.defer(thinking=True)

    try:
        result = obfuscate(script, level)
    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(
                title="❌ Obfuscation Failed",
                description=f"```{str(e)}```",
                color=0xFF4444
            )
        )
        return

    level_names = {1: "Basic", 2: "Strong", 3: "Maximum"}
    level_colors = {1: 0x88FF44, 2: 0x44AAFF, 3: 0xFF44AA}

    # If result is short enough, send as code block
    if len(result) <= 1900:
        embed = discord.Embed(
            title=f"🛡️ Script Protected — Level {level} ({level_names[level]})",
            color=level_colors[level]
        )
        embed.add_field(
            name="Obfuscated Script",
            value=f"```lua\n{result[:1800]}\n```",
            inline=False
        )
        embed.set_footer(text="Sttar Obfuscator • by Sttar Albiola")
        await interaction.followup.send(embed=embed)
    else:
        # Send as .lua file attachment
        import io
        file_bytes = result.encode("utf-8")
        file = discord.File(fp=io.BytesIO(file_bytes), filename="obfuscated.lua")

        embed = discord.Embed(
            title=f"🛡️ Script Protected — Level {level} ({level_names[level]})",
            description="Malaki ang script kaya naka-attach bilang file.",
            color=level_colors[level]
        )
        embed.set_footer(text="Sttar Obfuscator • by Sttar Albiola")
        await interaction.followup.send(embed=embed, file=file)


@bot.tree.command(name="help", description="Makita ang lahat ng commands ng Sttar Obfuscator")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🛡️ Sttar Obfuscator — Help",
        description="Lua script obfuscator bot ni **Sttar Albiola**",
        color=0xC8FF00
    )
    embed.add_field(
        name="</obfuscate:0>",
        value=(
            "I-obfuscate ang iyong Lua script.\n"
            "> **script** — ang Lua code mo\n"
            "> **level** — protection level (1/2/3)\n\n"
            "**Levels:**\n"
            "🟢 `1 — Basic` — Variable renaming, minify\n"
            "🔵 `2 — Strong` — XOR encoding + junk code *(default)*\n"
            "🔴 `3 — Maximum` — Triple XOR + anti-decompile"
        ),
        inline=False
    )
    embed.add_field(
        name="</help:0>",
        value="Ipakita ang help message na ito.",
        inline=False
    )
    embed.add_field(
        name="🌐 Website",
        value="[v0-sttar-obfuscator.vercel.app](https://v0-sttar-obfuscator.vercel.app)",
        inline=False
    )
    embed.set_footer(text="Sttar Obfuscator • by Sttar Albiola")
    await interaction.followup.send(embed=embed)

# ═══════════════════════════════════════
#  RUN BOT
# ═══════════════════════════════════════

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ ERROR: Walang DISCORD_TOKEN sa environment!")
    print("Kailangan mo i-set ang DISCORD_TOKEN sa .env file o sa Render environment variables")
    exit()

bot.run(TOKEN)
