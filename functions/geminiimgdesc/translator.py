from google.cloud import translate
import google.auth


def translate_text(text: str, target_language_code: str) -> str:
    _, project_id = google.auth.default()
    print(project_id)
    client = translate.TranslationServiceClient()
    print(f"Translating '{text}' to '{target_language_code}'")
    response = client.translate_text(
        parent=f"projects/{project_id}",
        contents=[text],
        target_language_code=target_language_code,
    )
    translation = response.translations[0]
    print(f"Translated to '{translation.translated_text}'")
    return translation.translated_text
