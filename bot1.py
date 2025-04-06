from telethon.sync import TelegramClient
from telethon import events
import httpx
import time

api_id = 1234321 # Your api_id
api_hash = 'YOUR API_HASH'
openrouter_key = 'YOUR API KEY'
client = TelegramClient('my_bot_session', api_id, api_hash)

client.start()

async def ask_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {openrouter_key}",
        "HTTP-Referer": "https://you.example",
        "Content-Type": "application/json",
    }

    json = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", # tell the model how to behave
             "content": "Ты общаешься как обычный человек, отвечая коротко и по существу. Будь дружелюбным и не перегружай ответы. Не пиши больше 6 слов"},
            {"role": "user", "content": prompt}
        ],
    }
    async with httpx.AsyncClient() as http:
        r = await http.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=json)

        print("Ответ от OpenRouter:")
        print(r.text)

        if r.status_code != 200:
            return f"Ошибка OpenRouter: {r.status_code} — {r.text}"

        try:
            return r.json()["choices"][0]["message"]["content"]
        except KeyError:
            return f"Ошибка разбора ответа: {r.text}"


async def send_welcome_message(event):
    user_id = event.sender_id

    try:
        user_entity = await client.get_entity(user_id)

        messages = await client.get_messages(user_entity, limit=1)

        if len(messages) == 0:
            # FIRST MESSAGE
            welcome_message = (
                "Приветствую, друг! Если я в сети, то подожди пока отвечу. "
                "Если же я не в сети, не нужно спамить, просто подожди — я отвечу через 5-10 часов, "
                "а если не отвечу... УШЕЛ В ЛЕС."
            )
            await event.reply(welcome_message)
            print("Приветственное сообщение отправлено!")
        else:
            # CHECKING THE TIME OF THE LAST CALL
            last_message_time = messages[0].date.timestamp()
            current_time = time.time()
            time_diff = current_time - last_message_time

            if time_diff > 36000:  # 10 HOURS
                reply_message = "Скоро отвечу, подожди несколько минуток..."
                await event.reply(reply_message)
                print("⏳ Сообщение о том, что скоро ответим, отправлено!")
    except ValueError as e:
        print(f"Ошибка при получении сущности пользователя: {e}")
        await event.reply("Ухты, новенький?")
        return

@client.on(events.NewMessage(incoming=True))
async def handler(event):
    if event.is_private:
        user_message = event.raw_text
        print(f"👤 {user_message}")

        await send_welcome_message(event)

        reply = await ask_openrouter(user_message)
        await event.reply(reply)
        print(f"🤖 {reply}")

# START CLIENT
client.run_until_disconnected()
