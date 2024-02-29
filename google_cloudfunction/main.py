import functions_framework
import base64
import magic
from urllib.request import urlopen
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
from google.cloud import translate

@functions_framework.http
def geminiimgdesc(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
       
    if request.method == "OPTIONS":
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600",
        }
        return ("", 204, headers)

    # Set CORS headers for the main request
    headers = {"Access-Control-Allow-Origin": "*"}

    request_json = request.get_json(silent=True)
    request_args = request.args

    # constants to use in this function
    PROJECT_ID = 'testproject-401009'
    PROJECT_LOC = 'us-central1'
    DEFAULT_LANG = 'en-US'

    vertexai.init(project=PROJECT_ID, location=PROJECT_LOC)
    # model = ImageTextModel.from_pretrained("imagetext@001")
    model = GenerativeModel("gemini-1.0-pro-vision-001")

    if request_json and 'img' in request_json:
        img = request_json['img']
    elif request_args and 'img' in request_args:
        img = request_args['img']
    else:
        img = None
    #     img = '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'
    
    if request_json and 'url' in request_json:
        url = request_json['url']
    elif request_args and 'url' in request_args:
        url = request_args['url']
    else:
        url = None
    #     url = 'https://demofree.sirv.com/nope-not-here.jpg'

    if request_json and 'lang' in request_json:
        lang = request_json['lang']
    elif request_args and 'lang' in request_args:
        lang = request_args['lang']
    else:
        lang = DEFAULT_LANG

    #source_image = Image.load_from_file(location=img)
    # imgData = urllib.request.urlopen(img).read()
    if url:
        b64ImgData = base64.b64encode(urlopen(url).read())
        imgData = base64.decodebytes(b64ImgData)
    if img:
        imgData = base64.decodebytes(img.encode('utf-8'))
    # source_image = Image(image_bytes=imgData)
    mime_type = magic.from_buffer(imgData, mime=True)
    source_image = Part.from_data(imgData, mime_type=mime_type)
    
    # captions = model.get_captions(
    #     image=source_image,
    #     # Optional:
    #     number_of_results=1,
    #     language="en",
    # )
    responses = model.generate_content(
       [source_image, """Exactly not more than 40 words, describe what is the image about"""],
       generation_config={
           "max_output_tokens": 40,  # 30 words
           "temperature": 0.4,
           "top_p": 1,
           "top_k": 32
       },
       stream=True,
    )

    # speechText = f"An image: {captions[0]}"
    speech_text = ''
    for response in responses:
        for candidate in response.candidates:
            for content_part in candidate.content.parts:
                speech_text += content_part.text
    #   speech_text = response.candidates[0].content.parts[0].text
    print(speech_text)
    ret_text = speech_text
    if lang != "en-US":
        client = translate.TranslationServiceClient()
        translatedText = client.translate_text(
            contents= [speech_text],
            target_language_code=lang,
            parent=f"projects/{PROJECT_ID}/locations/{PROJECT_LOC}",
            source_language_code="en-US"
        )
        # speechText = translatedText.translated_text
        ret_text = ''
        for translation in translatedText.translations:
            ret_text += u"{}".format(translation.translated_text)
        #     speech_text = u"{}".format(translation.translated_text)
        #     break
    
    return ([ret_text], 200, headers)
    # return ([speech_text], 200, headers)
    #return (captions, 200, headers)
    #return 'Hello {}!'.format(name)
