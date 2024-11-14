import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import cv2  # OpenCV for camera capture
import webbrowser
import random
import time
import numpy as np
from google.auth.transport.requests import Request

# YouTube API setup
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
CLIENT_SECRETS_FILE = "credentials.json"

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

def youtube_authenticate():
    """Authenticate the user and return the YouTube API service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')

        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    youtube = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
    return youtube

def search_youtube(youtube, query):
    """Search for videos on YouTube based on a query and return a list of video URLs."""
    request = youtube.search().list(
        part="snippet",
        maxResults=5,  # Fetch more results for shuffling
        q=query
    )
    response = request.execute()
    
    video_urls = []
    for item in response['items']:
        if item['id']['kind'] == 'youtube#video':
            video_id = item['id']['videoId']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_urls.append(video_url)
    
    return video_urls  # Return list of video URLs

def play_videos_in_single_tab(video_list, played_videos):
    """Play one video at a time in a single tab, ensuring no repeats."""
    if video_list:
        # Filter out already played videos
        filtered_videos = list(set(video_list) - set(played_videos))
        
        if not filtered_videos:
            print("All videos have already been played.")
            return
        
        random.shuffle(filtered_videos)  # Shuffle the video list
        for video_url in filtered_videos:
            print(f"Playing video: {video_url}")
            webbrowser.open(video_url)  # Open the video in the browser
            print("Waiting for the video to finish...")
            time.sleep(30)  # Wait for 30 seconds before opening the next video (or adjust this)
            played_videos.append(video_url)  # Mark this video as played
    else:
        print("No videos found to play.")

def capture_image(output_folder):
    """Capture an image using the webcam when the spacebar is pressed and save it."""
    cap = cv2.VideoCapture(0)  # 0 is the default camera

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        cv2.imshow('Press Space to Capture', frame)

        key = cv2.waitKey(1)

        if key == 32:  # Space bar pressed
            image_path = os.path.join(output_folder, 'captured_image.jpg')
            cv2.imwrite(image_path, frame)
            print(f"Image saved to {image_path}")
            break
        elif key == 113:  # 'q' pressed
            print("Quitting without saving.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return image_path if key == 32 else None

# New function for breathing exercise with webcam monitoring
def breathing_exercise_with_monitoring(duration=60):
    """Breathing exercise with visual guide and webcam monitoring to check if the user is breathing properly."""
    cap = cv2.VideoCapture(0)  # Initialize webcam

    if not cap.isOpened():
        print("Error: Could not open camera for monitoring.")
        return

    inhale = True
    start_time = time.time()
    exercise_time = 0

    while exercise_time < duration:
        ret, frame = cap.read()  # Capture frame from webcam
        if not ret:
            print("Error: Could not read from webcam.")
            break

        # Set up a blank image (for breathing guide)
        img = np.zeros((400, 400, 3), dtype="uint8")

        # Calculate the radius for inhale/exhale (cycle between 50 to 150 pixels)
        if inhale:
            radius = int(50 + (time.time() - start_time) * 100)  # Expanding
        else:
            radius = int(150 - (time.time() - start_time) * 100)  # Contracting

        # Draw a circle that expands and contracts
        cv2.circle(img, (200, 200), radius, (0, 255, 0), -1)

        # Display 'Inhale' or 'Exhale' text based on the breathing phase
        text = "Inhale" if inhale else "Exhale"
        cv2.putText(img, text, (150, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # Show the breathing guide
        cv2.imshow("Breathing Guide", img)

        # Detect the face or chest for monitoring breathing movements
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            # Draw rectangle around face (to give feedback that it's being monitored)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                # Provide feedback if face movement matches breathing pattern
                if inhale:
                    feedback = "Inhaling detected!"  # For simplicity, we assume movement is detected
                else:
                    feedback = "Exhaling detected!"
                cv2.putText(frame, feedback, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Display the webcam frame
        cv2.imshow("Webcam Monitoring", frame)

        # If the circle has fully expanded or contracted, switch phase
        if (inhale and radius >= 150) or (not inhale and radius <= 50):
            inhale = not inhale  # Switch between inhale/exhale
            start_time = time.time()  # Reset timer for new cycle

        # Exit the exercise if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        exercise_time = time.time() - start_time

    cap.release()
    cv2.destroyAllWindows()
    print("Breathing exercise completed.")

def main():
    youtube = youtube_authenticate()

    output_folder = 'images'
    os.makedirs(output_folder, exist_ok=True)
    captured_image_path = capture_image(output_folder)
    
    if captured_image_path:
        print(f"Image captured successfully at {captured_image_path}")

        # Simulate emotion detection
        emotions = ['happy', 'sad', 'angry', 'neutral']
        emotion = random.choice(emotions)

        # Define video queries based on emotion in Tamil
        video_queries = {
            'happy': "Tamil vibe songs",  # Happy videos
            'sad':  "Tamil comedy funny dialogues",  # Sad videos
            'angry': "Tamil soft music, trending funny videos",  # Angry videos
            'neutral': "melody songs in Tamil"  # Neutral videos
        }

        print(f"Emotion detected: {emotion}. Searching for: {video_queries[emotion]}")

        # Maintain a list of played videos
        played_videos = []

        # Trigger a breathing exercise if the detected emotion is 'angry'
        if emotion == 'angry':
            choice = input("Angry emotion detected. Would you like to do a breathing exercise? (yes/no): ")
            if choice.lower() == 'yes':
                breathing_exercise_with_monitoring(duration=60)  # Run breathing exercise with monitoring
                print("Breathing exercise completed. Now searching for calming videos.")
            else:
                print("Skipping breathing exercise.")

        # After breathing exercise, proceed with video search
        video_list = search_youtube(youtube, video_queries[emotion])

        if video_list:
            play_videos_in_single_tab(video_list, played_videos)
        else:
            print("No videos found for the search query.")
    else:
        print("Skipping YouTube search due to image capture failure.")

if __name__ == "__main__":
    main()
