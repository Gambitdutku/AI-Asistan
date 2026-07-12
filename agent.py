import os
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from tools import get_tools

MODEL_NAME = os.getenv("OLLAMA_MODEL")
llm = ChatOllama(model=MODEL_NAME, temperature=0.2)

SYSTEM_PROMPT = (
    "Sen profesyonel, organize ve çözüm odaklı bir sanal asistansın. "
    "Müşteri kayıtlarını ve randevuları yönetmekle sorumlusun. "
    "Sana verilen araçları kullanarak veritabanına veri ekleyebilir ve listeleyebilirsin. "
    "Eğer bir randevu oluşturduktan sonra araçtan 'e-posta adresi bulunamadı' uyarısı alırsan, "
    "kullanıcıya randevunun başarıyla eklendiğini ancak e-posta adresi olmadığı için bildirim gitmediğini söyle "
    "ve 'İsterseniz kendiniz mesaj atabilirsiniz' şeklinde nazikçe uyar."
)

agent_executor = create_agent(
    model=llm,
    tools=get_tools,
    system_prompt=SYSTEM_PROMPT,
)


def get_agent_executor():
    return agent_executor