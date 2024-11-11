# openai_client.py
import openai
from config import OPENAI_API_KEY

DIRECTIVE_PROMPT = "Отвечай кратко по теме нейросетей. Умещай ответ в 200 символов."
openai.api_key = OPENAI_API_KEY

def ask_chatgpt(user_question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": DIRECTIVE_PROMPT},
                {"role": "user", "content": user_question}
            ],
            max_tokens=200,
            temperature=0.5
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Произошла ошибка при обработке запроса к ChatGPT."

def generate_image(prompt):
    try:
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="512x512"
        )
        image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        print(f"An error occurred: {e}")
        return None