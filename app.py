import streamlit as st
from openai import OpenAI
import requests, json
from bs4 import BeautifulSoup

MODEL = "gpt-5-nano"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36"
}


class Website:
    def __init__(self, url: str):
        self.url = url
        response = requests.get(url, headers=headers)
        body = response.content
        self.soup = BeautifulSoup(body, 'html.parser')
        self.title = self.soup.title.string if self.soup.title else "No title found"
        self.text = self._extract_content(url)
        links = [link.get('href') for link in self.soup.find_all('a')]
        self.links = [link for link in links if link]

    def _extract_content(self, url):
        # --- Try Trafilatura ---
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                extracted = trafilatura.extract(downloaded)
                if extracted:
                    return extracted
        except Exception:
            pass

        # --- Try Newspaper3k ---
        try:
            from newspaper import Article
            article = Article(url)
            article.download()
            article.parse()
            if article.text.strip():
                return article.text
        except Exception:
            pass

        # --- Fallback: BeautifulSoup ---
        try:
            soup = self.soup

            # Remove irrelevant tags
            for irrelevant in soup.body(["script", "style", "img", "input", "footer", "nav", "aside"]):
                irrelevant.decompose()

            # Filter short/noisy paragraphs
            paras = [p.get_text(strip=True) for p in soup.find_all("p")]
            cleaned = [p for p in paras if len(p.split()) > 5]  # keep only meaningful sentences

            return ("\n".join(cleaned))
        except Exception:
            return ("No text extracted")

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"

link_system_prompt = """You are provided with a list of links found on a webpage. 
You are able to decide which of the links would be most relevant to include in a brochure about the company, 
such as links to an About page, or a Company page, or Careers/Jobs pages.
You should respond in JSON as in this example:
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page", "url": "https://another.full.url/careers"}
    ]
}
"""

def get_links_user_prompt(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format. \
Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_links(url, openai):
    website = Website(url)
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)

def get_all_details(url, openai):
    result = "Landing page:\n"
    result += Website(url).get_contents()
    links = get_links(url, openai)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Website(link["url"]).get_contents()
    return result

system_prompt = """You are an assistant that analyzes the contents of several relevant pages from a company website 
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown. 
Include details of company culture, customers and careers/jobs if you have the information."""

def get_brochure_user_prompt(company_name, url, openai):
    all_details = get_all_details(url, openai)
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown.\n"
    user_prompt += all_details
    user_prompt = user_prompt[:5_000]
    return user_prompt, all_details

# -------------------------------
# Streamlit Streaming + Memory
# -------------------------------
st.title("Company Brochure Generator with Q&A")

# Masked API key input
st.sidebar.header("API Tokens")
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
company_name = st.text_input("Enter the company name", placeholder="e.g. HuggingFace")
url = st.text_input("Enter the company website URL", placeholder="https://huggingface.co")

if "brochure_text" not in st.session_state:
    st.session_state.brochure_text = None
if "company_raw_info" not in st.session_state:
    st.session_state.company_raw_info = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if st.button("Generate Brochure"):
    if not api_key:
        st.error("Please enter your API key.")
    elif not company_name or not url:
        st.error("Please enter both company name and website URL.")
    else:
        openai = OpenAI(api_key=api_key)

        def stream_generator():
            user_prompt, all_details = get_brochure_user_prompt(company_name, url, openai)
            stream = openai.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True,
            )
            response = ""
            for chunk in stream:
                if hasattr(chunk.choices[0].delta, "content"):
                    token = chunk.choices[0].delta.content or ""
                    response += token
                    st.write(token, end="")
                    # yield token
            # Save full brochure in memory
            st.session_state.brochure_text = response
            st.session_state.company_raw_info = all_details
        with st.spinner("Fetching details and generating brochure... ⏳"):
            stream_generator()

# -------------------------------
# Follow-up Q&A from memory
# -------------------------------
if st.session_state.brochure_text:
    st.markdown(st.session_state.brochure_text)
    st.subheader("Company Q&A Chatbot")

    # Display past chat
    for turn in st.session_state.chat_history:
        st.markdown(f"**{turn['q']}**")
        st.markdown(f"{turn['a']}")

    # Chat input – auto clears on Enter
    user_q = st.chat_input("Ask a question about the company:")

    if user_q:  # runs only when user submits a new question
        if not api_key:
            st.error("Please enter your API key.")
        else:
            openai = OpenAI(api_key=api_key)

            guardrail_prompt = f"""You are an assistant that answers questions ONLY based on the brochure text provided below.
If the answer is not in the brochure, say that the fetched information does not mention this.
Do not make up facts.

Brochure text:
{st.session_state.company_raw_info}
"""
            # Append question immediately with empty answer placeholder
            st.session_state.chat_history.append({"q": user_q, "a": ""})

            # Display the question immediately
            st.markdown(f"**{user_q}**")

            # Create placeholder for streaming answer
            stream_placeholder = st.empty()
            streamed_answer = ""
            
            # placeholder for streaming output
            with st.spinner("Generating answer..."):
                stream_placeholder = st.empty()
                streamed_answer = ""

                for event in openai.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": guardrail_prompt},
                        {"role": "user", "content": user_q}
                    ],
                    stream=True,
                ):
                    delta = event.choices[0].delta.content if event.choices else None
                    if delta:
                        streamed_answer += delta
                        stream_placeholder.markdown(streamed_answer)

            # Save to chat history
            st.session_state.chat_history[-1]["a"] = streamed_answer

            # Trigger rerun so the new Q&A appears above the input box
            st.rerun()


