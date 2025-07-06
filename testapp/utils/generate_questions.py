from google import genai
from google.genai.types import Content
from pydantic import BaseModel, Field, conlist
from django.conf import settings
import json


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_option_id: int
    topic: str


client = genai.Client(api_key=settings.API_KEY_GENAI_ADMIN)


def generate_questions(subject="Matematika", grade=5, count=10, topics=None):
    prompt = f"""
        Qaraqalpaq tilinde {subject} páni boyınsha {grade}-klass oqıwshıları ushın {count} DANA quiz sorawın jaratıń.

        Talaplar:
        1. Soraw anıq hám túsinikli bolıwı kerek
        2. Tek 4 juwap variantı bolıwı kerek
        3. Tek bir dana durıs juwap variantı bolıwı kerek
        4. Durıs juwap variantlardıń indeksin (0, 1, 2, 3) beriw kerek
        5. Sorawlar qızıqlı hám úyretiwshi bolıwı kerek
        6. Sorawlar hám juwaplar qaraqalpaq tilinde hám qátesiz bolıwı kerek
        7. Sorawlar tákirarlanbawı (aldın bunday soraw berilmegen bolıwı) kerek, jańa hám qızıqlı sorawlar jaratıw kerek
        8. Sorawdıń teması hár saparı hár túrli bolsın.
        9. EŃ ÁHMIYETLISI: Qátesiz latın álipbesinde hám qaraqalpaq tilinde bolıwı kerek.
        10. {count} dana sorawdı bir json tizimi túrinde qaytarıń.
    """

    if topics:
        prompt += f'\n\nTemalar: \n{topics}'

    try:
        with open('history.json', 'r', encoding='utf-8') as file:
            history = json.load(file)
    except:
        history = []

    chat = client.chats.create(
        model="gemini-2.5-pro",
        config={
            "response_mime_type": "application/json",
            "response_schema": list[QuizQuestion]
        },
        history=[Content(**data) for data in history]
    )
    response = chat.send_message(prompt + f"\n\n{count} dana soraw jaratıń.")

    history = [content.model_dump() for content in chat._curated_history[-500:]]
    with open('history.json', 'w', encoding='utf-8') as file:
        json.dump(history, file, ensure_ascii=False, indent=4)

    quizzes: list[QuizQuestion] = response.parsed
    return quizzes
