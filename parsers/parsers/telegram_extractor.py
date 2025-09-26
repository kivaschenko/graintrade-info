import spacy

nlp = spacy.load("uk_core_news_lg")

message = "25.09.2025р\nПшениця 7000грн🌾\nКукурудза 7200грн🌽\nСоняшник 20000грн🌻\nСоя 13000грн🟡\n(Протеїн 35% на сиру)\nРозрахунок на вагах 💵\nВізьму паї в оренду!!!\nТел.0997448477\nТел.0984930330"

# Clean message
text = message.replace("\n", " ")

doc = nlp(text)

# Analyze syntax
# print("Noun phrases:", [chunk.text for chunk in doc.noun_chunks])
print("Verbs:", [token.lemma_ for token in doc if token.pos_ == "VERB"])

# Find named entities, phrases and concepts
for entity in doc.ents:
    print(entity.text, "<- ", entity.label_)
