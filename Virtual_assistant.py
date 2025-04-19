import ctypes
import speech_recognition as sr
import webbrowser
import pyttsx3
import pyautogui as m
import os
import google.generativeai as genai
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 6)
music = {"MUSIC NAME":"MUSIC URL"}
website = {"WEBSITE NAME","WEBSITE URL"}
recognizer = sr.Recognizer()
engine = pyttsx3.init() 
voices = engine.getProperty('voices')
engine.setProperty('rate',125)
engine.setProperty('voice', voices[1].id)
def speak(text):
    engine.say(text)
    engine.runAndWait()
def processCommand(c):
    if c.lower().startswith("open"):
        web = c.lower().replace("open " , "")
        link = website[web]
        speak(f"Opening {web}")
        webbrowser.open(link)
    elif c.lower().startswith("play"):
        song = c.lower().replace("play " , "")
        link = music[song]
        speak(f"Playing {song}")
        webbrowser.open(link)
    elif (c.lower().startswith("in youtube search")):
        search = c.lower().replace("in youtube search ","").replace(" ","+")
        speak(f"searching {search}")
        webbrowser.open(f"https://youtube.com/results?search_query={search}")
    elif (c.lower().startswith("search")):
        search = c.lower().replace("search ","").replace(" ","+")
        speak(f"searching {search}")
        webbrowser.open(f"https://www.google.com/search?q={search}")
    elif (c.lower().startswith("type")):
        text_type = c.lower().replace("type ","")
        m.typewrite(f'{text_type}', interval=0.1)
    elif (c.lower().startswith("press")):
        if " " in c :
            key = c.lower().replace("press ","")
            key1 = key[-1]
            key2 = key.replace(f" {key1}","")
            m.hotkey(f'{key2}',f'{key1}')
        else:
            key = c.lower().replace("press ","")
            m.hotkey(f'{key}')
    elif (c.lower() == "exit"):
            speak("Thanks for using Jarvis , Have a good day " , "Exiting")
    else:
        GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
        genai.configure(api_key="YOU'R API") 
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(f"Answer this in paragraph at least 70 words : {c}")
        print(response.text)
        speak(response.text)
if __name__ == "__main__":
    speak("Initializing Jarvis....")
    while True:
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                audio = r.listen(source)
            word = r.recognize_google(audio)
            if(word.lower().startswith("jarvis")):
                command = word.lower().replace("jarvis ","")
                processCommand(command)
        except Exception as e:
            print("",end="")
