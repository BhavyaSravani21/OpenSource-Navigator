# 🚀 OpenSource Navigator
### AI-Powered GitHub Repository Explorer & Code Intelligence Platform

**Understand any public GitHub repository. Explore its code. Discover how to contribute — all in one place.**

OpenSource Navigator is an AI-powered platform designed to help developers, especially beginners, understand unfamiliar GitHub repositories and find a clear path to their first open-source contribution.

Instead of manually exploring hundreds of files, users can enter a public GitHub repository URL and explore its structure, understand important source files, visualize Python dependencies, and generate a personalized contribution roadmap.

---

## ✨ Why OpenSource Navigator?

Getting started with open-source development can be challenging. Beginners often struggle to understand large codebases, identify important files, learn unfamiliar technologies, and decide where to contribute.

**OpenSource Navigator simplifies this journey** by combining repository exploration, AI-powered explanations, code intelligence, and contribution guidance in one platform.

## 🌟 Key Features

### 1. 🔍 GitHub Repository Explorer
- Enter a public GitHub repository URL.
- Fetch repository information and metadata.
- Explore the complete file and folder structure.
- View repository statistics, including stars and forks.
- Search for files and folders.

### 2. 🤖 AI-Powered Repository Understanding
- Understand the purpose of a repository.
- Identify technologies and frameworks used.
- Discover important files and their roles.
- Get beginner-friendly explanations of complex projects.
- Ask questions about the repository and receive AI-generated answers.

### 3. 🗺️ AI Contribution Roadmap
Generate a repository-based learning and contribution roadmap with three difficulty levels:

- **Beginner:** Understand the project and identify simple contribution opportunities.
- **Intermediate:** Explore implementation details and work on more involved improvements.
- **Advanced:** Investigate deeper technical challenges and potential enhancements.

The roadmap includes relevant skills, files to explore, contribution ideas, and actionable checklists.

### 4. 📊 Graphify – Code Intelligence
Explore Python module dependencies through an interactive graph.

- Analyze Python imports using AST.
- Visualize relationships between modules.
- Identify incoming and outgoing dependencies.
- Select a module to inspect its connections.

*Note: Graphify performs static Python import analysis; it does not represent runtime execution flow.*

### 5. 💡 Beginner-Friendly Experience
- Simple repository exploration workflow.
- Organized code viewing.
- AI-powered guidance.
- Structured learning and contribution suggestions.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Streamlit | Interactive web interface |
| GitHub REST API | Repository information and file access |
| Google Gemini API (Gemma) | AI-powered explanations and guidance |
| Requests | API communication |
| Python AST | Static import dependency analysis |

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.10 or later
- Git
- GitHub account
- Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/BhavyaSravani21/OpenSource-Navigator.git
```

### 2. Navigate to the project folder

```bash
cd OpenSource-Navigator
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GITHUB_TOKEN=your_github_token
```

Add your own API credentials. Never publish your `.env` file or expose your tokens.

### 6. Run the application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

---

## 🚀 How It Works

1. Enter a public GitHub repository URL.
2. Open the repository overview and explore its structure.
3. Search for files and inspect source code.
4. Use AI to understand the repository and ask questions.
5. Generate a contribution roadmap based on your selected difficulty level.
6. Use Graphify to explore Python module dependencies.

---

## 🎯 Who Can Benefit?

- Students beginning their open-source journey.
- Beginners exploring unfamiliar codebases.
- Developers looking for repository-level insights.
- Contributors searching for areas to improve.
- Learners who want structured guidance before contributing.

---

## 🔮 Future Enhancements

- Support for additional programming languages in dependency analysis.
- More advanced code relationship visualization.
- Improved contribution recommendations.
- Integration of issue-based contribution suggestions.
- Enhanced repository understanding and code navigation.

---

## 🔐 Security

- API credentials are stored in environment variables.
- `.env` is excluded from Git using `.gitignore`.
- Use tokens with only the minimum permissions required.
- Never commit API keys or access tokens to the repository.

---

## 👩‍💻 Developed By

**D.Bhavya Sravani**

Developed as a project to make open-source exploration and contribution more accessible to beginners.

**GitHub Repository:**  
https://github.com/BhavyaSravani21/OpenSource-Navigator

---

⭐ **If you find this project useful, consider giving it a star!**

*Explore repositories. Understand code. Build your open-source journey.*
