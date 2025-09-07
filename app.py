import streamlit as st
import google.generativeai as genai
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.title("📄 Iron Lady Chatbot")
st.write("Ask a question about Iron Lady based on the provided document.")

# --- API Key Configuration ---
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    st.info("Please set the GOOGLE_API_KEY environment variable to begin.")
    st.stop()

# --- Knowledge Base (Chunked) ---
document_chunks = [
    "Mission: Enabling A Million Women to Reach the Top through leadership programs focused on confidence, leadership, and breaking bias.",
    "Founders: Rajesh Bhat – Founder & Director; entrepreneur, TEDx speaker in a saree. Suvarna Hegde – Cofounder & CEO; former Infosys, Bosch, Philips. Creator of Business War Tactics for Women.",
    "Programs Offered: Master of Business Warfare – Advanced leadership program using tactical business strategies. Leadership Essentials Program – Core leadership development for aspiring women leaders. Business War Tactics Masterclass – Live, 2-day intensive workshops that focus on bias-breaking, career acceleration, and promotions.",
    "Impact: 78,000+ women trained. 1,200+ workshops conducted. 100+ women have reached ₹1 Crore+ annual income.",
    "Book: 'The Shameless Lady' by Rajesh Bhat & Suvarna Hegde – Leadership manifesto with stories and strategies.",
    "Events: 'Walk to the Board' – leadership-focused walkathon with Rajesh Bhat and Madan Padaki.",
    "Community: Active on Facebook, Instagram, and events.",
    "Success Story: Minal Bhagat – Built a ₹30 Crore business in 3 years after the Iron Lady programs.",
    "FAQ Context: What programs does Iron Lady offer? Master of Business Warfare, Leadership Essentials Program, Business War Tactics Masterclass. Program duration? Business War Tactics Masterclass: 2 days. Other programs vary from weeks to months. Is the program online or offline? Programs are primarily online; some events offline. Are certificates provided? Yes, certificates are provided. Mentors/coaches? Rajesh Bhat, Suvarna Hegde, plus guest industry mentors."
]

# --- RAG Functions ---
@st.cache_resource
def get_embeddings_and_chunks():
    """Generates embeddings for all document chunks."""
    embeddings = []
    for chunk in document_chunks:
        response = genai.embed_content(
            model="models/embedding-001",
            content=chunk
        )
        embeddings.append(np.array(response['embedding']))
    return embeddings, document_chunks

def retrieve_context(query, embeddings, chunks, top_k=3):
    """Retrieve top_k chunks most relevant to the query."""
    query_embedding_response = genai.embed_content(
        model="models/embedding-001",
        content=query
    )
    query_embedding = np.array(query_embedding_response['embedding']).reshape(1, -1)
    similarities = cosine_similarity(query_embedding, np.array(embeddings))
    top_indices = np.argsort(similarities[0])[-top_k:][::-1]
    combined_context = "\n\n".join([chunks[i] for i in top_indices])
    return combined_context

def generate_response(query, context):
    """Generate answer using Gemini model."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
You are an expert on the provided text.
Use the following context to answer the user's question.
Always answer using only the information in the context.

Context:
{context}

Question: {query}

Answer:"""
    response = model.generate_content(prompt)
    return response.text

# --- Streamlit Chat UI ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Ask me anything about Iron Lady."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if query := st.chat_input("Ask a question about Iron Lady"):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            embeddings, chunks = get_embeddings_and_chunks()
            context = retrieve_context(query, embeddings, chunks)
            response = generate_response(query, context)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
