import os
import ast
import textwrap
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai

# =====================================================
# 1. CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="OpenSource Navigator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv(Path(__file__).resolve().parent / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = "gemma-4-26b-a4b-it"

GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json"
}


# =====================================================
# 2. HTML RENDER HELPER
# =====================================================

def render_html(content):
    st.markdown(
        textwrap.dedent(content).strip(),
        unsafe_allow_html=True
    )


# =====================================================
# 3. CLOUD BLUE CSS THEME
# =====================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #F2F8FF;
    color: #243B53;
}

[data-testid="stHeader"] {
    background: #F2F8FF;
}

[data-testid="stSidebar"] {
    background: #E3F0FF;
    border-right: 1px solid #C5DCF5;
}

[data-testid="stSidebar"] * {
    color: #24476B;
}

.hero {
    padding: 32px;
    border-radius: 20px;
    background: linear-gradient(120deg, #DCEEFF, #C5E1FF);
    border: 1px solid #B5D5F5;
    margin-bottom: 25px;
}

.hero h1 {
    color: #24476B;
    font-size: 36px;
    font-weight: 800;
    margin: 0 0 12px 0;
}

.hero h2 {
    color: #24476B;
    font-weight: 800;
}

.hero p {
    color: #466987;
    font-size: 15px;
    line-height: 1.7;
}

.section-title {
    font-size: 21px;
    font-weight: 700;
    color: #24476B;
    margin: 22px 0 14px 0;
}

.metric-card {
    background: #FFFFFF;
    border: 1px solid #D4E5F7;
    border-radius: 15px;
    padding: 20px;
    min-height: 110px;
    box-shadow: 0 3px 12px rgba(49,95,145,0.06);
}

.metric-label {
    color: #66829D;
    font-size: 13px;
}

.metric-value {
    color: #24476B;
    font-size: 27px;
    font-weight: 800;
    margin-top: 7px;
}

.info-card {
    background: #FFFFFF;
    border: 1px solid #D4E5F7;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 14px;
    color: #36536F;
    box-shadow: 0 3px 12px rgba(49,95,145,0.04);
}

.info-card h3 {
    color: #24476B;
}

.info-card p {
    color: #466987;
    line-height: 1.7;
}

.info-card a {
    color: #3476B5;
    font-weight: 600;
    text-decoration: none;
}

.stButton > button {
    background: #477FB8;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    min-height: 43px;
    transition: 0.2s;
}

.stButton > button:hover {
    background: #315F91;
    color: white;
    border: none;
}

div[data-testid="stTextInput"] input {
    background: #FFFFFF;
    color: #243B53;
    border: 1px solid #B9D2EC;
    border-radius: 10px;
}

div[data-testid="stTextInput"] label {
    color: #315F91;
    font-weight: 600;
}

.stMarkdown p, .stMarkdown li {
    color: #36536F;
}

[data-testid="stCodeBlock"] {
    background: #FFFFFF;
    border: 1px solid #D4E5F7;
    border-radius: 10px;
}

[data-testid="stAlert"] {
    border-radius: 10px;
}

footer {
    visibility: hidden;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 4. SESSION STATE
# =====================================================

defaults = {
    "repo": None,
    "tree": [],
    "selected_file": None,
    "source_code": "",
    "ai_explanation": "",
    "ai_answer": "",
    "ai_roadmap": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# 5. GITHUB FUNCTIONS
# =====================================================

@st.cache_data(ttl=300)
def get_repo_data(owner, repo):

    repo_url = f"https://api.github.com/repos/{owner}/{repo}"

    response = requests.get(
        repo_url,
        headers=GITHUB_HEADERS,
        timeout=20
    )

    response.raise_for_status()

    metadata = response.json()

    branch = metadata["default_branch"]

    tree_url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/git/trees/{branch}?recursive=1"
    )

    tree_response = requests.get(
        tree_url,
        headers=GITHUB_HEADERS,
        timeout=30
    )

    tree_response.raise_for_status()

    tree_data = tree_response.json()

    return metadata, tree_data.get("tree", [])


def parse_github_url(url):

    url = url.strip().rstrip("/")

    if url.endswith(".git"):
        url = url[:-4]

    if "github.com/" not in url:
        raise ValueError("Please enter a valid GitHub repository URL.")

    parts = url.split("github.com/")[-1].split("/")

    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("Invalid GitHub repository URL.")

    return parts[0], parts[1]


def get_file_content(owner, repo, branch, path):

    url = (
        f"https://raw.githubusercontent.com/"
        f"{owner}/{repo}/{branch}/{path}"
    )

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    return response.text


# =====================================================
# 6. GRAPHIFY - PYTHON DEPENDENCY ANALYSIS
# =====================================================

@st.cache_data(ttl=300, show_spinner=False)
def analyze_python_dependencies(owner, repo, branch, python_paths):
    """Build a static, repository-local Python import graph."""

    paths = list(python_paths)[:40]
    path_to_module = {}

    for path in paths:
        if path.endswith('.py'):
            module = path[:-3].replace('/', '.')
            if module.endswith('.__init__'):
                module = module[:-9]
            path_to_module[module] = path

    known_modules = set(path_to_module)
    nodes = set(path_to_module.keys())
    edges = set()
    parse_errors = []

    for path in paths:
        module_name = path[:-3].replace('/', '.')
        if module_name.endswith('.__init__'):
            module_name = module_name[:-9]

        raw_url = (
            f"https://raw.githubusercontent.com/"
            f"{owner}/{repo}/{branch}/{path}"
        )

        try:
            response = requests.get(raw_url, timeout=12)
            response.raise_for_status()
            source = response.text

            if len(source) > 250_000:
                continue

            tree = ast.parse(source, filename=path)

        except (requests.RequestException, SyntaxError, UnicodeError):
            parse_errors.append(path)
            continue

        imported_names = set()

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:
                    imported_names.add(alias.name)

            elif isinstance(node, ast.ImportFrom):

                base = node.module or ''

                if node.level:

                    package = module_name.split('.')[:-1]

                    if path.endswith('/__init__.py'):
                        package = module_name.split('.')

                    trim = max(0, node.level - 1)

                    if trim:
                        package = package[:-trim]

                    base = '.'.join(
                        package + ([base] if base else [])
                    )

                if base:
                    imported_names.add(base)

                for alias in node.names:

                    if alias.name != '*':
                        imported_names.add(
                            '.'.join(
                                part for part in [base, alias.name]
                                if part
                            )
                        )

        for imported in imported_names:

            candidates = [imported]
            parts = imported.split('.')

            candidates.extend(
                '.'.join(parts[:i])
                for i in range(len(parts) - 1, 0, -1)
            )

            for candidate in candidates:

                if candidate in known_modules and candidate != module_name:
                    edges.add((module_name, candidate))
                    break

    return sorted(nodes), sorted(edges), parse_errors


def make_graphviz_source(nodes, edges):
    """Create safe DOT source with stable generated node identifiers."""

    import json

    ids = {
        name: f"node_{index}"
        for index, name in enumerate(nodes)
    }

    lines = [
        'digraph RepositoryDependencies {',
        'graph [rankdir=LR, bgcolor="transparent", pad="0.25", nodesep="0.45", ranksep="0.7"];',
        'node [shape=box, style="rounded,filled", fillcolor="#E3F0FF", color="#79A9D8", fontcolor="#24476B", fontname="Arial", margin="0.16,0.10"];',
        'edge [color="#6B9BCB", arrowsize="0.7"];'
    ]

    for name in nodes:

        label = name if len(name) <= 42 else name[:39] + '...'

        lines.append(
            f'{ids[name]} [label={json.dumps(label)}];'
        )

    for source, target in edges:

        if source in ids and target in ids:
            lines.append(
                f'{ids[source]} -> {ids[target]};'
            )

    lines.append('}')

    return '\n'.join(lines)


# =====================================================
# 7. GEMMA AI FUNCTION
# =====================================================

def get_ai_response(prompt):

    if not API_KEY:
        return "API key not detected. Check your .env file."

    try:

        client = genai.Client(api_key=API_KEY)

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        return response.text or "No AI response received."

    except Exception as error:

        return f"AI request failed: {str(error)}"
# =====================================================
# 8. SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("# 🚀 OpenSource")
    st.caption("NAVIGATOR")

    st.divider()

    st.markdown("### 🧭 Navigation")
    st.markdown("🏠 Repository Explorer")
    st.markdown("📂 File Browser")
    st.markdown("🤖 Gemma AI Assistant")
    st.markdown("🕸️ Graphify Code Intelligence")

    st.divider()

    st.markdown("### ⚙️ System Status")

    if API_KEY:
        st.success("AI API Connected")
    else:
        st.warning("AI API Not Connected")

    st.divider()

    st.markdown("### 🛠️ Technologies")
    st.markdown("""
    - 🐙 GitHub API
    - ✨ Google Gemma AI
    - 🐍 Python
    - ⚡ Streamlit
    """)

    st.divider()

    st.caption("OpenSource Navigator | 2026")


# =====================================================
# 9. HERO SECTION
# =====================================================

render_html("""
<div class="hero">
    <h1>🚀 OpenSource Navigator</h1>
    <p>
        Your intelligent gateway to exploring open-source projects.
        Understand repositories, explore source code and discover
        contribution opportunities with AI.
    </p>
</div>
""")


# =====================================================
# 10. REPOSITORY INPUT
# =====================================================

render_html("""
<div class="section-title">
    🔍 Explore GitHub Repository
</div>
""")

col1, col2 = st.columns([5, 1])

with col1:

    repo_url = st.text_input(
        "Repository URL",
        placeholder="https://github.com/owner/repository",
        label_visibility="collapsed"
    )

with col2:

    explore = st.button(
        "Explore →",
        use_container_width=True
    )


if explore:

    try:

        owner, repo_name = parse_github_url(repo_url)

        with st.spinner("Connecting to GitHub..."):

            metadata, tree = get_repo_data(owner, repo_name)

        st.session_state.repo = {
            "owner": owner,
            "name": repo_name,
            "metadata": metadata
        }

        st.session_state.tree = tree
        st.session_state.selected_file = None
        st.session_state.source_code = ""
        st.session_state.ai_explanation = ""
        st.session_state.ai_answer = ""
        st.session_state.ai_roadmap = ""
        st.session_state.graphify_nodes = []
        st.session_state.graphify_edges = []
        st.session_state.graphify_errors = []
        st.session_state.graphify_ready = False

        st.success("Repository loaded successfully!")

    except requests.exceptions.HTTPError as error:

        st.error(f"GitHub request failed: {error}")

    except requests.exceptions.RequestException:

        st.error("Network error. Please check your internet connection.")

    except Exception as error:

        st.error(str(error))


# =====================================================
# 11. REPOSITORY DASHBOARD
# =====================================================

if st.session_state.repo:

    repo = st.session_state.repo

    metadata = repo["metadata"]
    owner = repo["owner"]
    repo_name = repo["name"]
    tree = st.session_state.tree

    files = [
        item for item in tree
        if item["type"] == "blob"
    ]

    folders = [
        item for item in tree
        if item["type"] == "tree"
    ]

    # ---------------- METRICS ----------------

    render_html("""
    <div class="section-title">
        📊 Repository Overview
    </div>
    """)

    m1, m2, m3, m4 = st.columns(4)

    metrics = [
        (m1, "⭐ Stars", metadata.get("stargazers_count", 0)),
        (m2, "🍴 Forks", metadata.get("forks_count", 0)),
        (m3, "📄 Files", len(files)),
        (m4, "📁 Folders", len(folders))
    ]

    for column, label, value in metrics:

        with column:

            render_html(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value:,}</div>
            </div>
            """)

    # ---------------- PROJECT DETAILS ----------------

    render_html("""
    <div class="section-title">
        📌 Project Details
    </div>
    """)

    description = metadata.get("description") or "No description available."
    language_name = metadata.get("language") or "Not specified"
    github_url = metadata.get("html_url", "#")

    render_html(f"""
    <div class="info-card">
        <h3>📦 {metadata.get("full_name", repo_name)}</h3>
        <p>{description}</p>
        <p>💻 Primary Language: <b>{language_name}</b></p>
        <p>🌐 Visibility: Public</p>
        <a href="{github_url}" target="_blank">
            View GitHub Repository ↗
        </a>
    </div>
    """)

    # ---------------- FILE EXPLORER ----------------

    render_html("""
    <div class="section-title">
        📂 Repository File Explorer
    </div>
    """)

    search_file = st.text_input(
        "Search repository files",
        placeholder="Type a filename or folder..."
    )

    filtered_files = [
        item for item in files
        if search_file.lower() in item["path"].lower()
    ]

    file_col, code_col = st.columns([1, 2])

    with file_col:

        st.markdown("### 📁 Files")
        st.caption(f"{len(filtered_files)} matching files")

        for item in filtered_files[:150]:

            if st.button(
                f"📄 {item['path']}",
                key=f"file_{item['path']}",
                use_container_width=True
            ):

                st.session_state.selected_file = item["path"]
                st.session_state.source_code = ""

    with code_col:

        st.markdown("### 💻 Source Code")

        selected = st.session_state.selected_file

        if selected:

            st.caption(f"Selected: {selected}")

            if st.button("Load Source Code", key="load_source"):

                try:

                    with st.spinner("Loading source code..."):

                        content = get_file_content(
                            owner,
                            repo_name,
                            metadata["default_branch"],
                            selected
                        )

                    st.session_state.source_code = content

                except Exception as error:

                    st.error(f"Unable to load file: {error}")

            if st.session_state.source_code:

                extension = selected.split(".")[-1].lower()

                language_map = {
                    "py": "python",
                    "js": "javascript",
                    "jsx": "jsx",
                    "ts": "typescript",
                    "tsx": "tsx",
                    "html": "html",
                    "css": "css",
                    "json": "json",
                    "md": "markdown",
                    "java": "java",
                    "cpp": "cpp",
                    "c": "c",
                    "sql": "sql",
                    "yaml": "yaml"
                }

                language = language_map.get(extension, "text")

                st.code(
                    st.session_state.source_code,
                    language=language
                )

        else:

            st.info(
                "Select a file from the left panel to view its source code."
            )

    # =================================================
    # 12. GRAPHIFY - CODE INTELLIGENCE
    # =================================================

    st.divider()

    render_html("""
    <div class="hero">
        <h2>🕸️ Graphify — Code Intelligence</h2>
        <p>
            Visualize how Python modules inside this repository
            depend on one another.
        </p>
    </div>
    """)

    python_files = [
        item["path"] for item in files
        if item["path"].endswith(".py")
    ]

    st.caption(
        "Graphify performs static Python import analysis. "
        "It maps repository-local imports; it does not execute the project."
    )

    if not python_files:

        st.info(
            "No Python files were found in this repository. "
            "Graphify currently supports Python import maps."
        )

    else:

        st.write(
            f"Found **{len(python_files)}** Python files. "
            "The analysis scans up to 40 files per run."
        )

        if st.button(
            "🕸️ Generate Dependency Graph",
            key="generate_graphify",
            use_container_width=True
        ):

            with st.spinner("Graphify is analysing Python imports..."):

                try:

                    graph_nodes, graph_edges, graph_errors = (
                        analyze_python_dependencies(
                            owner,
                            repo_name,
                            metadata["default_branch"],
                            python_files
                        )
                    )

                    st.session_state.graphify_nodes = graph_nodes
                    st.session_state.graphify_edges = graph_edges
                    st.session_state.graphify_errors = graph_errors
                    st.session_state.graphify_ready = True

                except Exception as error:

                    st.error(
                        f"Graphify could not analyse this repository: {error}"
                    )

        if st.session_state.get("graphify_ready", False):

            graph_nodes = st.session_state.get("graphify_nodes", [])
            graph_edges = st.session_state.get("graphify_edges", [])
            graph_errors = st.session_state.get("graphify_errors", [])

            g1, g2, g3 = st.columns(3)

            g1.metric("Python modules", len(graph_nodes))
            g2.metric("Internal connections", len(graph_edges))
            g3.metric("Files skipped / parse errors", len(graph_errors))

            if graph_edges:

                st.graphviz_chart(
                    make_graphviz_source(graph_nodes, graph_edges),
                    use_container_width=True
                )

                selected_module = st.selectbox(
                    "Inspect a module",
                    graph_nodes,
                    key="graphify_selected_module"
                )

                outgoing = [
                    target
                    for source, target in graph_edges
                    if source == selected_module
                ]

                incoming = [
                    source
                    for source, target in graph_edges
                    if target == selected_module
                ]

                left, right = st.columns(2)

                with left:

                    st.markdown("**Imports these local modules**")

                    if outgoing:

                        for name in outgoing:
                            st.write(f"→ `{name}`")

                    else:

                        st.caption("No local imports detected.")

                with right:

                    st.markdown("**Imported by these modules**")

                    if incoming:

                        for name in incoming:
                            st.write(f"← `{name}`")

                    else:

                        st.caption("No incoming local imports detected.")

            else:

                st.info(
                    "No repository-local Python import connections "
                    "were detected. The repository may use another "
                    "language or external packages only."
                )

            if graph_errors:

                with st.expander("Files that could not be analysed"):

                    for path in graph_errors:
                        st.write(f"- `{path}`")
    # =================================================
    # 13. GEMMA AI ASSISTANT
    # =================================================

    st.divider()

    render_html("""
    <div class="hero">
        <h2>✨ Gemma AI Repository Assistant</h2>
        <p>
            Understand codebases, discover important files
            and get intelligent contribution suggestions.
        </p>
    </div>
    """)

    ai_col1, ai_col2 = st.columns(2)

    # ---------------- PROJECT EXPLANATION ----------------

    with ai_col1:

        st.markdown("### 🧠 Project Explanation")

        st.write(
            "Generate an AI-powered explanation of this repository."
        )

        if st.button(
            "✨ Generate Project Explanation",
            use_container_width=True
        ):

            prompt = f"""
            Analyze this GitHub repository using only the information below.

            Repository: {metadata.get('full_name')}
            Description: {description}
            Primary language: {language_name}

            Important files:
            {[item['path'] for item in files[:60]]}

            Explain:

            1. Main purpose of the project.
            2. Technologies used.
            3. Important files and their likely roles.
            4. How a beginner can understand this project.
            5. Three possible contribution ideas.

            Do not claim to have inspected source code
            that was not provided.

            Use simple, clear English.
            """

            with st.spinner("Gemma AI is analyzing the project..."):

                result = get_ai_response(prompt)

            st.session_state.ai_explanation = result

        if st.session_state.ai_explanation:

            st.markdown("#### AI Analysis")
            st.markdown(st.session_state.ai_explanation)

    # ---------------- ASK GEMMA ----------------

    with ai_col2:

        st.markdown("### 💬 Ask Gemma")

        question = st.text_input(
            "Your question",
            placeholder="Which files should I understand first?",
            key="gemma_question"
        )

        if st.button(
            "Ask Gemma →",
            use_container_width=True
        ):

            if question.strip():

                prompt = f"""
                You are an open-source codebase assistant.

                Repository: {metadata.get('full_name')}
                Description: {description}
                Language: {language_name}

                Available files:
                {[item['path'] for item in files[:60]]}

                Selected file:
                {st.session_state.selected_file}

                Source code:
                {st.session_state.source_code[:10000]}

                User question:
                {question}

                Answer in simple and clear language.
                Do not invent details about unseen source code.
                """

                with st.spinner("Gemma is thinking..."):

                    answer = get_ai_response(prompt)

                st.session_state.ai_answer = answer

            else:

                st.warning("Please enter a question.")

        if st.session_state.ai_answer:

            st.markdown("#### 🤖 Gemma's Answer")
            st.markdown(st.session_state.ai_answer)

    # =================================================
    # 14. AI CONTRIBUTION ROADMAP
    # =================================================

    st.divider()

    render_html("""
    <div class="hero">
        <h2>🧭 Your Open Source Contribution Roadmap</h2>
        <p>
            Get a personalized, step-by-step learning and contribution
            plan based on the repository you selected.
        </p>
    </div>
    """)

    st.markdown("### Choose your experience level")

    skill_level = st.selectbox(
        "Your current level",
        ["Beginner", "Intermediate", "Advanced"],
        key="roadmap_skill_level",
        help="Gemma will adjust the roadmap to your selected experience level."
    )

    roadmap_focus = st.selectbox(
        "What would you like to focus on?",
        [
            "Getting started with this project",
            "Understanding the codebase",
            "Finding a first contribution",
            "Improving my technical skills"
        ],
        key="roadmap_focus"
    )

    if st.button(
        "✨ Generate My Contribution Roadmap",
        use_container_width=True
    ):

        roadmap_prompt = f"""
        You are an open-source contribution mentor.

        Create a practical, repository-specific roadmap using only the
        repository information supplied below. Be honest about what is
        known and unknown. Do not claim that an issue is open or suitable
        unless live issue data has been supplied.

        REPOSITORY DETAILS
        Name: {metadata.get('full_name')}
        Description: {description}
        Primary language: {language_name}
        Default branch: {metadata.get('default_branch')}
        Repository URL: {github_url}

        AVAILABLE FILES (sample):
        {[item['path'] for item in files[:100]]}

        USER PROFILE
        Experience level: {skill_level}
        Main goal: {roadmap_focus}

        Write the roadmap in clear Markdown with these sections:

        1. Project in simple words
        2. Skills and concepts to learn first
        3. Important files/folders to explore, with reasons
        4. A step-by-step contribution preparation plan
        5. Three realistic contribution ideas appropriate to this level
        6. How to prepare, test, and submit a contribution safely
        7. A short checklist for the user's next actions

        Tailor the difficulty to the selected experience level:
        - Beginner: explain terms simply and start with documentation,
          setup, tests, and small fixes.
        - Intermediate: include code navigation, tests, debugging,
          and focused feature or bug-fix work.
        - Advanced: include architecture investigation, test strategy,
          performance, maintainability, and larger scoped contributions.

        Do not invent exact functions, file contents, bugs, or project
        conventions that cannot be confirmed from the supplied file list
        and metadata. Label suggestions as ideas to investigate, not
        confirmed issues. Keep the plan achievable and actionable.
        """

        with st.spinner("Gemma is building your personalized roadmap..."):

            st.session_state.ai_roadmap = get_ai_response(roadmap_prompt)

    if st.session_state.ai_roadmap:

        st.markdown("### 🎯 Your Personalized Roadmap")
        st.markdown(st.session_state.ai_roadmap)


# =====================================================
# 15. WELCOME SCREEN
# =====================================================

else:

    render_html("""
    <div class="info-card">
        <h3>👋 Welcome to OpenSource Navigator!</h3>
        <p>
            Start by entering a public GitHub repository URL above.
        </p>
        <p>🔍 Explore repositories</p>
        <p>📂 Understand project structure</p>
        <p>💻 View source code</p>
        <p>🕸️ Visualize Python module dependencies with Graphify</p>
        <p>✨ Get AI-powered project explanations</p>
        <p>🧭 Generate your contribution roadmap</p>
    </div>
    """)

    st.markdown("### 💡 Try a sample repository")

    st.code("https://github.com/psf/requests")


# =====================================================
# 16. FOOTER
# =====================================================

st.divider()

render_html("""
<div style="
    text-align:center;
    color:#66829D;
    padding:20px;
">
    <b>🚀 OpenSource Navigator</b>
    <p>Explore. Understand. Contribute.</p>
    <small>Built for the Open Source Community | 2026</small>
</div>
""")