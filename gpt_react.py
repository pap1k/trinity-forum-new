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
        messages=[{"role": "user", "content": "- Среднее количество текста.\n- Ты - профессиональный игрок с большой репутацией.\n - События просиходят в игровом мире Trinity GTA на сервере Trinity RPG.\n\nВыскажи свое мнение по поводу новости. Как ее события могут повлиять на дальнейшую жизнь?\n\n"+newtxt}],
    )
    reaction = response.choices[0].message.content
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Сократи текст, оставив основной смысл:\n\n"+reaction}],
    )
    return response.choices[0].message.content
