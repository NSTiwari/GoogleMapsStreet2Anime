# Google Maps Street2Anime
This project is an implementation of transforming places in Google Maps Street View to anime using Gemini.

## Pre-requisites:

1. Google Cloud SDK [(gcloud CLI)](https://cloud.google.com/sdk/docs/install) installed for authentication.
   
   - Go to terminal/command prompt and enter the command: `gcloud init` and choose the project ID.
     
   - Enter the following command to set a default login: `gcloud auth application-default login`.

## Run the Web App:

1. Clone the repository on your local machine.
2. Navigate to `cd GoogleMapsStreet2Anime` directory.
3. Run `pip install -r requirements.txt` to install the packages.
4. Open `.env` file and configure your `GEMINI_API_KEY`, `MAPS_API_KEY`.
   > **NOTE**
   > Enable the Maps JavaScript API, Places API, Places (New) API and the Street View API in Google Cloud credentials.
   > 
6. Run `flask run` to start the server.
7. Open `localhost:5000` on your web browser and live in your anime world in Google Maps Street View.

## Results:
<img src="https://github.com/NSTiwari/Sketch2Vid/blob/main/static/images/sketch2video.gif"/>

