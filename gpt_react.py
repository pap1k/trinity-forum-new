from g4f.client import Client
import g4f.Provider.Aichatos as prov

client = Client(provider=prov)

def get_reaction(post_text:str):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Сократи текст, оставив основной смысл:\n\n"+post_text}],
    )
    newtxt = response.choices[0].message.content
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Выскажи свое мнение. Среднее количество текста. События просиходят в игровом мире Trinity GTA на сервере Trinity RPG:\n\n"+newtxt}],
    )
    return response.choices[0].message.content
