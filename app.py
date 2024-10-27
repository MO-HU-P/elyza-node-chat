from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
import logging
from typing import Dict

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# メモリーをセッションごとに管理
sessions: Dict[str, ConversationBufferMemory] = {}

def get_or_create_memory(session_id: str) -> ConversationBufferMemory:
    if session_id not in sessions:
        sessions[session_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return sessions[session_id]

async def generate_response(query: str, session_id: str) -> str:
    try:
        memory = get_or_create_memory(session_id)
        
        llm = ChatOllama(
            model="elyza:jp8b",
            temperature=0,
            timeout=30
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "あなたは誠実で優秀なAIアシスタントです。ユーザーとの会話履歴を考慮しながら、丁寧に日本語で回答してください。"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        chain = prompt | llm
        
        response = await chain.ainvoke({
            "input": query,
            "chat_history": memory.chat_memory.messages
        })
        
        # メモリーに会話を追加
        memory.chat_memory.add_user_message(query)
        memory.chat_memory.add_ai_message(response.content)
        
        return response.content
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"エラーが発生しました: {str(e)}")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="メッセージが空です")
            
        response = await generate_response(request.message, request.session_id)
        return ChatResponse(reply=response)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="サーバーエラーが発生しました")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8501)

