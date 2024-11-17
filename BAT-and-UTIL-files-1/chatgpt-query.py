#!python3

import os
import sys
import openai


DEFAULTMODEL = "gpt-3.5-turbo"
model = DEFAULTMODEL
if os.environ.get('USE_GPT4') == '1': model = "gpt-4"



if len(sys.argv) < 2:
    print("Usage: python chatgpt-query.py <question>")
    sys.exit(1)


print("       - Default model: " + DEFAULTMODEL)
print("       - Current model: " + model       )

question = ' '.join(sys.argv[1:])



messages=[{"role":"system"    , "content":"You are a helpful assistant."},
#         {"role":"assistant" , "content":"Fans can't tell if it's an act ot real."},
          {"role":"user"      , "content": question},
#	      {"role":"user"      , "content":"Have any notable music critics discussed this topic before?"}
]

#print ("* messages object: " +str(messages))

response = openai.ChatCompletion.create(
	model=model,
    messages=messages,
	temperature=0.5,	    #:e degree of randomness and creativity in the generated text. Higher temperature values lead to more diverse and surprising outputs, while lower values lead to more predictable and conservative outputs. In this case, the temperature is set to 0.5, which is a moderate value that balances creativity and coherence.
	max_tokens=1000,		#maximum number of tokens (words or subwords) to generate in the text output. This parameter limits the length of the generated text and ensures that it remains focused on the task at hand. In this case, the maximum token count is set to 100, which is a reasonable limit for generating short and informative answers to user queries.
)

#print(response)

if os.environ.get('GPT_ANSWER_ONLY') != '1':
    print("\n* Model: " + model + "\n")
    print(f"\n*** Question: ***\n\n{question}\n\n\n\n")
    print("*** Answer: ***\n")

print(response.choices[0].message.content)



