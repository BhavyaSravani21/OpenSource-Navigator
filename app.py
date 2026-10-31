
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai

# Load API key from the .env file beside app.py
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemma-4-26b-a4b-it"

st.set_page_config(
    page_title="OpenSource Navigator",
    page_icon="🧭",
    layout="wide"
)

# ------------------ HEADER ------------------

st.title("🧭 OpenSource Navigator")

st.subheader("Explore. Understand. Contribute.")

st.write(
    "An AI-powered GitHub repository explorer "
    "that helps beginners understand open-source projects."
)

st.divider()

# ------------------ GITHUB FUNCTIONS ------------------

def get_repository(url):

    parsed = urlparse(url.strip())

    if parsed.netloc.lower() not in ["github.com", "www.github.com"]:
        raise ValueError("Please enter a valid GitHub URL.")

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("Enter a repository URL with owner and name.")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")

    headers = {
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}",
        headers=headers,
        timeout=15
    )

    response.raise_for_status()

    details = response.json()
    branch = details["default_branch"]

    tree_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
        headers=headers,
        timeout=20
    )

    tree_response.raise_for_status()

    tree_data = tree_response.json()

    return details, tree_data.get("tree", []), owner, repo, branch


def get_file_content(owner, repo, branch, file_path):

    raw_url = (
        f"https://raw.githubusercontent.com/"
        f"{owner}/{repo}/{branch}/{file_path}"
    )

    response = requests.get(raw_url, timeout=15)
    response.raise_for_status()

    return response.text


# ------------------ REPOSITORY INPUT ------------------

st.header("🔍 Explore a GitHub Repository")

repo_url = st.text_input(
    "GitHub Repository URL",
    placeholder="https://github.com/psf/requests"
)

if st.button("Explore Repository", type="primary"):

    if not repo_url.strip():
        st.warning("Please enter a GitHub repository URL.")

    else:
        try:
            with st.spinner("Fetching repository information..."):

                details, tree, owner, repo, branch = get_repository(
                    repo_url
                )

                st.session_state["details"] = details
                st.session_state["tree"] = tree
                st.session_state["owner"] = owner
                st.session_state["repo"] = repo
                st.session_state["branch"] = branch

            st.success("Repository loaded successfully!")

        except ValueError as error:
            st.error(str(error))

        except requests.HTTPError as error:
            st.error(
                f"GitHub returned an error: {error}. "
                "Check whether the repository is public."
            )

        except requests.RequestException:
            st.error("Network error. Please try again.")


# ------------------ REPOSITORY DETAILS ------------------

if "details" in st.session_state:

    details = st.session_state["details"]
    tree = st.session_state["tree"]

    owner = st.session_state["owner"]
    repo = st.session_state["repo"]
    branch = st.session_state["branch"]

    st.divider()
    st.header("📌 Repository Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("⭐ Stars", details["stargazers_count"])
    col2.metric("🍴 Forks", details["forks_count"])
    col3.metric("📁 Total Items", len(tree))

    st.write("**Project:**", details["full_name"])

    st.write(
        "**Description:**",
        details.get("description") or "No description available"
    )

    st.write(
        "**Main Language:**",
        details.get("language") or "Not specified"
    )

    st.write("**Default Branch:**", branch)

    st.markdown(
        f"[Open Repository on GitHub]({details['html_url']})"
    )

    # ------------------ FILE STRUCTURE ------------------

    st.divider()
    st.header("📂 Repository Structure")

    folders = [
        item["path"]
        for item in tree
        if item["type"] == "tree"
    ]

    files = [
        item["path"]
        for item in tree
        if item["type"] == "blob"
    ]

    with st.expander("📁 View Folders"):
        for folder in folders[:100]:
            st.write("📁", folder)

    with st.expander("📄 View Files"):
        for file in files[:150]:
            st.write("📄", file)

    # ------------------ SOURCE CODE VIEWER ------------------

    st.divider()
    st.header("💻 Source Code Explorer")

    code_files = [
        item["path"]
        for item in tree
        if item["type"] == "blob"
        and item["path"].endswith(
            (".py", ".js", ".jsx", ".ts", ".tsx",
             ".java", ".html", ".css")
        )
        and item.get("size", 0) < 100000
    ]

    if code_files:

        selected_file = st.selectbox(
            "Select a source file",
            code_files
        )

        if st.button("View Source Code"):

            try:
                content = get_file_content(
                    owner, repo, branch, selected_file
                )

                st.code(
                    content[:20000],
                    language="python"
                )

            except requests.RequestException:
                st.error("Unable to load this file.")

    else:
        st.info("No supported source files found.")

    # ------------------ GEMMA AI ------------------

    st.divider()
    st.header("🤖 Gemma AI Repository Assistant")

    if not API_KEY:

        st.warning(
            "API key not detected. Please check your .env file."
        )

    else:

        st.success("AI API key detected successfully.")

        # Create AI client
        client = genai.Client(api_key=API_KEY)

        # Project explanation
        if st.button("✨ Generate Project Explanation"):

            try:
                repo_info = f"""
                Repository: {details['full_name']}
                Description: {details.get('description')}
                Main Language: {details.get('language')}
                Folders: {folders[:40]}
                Files: {files[:60]}
                """

                with st.spinner("Gemma AI is analyzing the project..."):

                    response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=f"""
                        You are an open-source project guide.

                        Explain this GitHub repository to a beginner.

                        Include:
                        1. Project purpose
                        2. Important files and folders
                        3. Technologies used
                        4. How the project is organized
                        5. Beginner-friendly contribution ideas

                        Use simple and clear language.

                        Repository information:
                        {repo_info}
                        """
                    )

                st.subheader("📖 AI Project Explanation")
                st.markdown(response.text)

            except Exception as error:
                st.error(f"AI request failed: {error}")

        # Ask AI
        st.subheader("💬 Ask Questions About This Project")

        question = st.text_input(
            "Enter your question",
            placeholder="What does this project do?"
        )

        if st.button("Ask Gemma"):

            if not question.strip():

                st.warning("Please enter a question.")

            else:

                try:
                    repo_context = f"""
                    Repository: {details['full_name']}
                    Description: {details.get('description')}
                    Language: {details.get('language')}
                    Folders: {folders[:40]}
                    Files: {files[:60]}
                    """

                    with st.spinner("Gemma is preparing an answer..."):

                        response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=f"""
                            You are a helpful open-source project assistant.

                            Answer the user's question using the
                            repository information below.

                            If the information is insufficient,
                            clearly say so instead of guessing.

                            Repository information:
                            {repo_context}

                            User question:
                            {question}

                            Explain in beginner-friendly language.
                            """
                        )

                    st.subheader("💡 AI Answer")
                    st.markdown(response.text)

                except Exception as error:
                    st.error(f"AI request failed: {error}")


# ------------------ FOOTER ------------------

st.divider()

st.caption(
    "OpenSource Navigator | Built to make open-source contribution easier."
)
