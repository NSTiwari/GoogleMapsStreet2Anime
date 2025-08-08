from datetime import datetime
import os
import base64
import io
import requests
import PIL.Image
from flask import Flask, request, jsonify
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import json

from google.genai import types
from google import genai

load_dotenv('.env')

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MAPS_API_KEY = os.environ.get("MAPS_API_KEY")

MODEL_ID = 'gemini-2.0-flash-exp-image-generation'


app = Flask(__name__)
CORS(app)


client = None
if not GEMINI_API_KEY:
    print("Error: GOOGLE_API_KEY not found in .env file.")
else:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print(f"Gemini Client initialized successfully for model: {MODEL_ID}")
    except Exception as e:
        print(f"Error configuring Gemini or initializing client: {e}")


@app.route('/')
def index():
    """
    Renders the main HTML page and injects the Maps API key.
    """
    # The key from .env is passed as a variable to the template.
    return render_template('index.html', maps_api_key=MAPS_API_KEY)

@app.route('/generate-anime', methods=['POST'])
def generate_anime_view():
    if not client:
        return jsonify({"error": "Gemini client not initialized."}), 500

    req_data = request.json
    if not req_data or not all(k in req_data for k in ['lat', 'lng', 'heading', 'pitch', 'fov']):
        return jsonify({"error": "Missing or invalid location data"}), 400

    lat, lng, heading, pitch, fov = req_data['lat'], req_data['lng'], req_data['heading'], req_data['pitch'], req_data['fov']

    streetview_url = (
        f"https://maps.googleapis.com/maps/api/streetview"
        f"?size=640x640&location={lat},{lng}&heading={heading}"
        f"&pitch={pitch}&fov={fov}&key={MAPS_API_KEY}"
    )
    
    try:
        response = requests.get(streetview_url)
        response.raise_for_status()
        
        street_image_bytes = response.content
        
        # Save image locally.
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"streetview_captures/capture_{timestamp}.jpg"
            with open(filename, "wb") as f:
                f.write(street_image_bytes)
            print(f"Successfully saved Street View image to {filename}")
        except Exception as e:
            print(f"Could not save file: {e}")
        # --- END OF NEW CODE ---

        content_length = int(response.headers.get('Content-Length', 0))
        if content_length < 8000:
            print(f"No valid Street View imagery found. Size: {content_length} bytes.")
            return jsonify({"error": "No Street View imagery available here."}), 404
            
        street_view_pil_image = PIL.Image.open(io.BytesIO(street_image_bytes))
        print(f"Successfully fetched valid Street View image. Size: {content_length} bytes.")

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch Street View image: {e}"}), 500
    except PIL.UnidentifiedImageError:
        return jsonify({"error": "Invalid image data received from Street View"}), 500

    try:
        prompt_text = "Transform this image into Studio Ghibli style. Preserve the original aspects of the image. Use bright and calm colors. Keep the atmosphere calm and serene, with no additional characters. Remove any watermarks, if present. Do not alter the original elements. Treat this image as a fixed background for an anime film."
        #prompt_text = "Transform this image into Studio Ghibli style. Preserve the original aspects of the image exactly the way they are. Use bright, calm colors. Keep the atmosphere calm and serene, with no additional characters. Your response must contain only the raw image. Remove any watermarks, if present. Do not alter the original elements like trees, plants, buildings, monuments, structures, bridges, cars, etc. Do not add or remove anything. Do not hallucinate new content. Treat this image as a fixed background for an anime film."
        # prompt_text = "Apply a Studio Ghibli-style visual treatment to this image. Do not change any objects, layout, positions, or shapes. Maintain exact realism in composition and perspective. Only apply color grading, soft brush textures, and slight line stylization to make the image feel hand-painted and animated. Use calm, bright colors and a serene atmosphere without increasing the image's brightness too much. Do not add or remove anything. Do not hallucinate new content. Treat this image as a fixed background for an anime film."
        #prompt_text = "Transform this image into a hand-painted Studio Ghibli animation style. Preserve original elements, use bright, calm colors. Replace photorealistic details with stylized, illustrated features characteristic of Ghibli films. Emphasize whimsical natural elements, clean outlines, and a tranquil, dreamlike atmosphere. Avoid adding any new characters or objects. The final image should feel like a serene animation still from a Ghibli movie, capturing all the original elements and their positions."
        
        print(f"Sending request to Gemini model: {MODEL_ID}...")

        generation_config = types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
        )

        response = client.models.generate_content(model=MODEL_ID,
                                                  contents=[prompt_text, street_view_pil_image],
                                                  config=generation_config)

        print(response)

        if not response.candidates:
            error_message = "Gemini returned no candidates."
            if response.prompt_feedback:
                error_message += f" Block reason: {response.prompt_feedback.block_reason}"
            return jsonify({"error": error_message}), 500

        image_part = next(
            (part for part in response.candidates[0].content.parts if hasattr(part, 'inline_data') and part.inline_data),
        None
        )

        if not image_part:
            fallback_text = next(
                (part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')),
            "No image or text available in response."
              )
            

            return jsonify({"error": f"Gemini returned text instead of an image: '{fallback_text}'"}), 500

           
        image_data_bytes = image_part.inline_data.data
        mime_type = image_part.inline_data.mime_type
        base64_image = base64.b64encode(image_data_bytes).decode('utf-8')
        
        return jsonify({"image": f"data:{mime_type};base64,{base64_image}"})

    except Exception as e:
        return jsonify({"error": f"Failed to generate image: {getattr(e, 'message', str(e))}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)