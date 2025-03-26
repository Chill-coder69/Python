import speech_recognition as sr # install by "pip install speech_recognition" 
import webbrowser               # in-build function
import pyttsx3                  # install by "pip install pyttsx3"
engine.property("rate",167)
recognizer = sr.Recognizer()
engine = pyttsx3.init() 
musicLibrary = {"MUSIC NAME":"MUSIC URL",} # HERE ENTER YOUR MUSIC
website = {"WEBSITE NAME":"WEBSITE URL",}  # HERE ENTER YOUR WEBSITE
def speak(text):                     # for speaking
    engine.say(text)
    engine.runAndWait()
def processCommand(c):                                # commands by speech
    if c.lower().startswith("open"):                  # open your enter website
        web = c.lower().replace("open " , "") 
        link = website[web]
        speak(f"opening {web}")
        webbrowser.open(link)
    elif c.lower()=="play" or c.lower()=="pause":
        m.press('space')
    elif c.lower() =="close":
        m.hotkey('ctrl','w')
    elif c.lower().startswith("play"):                 # play your entered music
        song = c.lower().replace("play " , "")
        link = musicLibrary[song]
        speak(f"playing {song}")
        webbrowser.open(link)
    elif c.lower().startswith("in youtube"):                 # search youbube
        g=c.lower().replace("youtube search ", "").strip()
        speak(f"Searching {g}")
        p = c.lower().replace("youtube search ", "").strip().replace(" ", "+")
        webbrowser.open(f"https://www.youtube.com/results?search_query={p}")
    elif c.lower().startswith("search"):                    # search using google
        g= c.lower().replace("search ", "").strip()
        speak(f"Searching {g}")
        p = c.lower().replace("search ", "").strip().replace(" ", "+")
        webbrowser.open(f"https://www.google.com/search?q={p}")
    elif c.lower().startswith("speak "):                 # speak your speech
        f=c.replace("speak " , "")
        speak(f)
    else:
        print(c) # just print your speech
if __name__ == "__main__":
    speak("Initializing your Virtual assistant....")
    while True:          # generate a infinite loop
            # recognise your speech
        r = sr.Recognizer()
        print("recognizing...")
        try:
                 # listen your speech
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=5,phrase_time_limit=1)
                word = r.recognize_google(audio)
            if(word.lower() == "jarvis"):                         # Activate jarvis by wakeword "jarvis"
                speak(f"{word} activated. hey, how may i help you ?")
                with sr.Microphone() as source:
                    print("Jarvis Activated...")
                    audio = r.listen(source)
                    command = r.recognize_google(audio)
                    processCommand(command)
        except Exception as e: # in case a error occur
            print("Error; {0}".format(e))

# In case you want to remove the messege of recognition and listening
# Then just add "#" at start of "print("recognizing...")" and "print("Listening...")"
# In case you want to change the name of the voice assistant type your desired name in place of jarvis in "if(word.lower() == "jarvis"):"
