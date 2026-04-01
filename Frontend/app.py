import streamlit as st
import requests

st.title("Autonomous Research Agent")

query = st.text_input("Enter your question")

if st.button("Run Agent"):
    response = requests.post(
        "http://127.0.0.1:8000/run-agent",
        json={"query": query}
    )

    #st.write(response.json())
    if response.status_code == 200:
        result = response.json()
        st.subheader("Agent Response")
        st.write(result["response"])
    else:
        st.error("Backend Error:")
        st.write(response.text)
    '''result = response.json()

    st.subheader("Agent Response")
    st.write(result["response"])'''

