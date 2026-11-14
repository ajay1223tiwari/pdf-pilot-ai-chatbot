# 🚀 PDF Pilot – Full-Stack GenAI PDF Chatbot

**Chat with your PDF documents using Generative AI and RAG (Retrieval-Augmented Generation).**

PDF Pilot is a full-stack Generative AI application that allows users to upload PDF documents and ask questions about their content. It uses semantic search and Large Language Models (LLMs) to generate context-aware answers based on the uploaded documents.

🌐 **Live Demo:** https://pdf-pilot-ai-chatbot.vercel.app

---

## ✨ Features

- 📄 Upload multiple PDF documents.
- 🤖 Ask questions about uploaded PDFs using AI.
- 🔍 Semantic search for relevant document content.
- 🧠 RAG-based question answering.
- 💬 Chat with individual PDF documents.
- 📚 View and manage uploaded documents.
- 🗑️ Delete uploaded documents.
- 📖 View and download PDF files.
- 💾 Saved chat history.
- ⚡ Multiple LLM providers with fallback support.
- 📱 Responsive user interface.

## 🛠️ Tech Stack

### Frontend
- React.js
- Vite
- JavaScript
- CSS

### Backend
- Python
- FastAPI
- REST APIs
- SQLite

### Generative AI & RAG
- Groq LLM
- Google Gemini
- Sentence Transformers
- FAISS Vector Search
- LangChain Text Splitters
- Retrieval-Augmented Generation (RAG)

### PDF Processing
- PyPDF
- Text Extraction
- Text Chunking
- Semantic Search

### Deployment
- Vercel – Frontend
- Railway – Backend
- GitHub – Version Control

## 🏗️ System Architecture

```text
                 User
                  |
                  v
          React.js Frontend
               (Vercel)
                  |
                  v
             REST API
              (FastAPI)
             (Railway)
                  |
          +-------+-------+
          |               |
          v               v
     PDF Processing   Chat History
          |             (SQLite)
          v
      Text Extraction
          |
          v
       Chunking
          |
          v
  Sentence Transformers
       Embeddings
          |
          v
      FAISS Vector Store
          |
          v
     Semantic Search
          |
          v
       RAG Pipeline
          |
          v
      Groq / Gemini
          |
          v
    AI Generated Answer
```

## 🔄 How It Works

1. User uploads one or more PDF documents.
2. Backend extracts text from the PDFs.
3. Extracted text is divided into smaller chunks.
4. Sentence Transformers convert chunks into embeddings.
5. FAISS stores the embeddings for similarity search.
6. User asks a question about the selected PDF.
7. Relevant document chunks are retrieved using semantic search.
8. Retrieved context is sent to the LLM.
9. Groq or Gemini generates a context-aware response.
10. The answer is displayed in the React frontend.

## 📂 Project Structure

```text
ai-pdf-chatbot/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── text_processor.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── metadata_store.py
│   ├── llm.py
│   └── chat_store.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   └── package.json
│
├── uploads/
├── vector_stores/
├── metadata/
├── requirements.txt
├── .env
└── .gitignore
```

## ⚙️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/ajay1223tiwari/pdf-pilot-ai-chatbot.git
```

```bash
cd ai-pdf-chatbot
```

### 2. Create Python Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory.

```env
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

Replace the placeholder values with your own API keys.

**Important:** Never upload your `.env` file or expose API keys on GitHub.

### 5. Start Backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

Backend API:

```text
http://127.0.0.1:8000
```

API Documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Start Frontend

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start development server:

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| GROQ_API_KEY | Groq API authentication |
| GEMINI_API_KEY | Google Gemini API authentication |
| VITE_API_URL | Backend API URL for frontend |

## 🌐 Live Deployment

| Component | Platform |
|---|---|
| Frontend | Vercel |
| Backend | Railway |
| Source Code | GitHub |

**Live Application:**  
https://pdf-pilot-ai-chatbot.vercel.app

**Backend API:**  
https://pdf-pilot-ai-chatbot-production.up.railway.app

**API Documentation:**  
https://pdf-pilot-ai-chatbot-production.up.railway.app/docs

## 🎯 Key Concepts Demonstrated

- Full-Stack Web Development
- Generative AI
- Retrieval-Augmented Generation (RAG)
- Large Language Models (LLMs)
- Text Embeddings
- Vector Databases
- Semantic Search
- REST API Development
- PDF Document Processing
- Cloud Deployment

## 👨‍💻 Author

**Ajay Tiwari**

B.Tech – Computer Science & Engineering

GitHub: https://github.com/ajay1223tiwari

---

⭐ If you find this project useful, consider giving it a star!

**PDF Pilot – Your Documents, Understood.**
