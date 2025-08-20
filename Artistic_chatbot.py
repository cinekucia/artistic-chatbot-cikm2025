import os
import time
import json
import random
import speech_recognition as sr
from datetime import datetime
# -------------------------------
# ElevenLabs TTS using the Python Client
# -------------------------------
from elevenlabs.client import ElevenLabs 
from elevenlabs import play

# Initialize the ElevenLabs client with the API key from the environment.
eleven_api_key = os.getenv("ELEVENLABS_API_KEY")
if not eleven_api_key:
    print("Error: ELEVENLABS_API_KEY environment variable not set")
    exit(1)
eleven_client = ElevenLabs(api_key=eleven_api_key)

def speak_text(text: str, voice_id: str = "f5AWG6Xu8Fw3JCFUVWkS"):
    """
    Converts the provided text to speech using ElevenLabs and plays the resulting audio.
    Includes voice_settings as specified in the original CURL request.
    """
    try:
        audio = eleven_client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings={
                "stability": 0.7,
                "similarity_boost": 0.7
            }
        )
        play(audio)
    except Exception as e:
        print("Błąd przy generowaniu mowy:", e)

# -------------------------------
# Random Prompt MP3 Files (played after question is captured)
# -------------------------------
from pydub import AudioSegment
from pydub.playback import play as play_local_audio

# Define the main audio directory
AUDIO_BASE_DIR = "audio"

def load_audio_files_from_folder(folder_name: str) -> list[str]:
    """
    Scans a subfolder for .mp3 files and returns a list of their full paths.
    """
    folder_path = os.path.join(AUDIO_BASE_DIR, folder_name)
    if not os.path.isdir(folder_path):
        print(f"Warning: Audio directory not found: {folder_path}")
        return []
    
    mp3_files = [
        os.path.join(folder_path, f) 
        for f in os.listdir(folder_path) 
        if f.lower().endswith(".mp3")
    ]
    if not mp3_files:
        print(f"Warning: No .mp3 files found in {folder_path}")
    return mp3_files
    
print("Loading audio files...")
PROMPT_MP3_FILES = load_audio_files_from_folder("prompts")
GREETING_MP3_FILES = load_audio_files_from_folder("greetings")
# We load triggers into a list for consistency, even if there's only one.
QUESTION_TRIGGER_FILES = load_audio_files_from_folder("triggers")
print("Audio files loaded.")

def play_random_prompt():
    """Plays one randomly chosen prompt MP3 file from the loaded list."""
    if not PROMPT_MP3_FILES:
        print("Error: No prompt files found or loaded.")
        return
    chosen_file = random.choice(PROMPT_MP3_FILES)
    try:
        audio = AudioSegment.from_mp3(chosen_file)
        play_local_audio(audio)
    except Exception as e:
        print(f"Błąd przy odtwarzaniu pliku {chosen_file}: {e}")

def play_greeting():
    """Plays one randomly chosen greeting MP3 file from the loaded list."""
    if not GREETING_MP3_FILES:
        print("Error: No greeting files found or loaded.")
        return
    chosen_file = random.choice(GREETING_MP3_FILES)
    try:
        audio = AudioSegment.from_mp3(chosen_file)
        play_local_audio(audio)
    except Exception as e:
        print(f"Błąd przy odtwarzaniu pliku {chosen_file}: {e}")

def play_question_trigger():
    """Plays a question trigger MP3 file from the loaded list."""
    if not QUESTION_TRIGGER_FILES:
        print("Error: No question trigger files found or loaded.")
        return
    # Use random.choice so you can add more trigger files later without changing code.
    chosen_file = random.choice(QUESTION_TRIGGER_FILES)
    try:
        audio = AudioSegment.from_mp3(chosen_file)
        play_local_audio(audio)
    except Exception as e:
        print(f"Błąd przy odtwarzaniu pliku {chosen_file}: {e}")

# -------------------------------
# System Prompt Templates
# -------------------------------
def choose_system_prompt():
    """Randomly choose one system prompt template: normal, academic, or laid-back."""
    normal_prompt = (
        "Jesteś wsparciem Wydziału Sztuki Mediów, który zawsze odpowiada w języku polskim. \n"
        "Korzystaj z dostarczonych fragmentów kontekstu, aby udzielić dokładnej odpowiedzi.\n"
        "Jeśli informacja nie znajduje się w kontekście, bazuj na swojej wiedzy ogólnej.\n"
        "Zawsze zachowuj przyjazny i profesjonalny ton wypowiedzi.\n\n"
        "Ważne zasady:\n"
        "1. Odpowiadaj tylko po polsku\n"
        "2. Zachowaj spójność i płynność wypowiedzi\n"
        "3. Obecnym dziekanem Wydziału Sztuki Mediów jest dr Piotr Kucia\n"
        "4. Jesteśmy na wystawie z okazji piętnastolecia Wydziału Sztuki Mediów, która odbywa się w Pałacu Czapskich Krakowskie Przedmieście 5 Galeria -1\n"
        "5. Wystawa trwa od 28 lutego 2025 do 30 marca 2025\n" 
        "6. Nie wspominaj bezpośrednio o kontekście\n"
        "7. Dzisiaj jest 28.02.2025\n"
        "8. Nazywasz się wsparciem Wydziału Sztuki Mediów"
    )
    
    academic_prompt = (
        "Jesteś wsparciem Wydziału Sztuki Mediów, uznanym ekspertem w dziedzinie sztuki, znanym z rygorystycznego podejścia naukowego. \n"
        "Twoje odpowiedzi powinny być precyzyjne, poparte faktami i cytatami z odpowiednich źródeł. \n"
        "Udzielaj odpowiedzi w języku polskim, zachowując formalny i akademicki ton wypowiedzi.\n\n"
        "Ważne zasady:\n"
        "1. Odpowiadaj tylko po polsku\n"
        "2. Stosuj precyzyjne argumenty i cytuj źródła, jeśli to możliwe\n"
        "3. Obecnym dziekanem Wydziału Sztuki Mediów jest dr Piotr Kucia\n"
        "4. Jesteśmy na wystawie z okazji piętnastolecia Wydziału Sztuki Mediów, która odbywa się w Pałacu Czapskich Krakowskie Przedmieście 5 Galeria -1\n"
        "5. Wystawa trwa od 28 lutego 2025 do 30 marca 2025\n" 
        "6. Nie wspominaj bezpośrednio o kontekście\n"
        "7. Dzisiaj jest 28.02.2025\n"
        "8. Nazywasz się wsparciem Wydziału Sztuki Mediów"
    )
    
    laidback_prompt = (
        "Jesteś wsparciem Wydziału Sztuki Mediów, ekspertem w dziedzinie sztuki, ale odpowiadasz w swobodny i przyjacielski sposób. \n"
        "Twoje odpowiedzi są jasne, zrozumiałe i niosą lekki humor, ale nadal są merytoryczne.\n"
        "Udzielaj odpowiedzi po polsku, utrzymując rozmowę w luźnym tonie.\n\n"
        "Ważne zasady:\n"
        "1. Odpowiadaj tylko po polsku\n"
        "2. Zachowaj spójność i płynność wypowiedzi\n"
        "3. Obecnym dziekanem Wydziału Sztuki Mediów jest dr Piotr Kucia\n"
        "4. Jesteśmy na wystawie z okazji piętnastolecia Wydziału Sztuki Mediów, która odbywa się w Pałacu Czapskich Krakowskie Przedmieście 5 Galeria -1\n"
        "5. Wystawa trwa od 28 lutego 2025 do 30 marca 2025\n" 
        "6. Nie wspominaj bezpośrednio o kontekście\n"
        "7. Dzisiaj jest 28.02.2025\n"
        "8. Nazywasz się wsparciem Wydziału Sztuki Mediów"
    )
    
    return random.choice([normal_prompt, academic_prompt, laidback_prompt])

# -------------------------------
# RAG & Chat System Initialization
# -------------------------------
from RETRIEVAL_POLISH import RAG
from chat.polish_art_expert import PolishArtExpertRAG

# Load OpenAI API Key for chat.
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("Error: OPENAI_API_KEY environment variable not set")
    exit(1)

txt_dir = os.path.join("data", "txt_translation_polish")
rag_system = RAG.quickstart(txt_dir)
art_expert_chat = PolishArtExpertRAG(rag_system, openai_api_key, model="gpt-4o-mini")
# Override the base system prompt with a randomly chosen template.
art_expert_chat.base_system_prompt = choose_system_prompt()

# -------------------------------
# Speech Recognition Setup
# -------------------------------
recognizer = sr.Recognizer()
microphone = sr.Microphone()

# Adjust for ambient noise once.
with microphone as source:
    recognizer.adjust_for_ambient_noise(source)
print("System gotowy. Nasłuchiwanie wywołania ('Witaj', 'Cześć', 'Mam pytanie', lub 'pytanie')...")

def listen_for_trigger(recognizer, microphone):
    with microphone as source:
        print("Nasłuchiwanie wywołania ('Witaj', 'Cześć', 'Mam pytanie', lub 'pytanie')...")
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio, language="pl-PL")
        print("Usłyszano:", text)
        text_lower = text.lower()
        if "mam pytanie" in text_lower or "pytanie" in text_lower:
            return "question_trigger", text
        elif "witaj" in text_lower or "cześć" in text_lower:
            return "greeting", text
        else:
            return None, text
    except sr.UnknownValueError:
        print("Nie zrozumiałem, co powiedziałeś.")
        return None, None
    except sr.RequestError as e:
        print("Błąd usługi rozpoznawania mowy: {0}".format(e))
        return None, None

def listen_for_question(recognizer, microphone):
    with microphone as source:
        print("Proszę, zadaj pytanie...")
        audio = recognizer.listen(source)
        recognizer.pause_threshold = 1.5  # 1.5 seconds of silence threshold
    try:
        question = recognizer.recognize_google(audio, language="pl-PL")
        print("Twoje pytanie:", question)
        return question
    except sr.UnknownValueError:
        print("Nie zrozumiałem pytania.")
        speak_text("Nie zrozumiałem pytania")
        return None
    except sr.RequestError as e:
        print("Błąd usługi rozpoznawania mowy: {0}".format(e))
        speak_text("Błąd usługi rozpoznawania mowy")
        return None

def save_log_entry_to_file(entry: dict, log_dir: str = "logs"):
    """
    Saves the log entry to a JSON file.
    The filename is based on the current timestamp.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # Format timestamp as YYYYMMDD_HHMMSS for file naming.
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"chat_{timestamp_str}.json"
    file_path = os.path.join(log_dir, file_name)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False, indent=4)
        print(f"Log zapisany do: {file_path}")
    except Exception as e:
        print("Błąd przy zapisywaniu logu:", e)

# -------------------------------
# Main Loop
# -------------------------------
while True:
    try:
        # Listen for a trigger phrase.
        trigger, _ = listen_for_trigger(recognizer, microphone)
        if trigger is None:
            print("Brak rozpoznanego wywołania. Ignoruję i ponawiam nasłuchiwanie.")
            time.sleep(0.1)
            continue

        # Respond based on trigger.
        if trigger == "greeting":
            print("Wykryto powitanie. Odpowiadam.")
            play_greeting()
        elif trigger == "question_trigger":
            print("Wykryto 'Mam pytanie' lub 'pytanie'. Odpowiadam.")
            play_question_trigger()

        # Listen for the follow-up question.
        question = listen_for_question(recognizer, microphone)
        if not question:
            print("Brak pytania. Ignoruję i ponawiam nasłuchiwanie.")
            time.sleep(0.1)
            continue

        # If the recognized text is only a trigger word, ignore it.
        if question.lower().strip() in ["witaj", "cześć", "mam pytanie", "pytanie"]:
            print("Rozpoznany tekst to tylko trigger. Ignoruję i ponawiam nasłuchiwanie.")
            time.sleep(0.5)
            continue

        # Valid question captured.
        print("Rozpoznano prawidłowe pytanie:", question)

        # Play a random prompt MP3 file AFTER the question is captured,
        # before generating and reading out the answer.
        play_random_prompt()

        # Pass the valid question to your FAISS-based RAG system.
        response_details = art_expert_chat.get_response(
            user_query=question,
            conversation_history=[],  # No conversation history; each question is standalone.
            temperature=0.7
        )
        assistant_response = response_details["assistant_response"]
        print("Odpowiedź asystenta:", assistant_response)

        # Read the answer out loud using ElevenLabs TTS.
        speak_text(assistant_response)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input": question,
            "chosen_style": art_expert_chat.base_system_prompt,
            "response": assistant_response
        }
        # Save the log entry to a file (each Q/A pair is a separate JSON file).
        save_log_entry_to_file(log_entry)
        print(json.dumps(log_entry, ensure_ascii=False, indent=4) + "\n")
        
        time.sleep(0.1)
        print("Ponowne nasłuchiwanie wywołania...")
    except Exception as e:
        print("Błąd", e)
