import discord
from discord.ext import commands, tasks
import random
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
import os
import asyncio
import re
import json

# ✅ 데이터 파일 경로 및 초기값 세팅 (import 바로 아래)
DATA_FILE = "bot_data.json"
bot_data = {
    "target_user_ids": set(),
    "target_role_names": set(),
    "homework_records": {},
    "penalty_records": {}
}

# ✅ 저장 함수
def save_data():
    data_copy = {
        "target_user_ids": list(bot_data["target_user_ids"]),
        "target_role_names": list(bot_data["target_role_names"]),
        "homework_records": bot_data["homework_records"],
        "penalty_records": bot_data["penalty_records"]
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data_copy, f, indent=4)

# ✅ 불러오기 함수
def load_data():
    global bot_data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            bot_data["target_user_ids"] = set(data.get("target_user_ids", []))
            bot_data["target_role_names"] = set(data.get("target_role_names", []))
            bot_data["homework_records"] = data.get("homework_records", {})
            bot_data["penalty_records"] = data.get("penalty_records", {})
    else:
        save_data()

# ✅ 프로그램 시작시 로드
load_data()

'''-------지랄함수 시작-------'''

# .env 파일에서 토큰 불러오기
load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.members = True
intents.dm_messages = True
intents.message_content = True
#intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 메모리 기반 관리 (서버 확장 구조)
target_user_ids = set()
target_role_names = set()

# 숙제 기록 및 벌칙 인증 상태
homework_records = {}
penalty_records = {}

# 지랄 메시지 리스트
JIRAL_MESSAGES = [
    "머리박고 숙제 시작해라 😇",
    "혜미야 또 미뤘지? 지금 안 하면 진짜 머리박아야해.",
    "숙제는 안 하고 게임만 하냐…",
    "숙제 안 하면 오늘도 디엠 간다.",
    "혜미, 넌 이제 진짜로 숙제해야 돼. 농담 아님.",
    "지금도 안 하면 수업 당일에 진짜 사망각이야.",
    "헤이~ 숙제 안 하면 귀여운 벌칙이 기다리고 있어~ 🐾",
    "애기야... 오늘도 숙제 안 했구나? 😇 이제 벌칙 각이다!",
    "숙제 안 하고 또 게임? 유튜브??? 내가 정말 너를... 👀",
    "오늘도 숙제는 없다! 벌칙 시간~ 🐣",
    "귀여운 벌칙이 기다리는데... 숙제 시작 안 해? 😢",
    "숙제 안 하면 징그러운 벌칙이 기다린다~ 🐱💦"
]

# 벌칙 예고 메시지
PENALTY_MESSAGES = [
    "벌칙 예고!를 안 하면 내일은 스쿼트 200회! 😈",
    "벌칙 각! 내일 간식 못 먹기 게임! 🍪",
    "오늘 숙제 안 하면 내일 내가 널 30분 동안 어드바이스로 괴롭힌다 👹",
]

@bot.event
async def on_ready():
    print(f"✅ 지랄봇 로그인 완료: {bot.user}")
    scheduled_jiral.start()

# 권한 체크 함수
def is_authorized(ctx):
    user = ctx.author
    if user.id in bot_data["target_user_ids"]:
        return True
    for role in user.roles:
        if role.name in bot_data["target_role_names"]:
            return True
    return False

# ✅ 관리자 전용: 유저 추가
@bot.command()
@commands.has_permissions(administrator=True)
async def 대상추가(ctx, member: discord.Member):
    bot_data["target_user_ids"].add(member.id)
    save_data()
    await ctx.send(f"{member.display_name} 님을 대상자로 추가했어요.")

# ✅ 관리자 전용: 유저 제거
@bot.command()
@commands.has_permissions(administrator=True)
async def 대상삭제(ctx, member: discord.Member):
    if member.id in bot_data["target_user_ids"]:
        bot_data["target_user_ids"].remove(member.id)
        save_data()
        await ctx.send(f"{member.display_name} 님을 대상자에서 제거했어요.")
    else:
        await ctx.send(f"{member.display_name} 님은 현재 대상자가 아닙니다.")

# ✅ 관리자 전용: 역할 추가
@bot.command()
@commands.has_permissions(administrator=True)
async def 역할추가(ctx, *, role_name):
    role_name = role_name.strip()
    bot_data["target_role_names"].add(role_name)
    save_data()
    await ctx.send(f"'{role_name}' 역할을 대상 역할로 추가했어요.")

# ✅ 관리자 전용: 역할 제거
@bot.command()
@commands.has_permissions(administrator=True)
async def 역할제거(ctx, *, role_name):
    if role_name in bot_data["target_role_names"]:
        bot_data["target_role_names"].remove(role_name)
        save_data()
        await ctx.send(f"'{role_name}' 역할을 대상에서 제거했어요.")
    else:
        await ctx.send(f"'{role_name}' 역할은 등록되어 있지 않아요.")

# ✅ 관리자 전용: 현재 대상 목록 확인
@bot.command()
@commands.has_permissions(administrator=True)
async def 목록확인(ctx):
    user_list = ', '.join(str(uid) for uid in bot_data["target_user_ids"]) or '없음'
    role_list = ', '.join(bot_data["target_role_names"]) or '없음'
    await ctx.send(f"유저 대상자: {user_list}\n역할 대상자: {role_list}")
  
# 랜덤 지랄 디엠
@bot.command()
async def 지랄해(ctx):
    if not is_authorized(ctx):
        await ctx.send("이건 대상자 전용 커맨드야 😎")
        return
    await ctx.author.send(random.choice(JIRAL_MESSAGES))
    await ctx.send("지랄 디엠 날아갔습니다 💥")

# 숙제 했을 때
@bot.command()
async def 숙제했어(ctx):
    if not is_authorized(ctx):
        return
    today = datetime.now().date()
    homework_records[(ctx.author.id, today)] = True
    await ctx.send(f"오늘 숙제 완료! 너무 잘했어, {ctx.author.display_name}!🌸")

# 벌칙 예고
@bot.command()
async def 벌칙예약(ctx):
    if not is_authorized(ctx):
        return
    await ctx.author.send(random.choice(PENALTY_MESSAGES))
    await ctx.send("벌칙이 예약되었습니다! 😈 숙제 안 하면 벌칙 각!")

# 벌칙 수행 인증
@bot.command()
async def 벌칙인증(ctx):
    if not is_authorized(ctx):
        return
    if not penalty_records.get(ctx.author.id, False):
        await ctx.send(f"{user.name}님, 벌칙을 수행한 인증을 제출해 주세요! 📸")
    else:
        await ctx.send("이미 벌칙 인증이 완료되었습니다! 🎉")

# 메시지에서 인증 이미지 처리
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    ctx = await bot.get_context(message)
    if message.attachments:
        if is_authorized(ctx):
            if not penalty_records.get(message.author.id, False):
                penalty_records[message.author.id] = True
                await message.channel.send(f"{message.author.name}님의 벌칙 인증이 완료되었습니다! 🎉")
            else:
                await message.channel.send("이미 인증했잖아 😏")
        else:
            await message.channel.send("벌칙 인증은 대상자만 가능해요! 🤖")
    await bot.process_commands(message)

# 숙제 통계
@bot.command()
async def 숙제통계(ctx):
    if not is_authorized(ctx):
        return
    missed = [str(date) for (uid, date), done in homework_records.items()
              if uid == ctx.author.id and not done]
    if not missed:
        await ctx.send(f"숙제 완벽하게 다 했어! 대단해! 🏅\n미제출일: {', '.join(missed)}( 총 {len(missed)}일 🌼)")
    else:
        await ctx.send(f"미제출일: {', '.join(missed)}( 총 {len(missed)}일 💀)")


# 매일 특정 시간에 자동 디엠
@tasks.loop(minutes=60)
async def scheduled_jiral():
    now = datetime.now()
    if now.hour in [9, 12, 15, 18, 21, 22, 23]:
        guild = discord.utils.get(bot.guilds)  # 첫번째 서버 기준
        # 유저 ID 기준 DM
        for user_id in target_user_ids:
            try:
                user = await bot.fetch_user(user_id)
                await user.send(random.choice(JIRAL_MESSAGES))
            except Exception as e:
                print(f"유저 {user_id} DM 실패: {e}")
                
        # 역할 기반 DM
        for role_name in target_role_names:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                for member in role.members:
                    try:
                        await member.send(random.choice(JIRAL_MESSAGES))
                    except Exception as e:
                        print(f"{member} DM 실패: {e}")

'''부가기능 디데이, 타이머 '''

# 디데이
d_day_list = {}

@bot.command(name='디데이')
async def dday(ctx, date_str: str):
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = date.today()
        delta = (target_date - today).days

        if delta > 0:
            await ctx.send(f"📆 `{date_str}`까지 D-{delta}")
        elif delta == 0:
            await ctx.send(f"📆 오늘이 바로 `{date_str}`! 🎉")
        else:
            await ctx.send(f"📆 `{date_str}`는 이미 지났어요! (D+{abs(delta)})")
    except ValueError:
        await ctx.send("❌ 날짜 형식이 잘못되었어요. 예: `!디데이 2025-06-01` 처럼 입력해주세요!")

@bot.command()
async def 디데이등록(ctx, 이름: str, 날짜: str):
    try:
        dday_date = datetime.strptime(날짜, "%Y-%m-%d").date()
        d_day_list[이름] = dday_date
        await ctx.send(f"✅ 디데이 '{이름}'이(가) {날짜}로 등록되었어요!")
    except ValueError:
        await ctx.send("❌ 날짜 형식이 잘못됐어요! `YYYY-MM-DD` 형식으로 입력해주세요.")

@bot.command()
async def 디데이목록(ctx):
    if not d_day_list:
        await ctx.send("📭 아직 등록된 디데이가 없어요.")
        return

    today = date.today()
    result = "📅 **디데이 목록**\n"
    for name, dday_date in sorted(d_day_list.items(), key=lambda x: x[1]):
        delta = (dday_date - today).days
        if delta > 0:
            result += f"🔸 {name}: {delta}일 남음 ({dday_date})\n"
        elif delta == 0:
            result += f"🟡 {name}: 바로 오늘! ({dday_date})\n"
        else:
            result += f"⚫️ {name}: {-delta}일 지남 ({dday_date})\n"

    await ctx.send(result)

@bot.command()
async def 디데이삭제(ctx, 이름: str):
    if 이름 in d_day_list:
        del d_day_list[이름]
        await ctx.send(f"🗑️ 디데이 '{이름}'이(가) 삭제되었어요.")
    else:
        await ctx.send(f"❌ 디데이 '{이름}'은(는) 목록에 없어요.")

@bot.command()
async def 디데이초기화(ctx):
    d_day_list.clear()
    await ctx.send("🧹 모든 디데이 목록이 초기화되었습니다!")


# 타이머 기능
# 전역 변수: 타이머 딕셔너리
active_timers = {}

# 시간 파싱 함수 (깔끔하게 분리)
def parse_time(시간문자열):
    pattern = re.compile(r'(?:(\d+)시간)?(?:(\d+)분)?(?:(\d+)초)?')
    match = pattern.fullmatch(시간문자열)
    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours, minutes, seconds

# 타이머 설정 명령어
@bot.command()
async def 타이머(ctx, 시간문자열: str, *, 메시지: str = "타이머 종료!"):
    parsed = parse_time(시간문자열)
    if not parsed:
        await ctx.send("❌ 시간 형식이 잘못됐어요! 예: `1시간30분`, `45분`, `10초` 처럼 입력해주세요.")
        return

    hours, minutes, seconds = parsed
    total_seconds = hours * 3600 + minutes * 60 + seconds

    if total_seconds <= 0:
        await ctx.send("⛔ 타이머 시간은 1초 이상이어야 합니다!")
        return

    end_time = datetime.now() + timedelta(seconds=total_seconds)

    # 기존 타이머 있으면 취소
    if ctx.author.id in active_timers:
        active_timers[ctx.author.id]['task'].cancel()

    async def timer_task():
        try:
            await asyncio.sleep(total_seconds)
            await ctx.send(f"⏰ 타이머 종료: {메시지}")
            try:
                await ctx.author.send(f"⏰ DM 타이머 종료 알림: {메시지}")
            except discord.Forbidden:
                await ctx.send("⚠️ DM 전송에 실패했어요 (DM 차단 상태일 수 있어요).")
        except asyncio.CancelledError:
            pass
        finally:
            active_timers.pop(ctx.author.id, None)

    task = asyncio.create_task(timer_task())
    active_timers[ctx.author.id] = {
        "task": task,
        "end_time": end_time
    }

    await ctx.send(f"⏰ 타이머 시작: {시간문자열} 후에 알려드릴게요.")

# 남은 시간 확인 명령어
@bot.command()
async def 타이머확인(ctx):
    info = active_timers.get(ctx.author.id)
    if not info:
        await ctx.send("🔎 현재 설정된 타이머가 없어요!")
        return

    now = datetime.now()
    remaining = info['end_time'] - now

    if remaining.total_seconds() <= 0:
        await ctx.send("⏰ 타이머가 곧 종료될 예정이에요!")
        return

    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    시간표현 = f"{hours}시간 {minutes}분 {seconds}초" if hours else f"{minutes}분 {seconds}초"
    await ctx.send(f"⏳ 남은 시간: {시간표현}")

# 타이머 취소 명령어
@bot.command()
async def 타이머취소(ctx):
    info = active_timers.get(ctx.author.id)
    if info:
        info['task'].cancel()
        active_timers.pop(ctx.author.id, None)
        await ctx.send("🛑 타이머가 취소되었어요.")
    else:
        await ctx.send("❌ 취소할 타이머가 없습니다!")


        

# 명령어 설명
@bot.command(name='지랄봇명령어')
async def 지랄봇명령어(ctx):
    help_text = """

📖 **혜미 지랄봇 명령어 목록**

 `!지랄해`  
👉 숙제를 안하면 지랄합니다.

 `!숙제했어`  
👉 숙제를 했으니 칭찬합니다.

 `!숙제통계`  
👉 숙제 얼마나 했고, 안했는지 알려줍니다.

 `!벌칙예약`  
👉 숙제 안했으면 벌칙을 받아야지???

 `!벌칙인증`  
👉 벌칙을 했으면 여기에 인증합시다.

 `!지랄봇명령어`  
👉 이 명령어 설명을 보여줍니다.

 `!디데이 [0000-00-00]`  
👉 오늘 기준으로 적은 날짜까지 남은 일수를 알려줍니다.
   예시)!디데이 2002-12-06

 `!디데이등록 [이름] [0000-00-00]`  
👉 주요 일정 디데이를 등록합니다.
   예시)!디데이등록 생일 2002-12-06

 `!디데이목록`  
👉 등록한 디데이를 보여줍니다.

 `!디데이삭제 [이름]`  
👉 작성한 디데이를 삭제합니다.
   예시)!디데이삭제 생일
   
 `!디데이초기화`  
👉 모든 디데이 목록을 초기화합니다.

 `!타이머 [시간] [메세지]`  
👉 타이머 기능을 이용합니다.(아직 1개만 가능) 
   예시)!타이머 1시간18분2초 진실의방감금 
   
 `!타이머취소`  
👉 흘러가는 시간을 취소합니다.

"""
    await ctx.send(help_text)


# 봇 실행
bot.run(TOKEN)

