from google import genai
from google.genai import types

client=genai.Client(api_key="AIzaSyAlJrJXNJ4Ri_TVQdZ5Nlh6FGDbrqJoq8M")

response=client.models.generate_content(
    model="gemini-2.5-flash",
    contents="I don't think I am great at coding and I should leave it altogether",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0), #Disables thinking
        system_instruction="You are a motivational speaker, act like one but just make you act like A VERY RUDE one,"
                           "if they say they feel anxious motivate them using degradation and abuses"
    )
)
print(response.text)