# Company Brochure Q/A Chatbot

This project is a **Streamlit web application** that:
1. Generates a **company brochure** from user-provided input.
2. Provides a **Q&A chatbot** that answers questions strictly based on the generated brochure.

The app uses the **OpenAI API** to generate text, and Streamlit for the interactive UI.

---

## 🚀 Features
- Secure **API Key input** (masked in UI).
- One-click **brochure generation**.
- Interactive **Q&A chatbot** with guardrails:
  - Answers only from the brochure text.
  - If the information isn’t in the brochure, it will say so.
- **Chat history memory**.
- **Streaming answers** (question stays visible while response is generating).
- Input box clears automatically after each question.

---

## 🛠️ Installation

1. Clone the repository:

```bash
git clone https://github.com/<your-username>/brochure-chatbot.git
cd brochure-chatbot
````

2. (Optional but recommended) Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

Run the Streamlit app:

```bash
streamlit run app.py
```

Then open the URL shown in your terminal (usually [http://localhost:8501](http://localhost:8501)).

---

## 🔑 API Key

The app requires an **OpenAI API Key**.
You can generate one from [https://platform.openai.com/](https://platform.openai.com/).

When you open the app:

* Enter your API key in the provided **masked input box**.
* This key is only used for your session (not stored permanently).

---

## 📂 Project Structure

```
brochure-chatbot/
│── app.py               # Main Streamlit app
│── requirements.txt     # Python dependencies
│── README.md            # Project documentation
```

---

## 💡 Example Workflow

1. Enter company details → click **Generate Brochure**.
2. The brochure is displayed.
3. Start asking questions in the chatbot input box.

   * Your questions and answers will be displayed as a conversation.
   * The model will only use the brochure for answers.

---

## 📜 License

MIT License. Feel free to fork and improve!

````

---
