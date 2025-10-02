from flask import Flask, render_template, request, url_for
import json
import os

app = Flask(__name__)


# Load language data
def load_translations():
    translations = {}
    locales_dir = os.path.join(app.root_path, "locales")

    for lang_file in ["en.json", "uk.json"]:
        lang_code = lang_file.split(".")[0]
        file_path = os.path.join(locales_dir, lang_file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                translations[lang_code] = json.load(f)
        except FileNotFoundError:
            translations[lang_code] = {}

    return translations


def get_current_language():
    return request.args.get("lang", "en")


@app.route("/")
def index():
    lang = get_current_language()
    print(lang)
    translations = load_translations()
    print(translations)
    return render_template(
        "index.html",
        lang=lang,
        t=translations.get(lang, {}),
        all_translations=translations,
    )


@app.route("/how-to")
def how_to():
    lang = get_current_language()
    translations = load_translations()
    return render_template(
        "how-to.html",
        lang=lang,
        t=translations.get(lang, {}),
        all_translations=translations,
    )


@app.route("/faq")
def faq():
    lang = get_current_language()
    translations = load_translations()
    return render_template(
        "faq.html",
        lang=lang,
        t=translations.get(lang, {}),
        all_translations=translations,
    )


@app.route("/health")
def health():
    return {"status": "healthy"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003, debug=True)
