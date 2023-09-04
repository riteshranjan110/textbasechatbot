from textbase import bot, Message
from textbase.models import OpenAI
from typing import List

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib
import re 

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.vectorstores import FAISS
import tempfile
import os 
import constants

# Load your OpenAI API key
OpenAI.api_key = "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"

os.environ["OPENAI_API_KEY"] = "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"

# Prompt for GPT-3.5 Turbo
SYSTEM_PROMPT = """You are chatting with an AI. There are no specific prefixes for responses, so you can ask or talk about anything you like.
The AI will respond in a natural, conversational manner. Feel free to start the conversation with any question or topic, and let's have a
pleasant chat!
"""

## Loading the dataset. We will load all the dataset while loaing the API itself.
loader = CSVLoader(file_path=constants.PATH+"\\all_college_rank_list.csv",encoding="utf-8", csv_args={'delimiter': ','})
data = loader.load()
#print(data)

embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(data, embeddings)

chain = ConversationalRetrievalChain.from_llm(
llm = ChatOpenAI(temperature=0.0,model_name='gpt-3.5-turbo'),
retriever=vectorstore.as_retriever())

chat_history = []
message_mail_history = []
def get_response(query, message_history):
    
    result = chain({"question": query, "chat_history":message_history})
    #print("result = ",result)
    chat_history.append((query, result["answer"]))
    
    return result["answer"]

# regex to validate emai; id.
regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
def validate_email(email):
    if(re.fullmatch(regex, email)):
        return True
    else:
        return False

def send_mail(text,send_flag=False):
    if(send_flag):
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()
        smtp.login('mailautomation110@gmail.com', 'nkswzvceetlvqxro')

        msg = MIMEMultipart()
        subject = "Please find the requested data." 
        msg['Subject'] = subject
        msg.attach(MIMEText(text))

        to = ["riteshk981@gmail.com"]
        smtp.sendmail(from_addr="mailautomation110@gmail.com",
                to_addrs=to, msg=msg.as_string())
        smtp.quit() 
        return "Mail Sent Successfully"
    

@bot()
def on_message(message_history: List[Message], state: dict = None):
    print("mail message history = ", message_mail_history)
    # We have customized the chatbot a bit.
    # We will take the latest query given by the user.
    query = message_history[-1]['content'][0]['value']
    
    # We will check if the user is starting a new conversation with the chatbot.
    # If so we will greet the user and tell them what they cas expect from this chatbot.
    if(query.lower() in ['hi','hello','good morning','good afternoon','good evening','gud mrng','gud noon','gud eve']):
        bot_response = query+""", I am your counselling assistant. 
        I will help you with Colleges In India that offer B.tech in Computer Science. 
        I can assist you in 
        Engineering,
        Medical,
        Management,
        Law,
        Architecture,
        Pharmacy,
        Dental."""
        chat_history.append((query, bot_response))
    elif(query.find(".com")>-1 and query.find("@")>-1 and validate_email(query)):
        query = query.strip()
        is_mail_valid = validate_email(query)
        if(is_mail_valid):
            if(len(message_mail_history)):
                subject = message_mail_history[-1]
                subject = subject.replace("If U want to mail this information the please type 'mail me'.","")
                mess = send_mail(subject, True)
                bot_response = mess
            else:
                bot_response = "please get a result from the bot that u want on ur mail."
        else:
            bot_response = "please give correct email id."
    else:
        # if user asks anything other than greeting we will use our local database to answer.
        # If the chatgpt fails to answer then we will directly use chatgpt.
        bot_response = get_response(query,chat_history)
        # If chatgpt is not able to find the answer in local database the we will directly use chatgpt.
        f1 = bot_response.find("sorry")>-1
        f2 = bot_response.find("don't have")>-1
        if(f1 or f2):
            bot_response =  OpenAI.generate(
                            system_prompt=SYSTEM_PROMPT,
                            message_history=message_history, # Assuming history is the list of user messages
                            model="gpt-3.5-turbo",)
        message_mail_history.append(bot_response)
        bot_response += " If U want to mail this information the please type your email id."


    response = {
        "data": {
            "messages": [
                {
                    "data_type": "STRING",
                    "value": bot_response
                }
            ],
            "state": state
        },
        "errors": [
            {
                "message": ""
            }
        ]
    }

    return {
        "status_code": 200,
        "response": response
    }