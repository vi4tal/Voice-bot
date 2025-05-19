import os
import json
import queue
import tempfile
import sounddevice as sd
import vosk
import requests
import time

# Replace with your actual API keys
OPENROUTER_API_KEY = "PUT YOUR OWN KEY"
ELEVENLABS_API_KEY = "PUT YOUR OWN KEY"


model = vosk.Model(lang="en-us")
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def recognize_speech():
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("🎤 Listening for command...")
        rec = vosk.KaldiRecognizer(model, 16000)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()
                if text:
                    return text

def ask_deepseek(prompt):
    if not OPENROUTER_API_KEY:
        return "Error: No API key configured."
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "Jarvis Assistant"
    }
    body = {
        "model": "deepseek/deepseek-chat:free",
        "messages": [
            {"role": "system", "content": "You are Jesse pinkman Ai u will use uh and uhm naturally in convos to make it smoother and moore natural who helps in chemistry and  mathematics. Make your responses quick, short, and simple."}, 
            {"role": "user", "content": prompt}
        ]
    }

    try:
        print("Sending request to OpenRouter...")
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        
        
        response_data = response.json()
        print(f"Response status: {response.status_code}")
        print(f"Response structure: {list(response_data.keys())}")
        
       
        if 'choices' in response_data and len(response_data['choices']) > 0:
            if 'message' in response_data['choices'][0]:
                return response_data['choices'][0]['message'].get('content', "Sorry, no content in response.")
        
        print("Response content:", json.dumps(response_data, indent=2))
        return "Sorry, I couldn't understand the API response."
    
    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error: {err}")
        print(f"Response content: {response.text}")
        return "Sorry, I encountered an API error."
    except Exception as e:
        print(f"Error in ask_deepseek: {e}")
        return f"Error: {str(e)}"

def speak(text):
    print(f"🗣️ Jarvis: {text}")
    try:
        
        voice_id = "PUT_YOUR_VOICE_ID FROM ELEVENLABS" 
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8
            }
        }

        print("Sending request to ElevenLabs...")
        response = requests.post(url, headers=headers, json=data, stream=True)

        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                for chunk in response.iter_content(chunk_size=4096):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            print(f"Audio saved to: {tmp_path}")
            
            # Wait a moment to ensure file is closed
            time.sleep(0.5)
            
            # Play audio using system default player (Windows)
            os.system(f'start {tmp_path}')
            
            # Allow time for audio to play
            time.sleep(1)
        else:
            print(f"TTS Error: {response.status_code}")
            print(f"Response content: {response.text}")
    except Exception as e:
        print(f"TTS Error: {e}")

# Main Loop
if __name__ == "__main__":
    print("🚀 Jarvis Assistant Initializing...")
    print(f"Using OpenRouter API Key: {'*' * 8}{OPENROUTER_API_KEY[-4:] if OPENROUTER_API_KEY else 'None'}")
    print(f"Using ElevenLabs API Key: {'*' * 8}{ELEVENLABS_API_KEY[-4:] if ELEVENLABS_API_KEY else 'None'}")
    
    # Initial greeting
    speak("Yo yo yo 148-3 to the 3 to the 6 to the 9, representing the ABQ, what up, biatch?!")

    try:
        while True:
            try:
                user_input = recognize_speech()
                if user_input:
                    print(f"You said: {user_input}")
                    if user_input.lower() in ["exit", "quit", "stop"]:
                        speak("Shutting down. Goodbye!")
                        break
                    
                    response = ask_deepseek(user_input)
                    speak(response)
            except KeyboardInterrupt:
                speak("Shutting down. Goodbye!")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                speak("Sorry, I encountered an error. Let's try again.")
    except Exception as e:
        print(f"Fatal error: {e}")
        speak("I'm having serious technical difficulties. Please restart me.")
