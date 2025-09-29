import berserk

TOKEN = "lip_RaPiYQxRxyC61X3urYME"

session = berserk.TokenSession(TOKEN)
client = berserk.Client(session=session)

print("Bot เริ่มทำงานแล้ว...")

for event in client.bots.stream_incoming_events():
    if event["type"] == "challenge":
        challenge_id = event["challenge"]["id"]
        print(f"มี challenge ใหม่: {challenge_id}, ตอบรับ...")
        client.bots.accept_challenge(challenge_id)
    
    elif event["type"] == "gameStart":
        game_id = event["game"]["id"]
        print(f"เกมเริ่ม: {game_id}, ทำ move e2e4")
        client.bots.make_move(game_id, "e2e4")
