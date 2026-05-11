from src.connectors.llm import LLM
import random

class BotPersonality():
    def __init__(self, llm_mode = "cpu", llm_model_path = "./models/google_gemma-4-E2B-it-Q4_K_M.gguf"):
        self.llm_mode = llm_mode
        self.llm_model_path = llm_model_path
        self.llm = LLM(mode=self.llm_mode, model_path=llm_model_path)
        self.llm.start()
        self.short_term_memory = []
        self.message_counter = 0
        self.history_length = 25

        self.long_term_memory_path = "./src/personality/long_term_memory.txt"
        self.system_long_term_memory_path = "./src/personality/system_long_term_memory.txt"
        self.system_personality_path = "./src/personality/system_personality.txt"

        with open(self.long_term_memory_path, "r") as f:
            self.long_term_memory = f.read()

        with open(self.system_long_term_memory_path, "r") as f:
            self.system_long_term_memory = f.read()

        with open(self.system_personality_path, "r") as f:
            self.system_personality = f.read()

        self.special_string = ""

    def message_processor(self, message, mode = 0): # mode = 0: Zhart not mentionned, 1: Zhart in text, 2: Zhart tagged 3: from Zhart
        
        clean_message = message.content.lower().strip()
        conv_log = f"{message.channel} | {message.author} | {clean_message}"
        self.short_term_memory.append(conv_log)
        self.message_counter += 1

        while len(self.short_term_memory) > self.history_length:
            del self.short_term_memory[0]

        

        reply = ""
        self.special_string = ""
        reply_decision_threshold = 100
        random_int = random.randint(1, 100)

        match mode:
             case 0:
                  reply_decision_threshold = 3
                  self.special_string = "\nYou are replying unprompted"
             case 1:
                  reply_decision_threshold = 15
                  self.special_string = "\nAs the message log suggests, you were mentioned by name in the conversation"
             case 2:
                  reply_decision_threshold = 100
                  self.special_string = "\nAs the message log suggests, You were directly tagged and are expected to respond"
             case 3:
                  reply_decision_threshold = -1
             case _:
                  pass
            
        if random_int <= reply_decision_threshold:
            if self.message_counter >= self.history_length:
                self.long_term_memory_update()
            reply = self.llm_request(mode = 0)

        return reply


    def long_term_memory_update(self):
        self.message_counter = 0
        self.long_term_memory = self.llm_request(mode = 1)
        with open(self.long_term_memory_path, "w") as f:
            f.write(self.long_term_memory)



    def llm_request(self, mode = 0, ): # mode = 0: zhart, 1: long term memory
        prompt = ""
        system = ""
        message_log = ""

        message_log = "\n".join(self.short_term_memory)
        
        prompt += f"Long term memory file:\n{self.long_term_memory}\n\nChat log:\n{message_log}"

        if mode == 0:
            system = self.system_personality + self.special_string
        elif mode == 1:
            system = self.system_long_term_memory

        reply = self.llm.chat(
                    prompt=prompt,
                    system=system
                )
        print("1=============================")
        print(system)
        print(prompt)
        print(reply)
        print("=============================1")
        return reply