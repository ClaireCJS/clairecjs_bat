import os
import re
import sys
import time

DEFAULTMODEL           = "gpt-3.5-turbo"
OPENAI_FAIL_SLEEP_TIME = 21                     #as of 20230428 max requests of 3 per minute, so, 20 seconds each. I don't think that's the best criteria for this video, however, when you get an error from OpenAI, it explicitly says try again in 20 seconds. I think that's the best value to set this variable from. That plus one. However, we attempt to actually read their response and wait how long they say. This is just the fallback value if that fails. And in fact if you are paying, you can get away with a much lower value, but it's still prudent to keep it this high because there may be an infinite loop and you wouldn't want to automatically spend your API access money running a pointless loop! Better to have a few seconds to interrupt things!


    #randomness == temperature == which is a moderate value that balances creativity and coherence. 0.5 is balanced. I think max is 2 which is creative.

def ask_GPT(our_prompt, personality="You are a helpful assistant", additionalContext="", randomness=0.5, max_tokens=100,
            debug = False, debugMore = False):
    """
        A super-easy way to query OpenAI's ChatGPT/GPT entity, assuming you have an API key in your environment.

        Can also set USE_GPT4=1 at the command line, but be careful with those API fees

        answer = ask_GPT("How much would could a woodchuck chuck?")

        can also pass additionalContext, randomness(0-2), and max_tokens
    """
    global OPENAI_FAIL_SLEEP_TIME, DEFAULTMODEL

    import openai

    if os.environ.get('USE_GPT4') == '1': model = "gpt-4"
    model = DEFAULTMODEL
    if debug: print( "       - Default model: " + DEFAULTMODEL + "       -  Using  model: " + model + f"       -      Question: {our_prompt}")

    our_messages = []
    our_messages.append({"role":"system"   , "content": personality      }) if personality       != "" else "pass"
    our_messages.append({"role":"assistant", "content": additionalContext}) if additionalContext != "" else "pass"
    our_messages.append({"role":"user"     , "content": our_prompt       })
    #our_essages.append({"role":"user"     , "content": additional_prompt}) #additional questions may be added like this
    if debug: print(f"       -  Messages obj: {str(our_messages)}"   )

    while True:
        try:
            response = openai.ChatCompletion.create(model=model, max_tokens=max_tokens, messages=our_messages, temperature=randomness)
            if response.choices:
                if debugMore: print(f"       -  Response object: {response.choices[0]}")
                answer = response.choices[0].message['content']
            else:
                answer = "<<<<< AI ANSWER RETRIEVAL FAILURE [AARF1] >>>>>"
            if debug:
                debugAnswer = answer
                if response: debugAnswer=answer + " // " + repr(response)
                if debugMore: print("*** Answer: ***\n" + debugAnswer)
            return answer
        except Exception as ex:
            exstr = repr(ex)
            print(f"\n\n*********** OpenAI call Error: ***********\n\n{exstr}\n\n")
            match = re.search(r"try again in (\d+)s", exstr)                              #obey how long OpenAI's error message says to wait
            wait_time = int(match.group(1)) if match else OPENAI_FAIL_SLEEP_TIME;
            print(F"...Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

#print(ask_GPT("What is the future of OpenAI's GPT AI?"))
