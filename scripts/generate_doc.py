"""Generates Design_details.docx for the Incident Copilot project."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin   = Cm(3.0)
    section.right_margin  = Cm(2.5)

# ── Helper functions ──────────────────────────────────────────────────────────
def set_font(run, name="Calibri", size=11, bold=False, italic=False, color=None):
    run.font.name  = name
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

def heading(text, level=1):
    p = doc.add_heading(text, level=level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = RGBColor(0x1E, 0x40, 0xAF)  # indigo-800
    return p

def body(text, space_before=0, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    run = p.add_run(text)
    set_font(run)
    return p

def bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    if bold_prefix:
        r = p.add_run(bold_prefix + "  ")
        set_font(r, bold=True, size=11)
    r2 = p.add_run(text)
    set_font(r2)
    return p

def sub_bullet(text, bold_prefix=None):
    p = doc.add_paragraph(style="List Bullet 2")
    p.paragraph_format.space_after = Pt(2)
    if bold_prefix:
        r = p.add_run(bold_prefix + "  ")
        set_font(r, bold=True, size=10)
    r2 = p.add_run(text)
    set_font(r2, size=10)
    return p

def labeled(label, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    r1 = p.add_run(label + ": ")
    set_font(r1, bold=True)
    r2 = p.add_run(text)
    set_font(r2)
    return p

def add_table(headers, rows):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.style = "Light Grid Accent 1"
    hdr = t.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        cell.text = h
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.name = "Calibri"
            run.font.size = Pt(10)
    for ri, row in enumerate(rows):
        r = t.rows[ri + 1]
        for ci, val in enumerate(row):
            r.cells[ci].text = val
            for run in r.cells[ci].paragraphs[0].runs:
                run.font.name = "Calibri"
                run.font.size = Pt(10)
    doc.add_paragraph()

def divider():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)

# ══════════════════════════════════════════════════════════════════════════════
# COVER
# ══════════════════════════════════════════════════════════════════════════════
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(48)
r = p.add_run("Incident Copilot")
set_font(r, size=28, bold=True, color=(0x1E, 0x40, 0xAF))

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = p2.add_run("Design & Architecture Document")
set_font(r2, size=16, italic=True, color=(0x47, 0x55, 0x69))

p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r3 = p3.add_run(f"Version 1.0  ·  {datetime.date.today().strftime('%B %d, %Y')}")
set_font(r3, size=11, color=(0x6B, 0x72, 0x80))

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════════════════
# 1. EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
heading("1. Executive Summary")
body(
    "Incident Copilot is a GenAI-powered assistant built to help software engineering and "
    "Site Reliability Engineering (SRE) teams investigate and resolve production incidents "
    "faster. Instead of an engineer manually searching through logs, dashboards, and runbooks "
    "while under pressure, Incident Copilot acts as an always-available expert colleague — "
    "one that has read every past incident the team has ever dealt with."
)
body(
    "The system accepts plain-English questions such as 'Why is the payment API slow?' and "
    "responds in real time, weaving together relevant past incidents, live log data, and recent "
    "deployment history to produce grounded, actionable answers. It can also produce a structured "
    "Root Cause Analysis (RCA) report at the click of a button, and it enforces a human approval "
    "step before any suggestion that could change a production system is acted upon."
)
body(
    "The MVP (Minimum Viable Product) described in this document covers the core conversational "
    "loop, semantic search over historical incidents, RCA generation, and the human approval "
    "gate — all running in Docker containers on a single machine."
)

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 2. PROBLEM STATEMENT
# ══════════════════════════════════════════════════════════════════════════════
heading("2. Problem Statement")
body(
    "When a production incident occurs — a service going down, a spike in errors, a sudden "
    "performance degradation — the on-call engineer faces a high-pressure, time-critical "
    "situation. The typical workflow involves:"
)
bullet("Searching Slack, Jira, or a wiki for similar past incidents.")
bullet("Manually pulling logs from multiple tools (Kibana, Splunk, Datadog).")
bullet("Reviewing recent deployment timelines to spot correlation.")
bullet("Writing an RCA report after the incident, often from memory.")
body(
    "This process is slow, error-prone, and relies heavily on institutional knowledge that is "
    "often held by a handful of senior engineers. Junior engineers in particular struggle "
    "to navigate unfamiliar services under pressure."
)
body(
    "Incident Copilot addresses this by consolidating institutional knowledge into a searchable, "
    "conversational assistant that surfaces the right context in seconds."
)

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 3. HIGH-LEVEL ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
heading("3. High-Level Architecture")
body(
    "The system is divided into three main layers that run as Docker containers:"
)
bullet("Frontend (React web app) — what the engineer sees and interacts with in their browser.")
bullet("Backend API (FastAPI Python service) — the brain of the system; handles all logic, AI calls, and database access.")
bullet("Database (PostgreSQL with pgvector) — stores incidents and their vector embeddings for semantic search.")
body(
    "The three containers communicate over a private Docker network. The engineer's browser "
    "only talks to the frontend container. The frontend proxies API requests to the backend. "
    "The backend talks to the database and to two external AI APIs (Anthropic and Voyage AI)."
)

heading("3.1 Data Flow — Conversational Chat", level=2)
body("When an engineer types a question, this is the sequence of events:")
bullet("1.", bold_prefix="Browser")
sub_bullet("Engineer types a question and presses Enter. The browser sends the message to the backend via an HTTP POST request.")
bullet("2.", bold_prefix="Backend — RAG retrieval")
sub_bullet("The backend converts the question into a numerical vector using Voyage AI's embedding model. It then searches the database for the three most similar past incidents using that vector. This is called Retrieval-Augmented Generation (RAG).")
bullet("3.", bold_prefix="Backend — Context assembly")
sub_bullet("The backend assembles a context block containing: the similar past incidents (with titles, descriptions, and resolutions), the current incident's log snapshot and live connector logs, and the three most recent deployments for the service in question.")
bullet("4.", bold_prefix="Backend — Claude API call")
sub_bullet("The assembled context plus the engineer's question are sent to Claude (Anthropic's AI model). The response is streamed back word-by-word as it is generated.")
bullet("5.", bold_prefix="Browser — Live streaming")
sub_bullet("The frontend reads the streamed response and displays each word as it arrives, giving the engineer immediate feedback rather than waiting for the full answer.")
bullet("6.", bold_prefix="Citations")
sub_bullet("Once the answer is complete, the backend sends a list of the historical incidents that were used as context. These appear as coloured chips under the message and in the right-hand 'Context' panel.")

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 4. COMPONENT BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
heading("4. Component Breakdown")

# 4.1 Frontend
heading("4.1 Frontend — React Web Application", level=2)
body(
    "The frontend is a single-page web application. The engineer opens it in a standard "
    "browser — no installation required. It is built with React 18, TypeScript, Tailwind CSS, "
    "and Vite."
)

heading("4.1.1 Incident Selector (Top Navigation Bar)", level=3)
body(
    "A dropdown at the top of the page lists all incidents stored in the system, labelled "
    "with their severity (P1–P4) and title. When the engineer selects an incident, all subsequent "
    "chat messages automatically include that incident's log data and deployment history as "
    "context for the AI. Selecting 'No incident selected' returns the copilot to general mode."
)

heading("4.1.2 Chat Panel", level=3)
body(
    "The main area of the screen. The engineer types questions in a text box at the bottom. "
    "Pressing Enter sends the message; Shift+Enter inserts a new line. The AI's response "
    "streams in real time in a chat-bubble style. A blinking cursor indicates the AI is still "
    "generating. User messages appear on the right in indigo; AI messages appear on the left "
    "in grey. The panel auto-scrolls to the latest message."
)

heading("4.1.3 Right Sidebar — Context Tab", level=3)
body(
    "After each AI response, the sidebar updates to show the historical incidents that the AI "
    "used to form its answer. Each card shows the incident's severity badge and title. This "
    "gives the engineer full transparency into what information the AI is drawing from. "
    "It also helps validate the answer — if the retrieved incidents are clearly irrelevant, "
    "the engineer knows to treat the response with caution."
)

heading("4.1.4 Right Sidebar — RCA Tab", level=3)
body(
    "When an incident is selected, the engineer can switch to the RCA tab and click "
    "'Generate RCA'. The system sends the incident details and similar past incidents to Claude "
    "with a specialised prompt that asks for a structured JSON response. The result is displayed "
    "in five clearly labelled sections:"
)
bullet("Timeline — a chronological sequence of events")
bullet("Root Cause — the precise technical reason the incident occurred")
bullet("Impacted Systems — the services and components affected")
bullet("Resolution Steps — the actions taken or recommended to fix the issue")
bullet("Recommendations — preventive measures to stop recurrence")
body(
    "If an RCA was previously generated for this incident, it loads immediately without "
    "regenerating. The engineer can regenerate it at any time to get a fresh analysis."
)

heading("4.1.5 Approval Gate", level=3)
body(
    "The AI is instructed never to suggest a production-impacting action without flagging it. "
    "When the AI's response contains the text '[REQUIRES APPROVAL]', an amber warning card "
    "automatically appears below that message. The card describes the action and presents two "
    "buttons:"
)
bullet("Approve — creates an approval record in the database and marks it as 'approved'.")
bullet("Reject — creates a record and marks it as 'rejected'. Both actions are permanently recorded.")
body(
    "This ensures that no automated or AI-suggested action is executed in production without "
    "a human explicitly signing off. The decision and who made it are stored in the database "
    "for audit purposes."
)

# 4.2 Backend
heading("4.2 Backend — FastAPI Python API", level=2)
body(
    "The backend is a Python web service built with FastAPI. It is the central hub that "
    "orchestrates all logic: authentication, database queries, AI calls, and streaming responses. "
    "All operations are asynchronous, meaning the server can handle multiple requests "
    "simultaneously without blocking."
)

heading("4.2.1 Authentication", level=3)
body(
    "Every request to the API must include an X-API-Key header. The backend checks this "
    "against the configured secret. If it is missing or wrong, the request is rejected with "
    "a 401 Unauthorized response. This is a simple but effective first line of defence, "
    "preventing unauthorised access to the API from outside the organisation."
)

heading("4.2.2 Chat Endpoint (POST /api/chat)", level=3)
body(
    "This is the most important endpoint. It accepts the engineer's message, optionally an "
    "incident ID, and the conversation history so far. It runs the full RAG pipeline "
    "(retrieve → assemble context → call Claude → stream back) and returns a "
    "Server-Sent Events (SSE) stream. SSE is a lightweight standard for one-way real-time "
    "data pushing from server to browser — it is what enables the typewriter streaming effect."
)

heading("4.2.3 RCA Endpoint (POST /api/rca/generate)", level=3)
body(
    "Accepts an incident ID. Fetches the incident from the database, retrieves similar past "
    "incidents, calls Claude with a strict JSON-output prompt, parses the result, and stores "
    "it in the rca_reports table. If an RCA already exists for this incident, it is replaced "
    "with the new one. The response is the full structured RCA as a JSON object."
)

heading("4.2.4 Incidents Endpoints", level=3)
body("Four REST endpoints manage the incident data:")
bullet("GET /api/incidents — returns all incidents ordered by creation date, newest first.")
bullet("GET /api/incidents/{id} — returns a single incident plus its RCA report if one has been generated.")
bullet("POST /api/incidents/{id}/approve — creates an approval request record with status 'pending'.")
bullet("PATCH /api/incidents/{id}/approve/{approval_id} — updates an approval request to 'approved' or 'rejected'.")

heading("4.2.5 Mock Connectors", level=3)
body(
    "In a production deployment, the backend would integrate with real observability tools "
    "such as Datadog, Splunk, or a Kubernetes API. In the MVP, two mock connectors simulate "
    "this data:"
)
bullet("Log connector (logs.py) — generates realistic fake log lines tailored to the service name. A payment-api incident shows payment processing errors; a checkout-service incident shows cart operation failures.")
bullet("Deployment connector (deployments.py) — generates a list of three recent fake deployments. The most recent one is always either a failed deployment or one with a suspiciously risky commit message, making it an ideal demonstration of deployment-correlated incidents.")

heading("4.2.6 Seed Data", level=3)
body(
    "When the backend starts for the first time, it automatically inserts 20 realistic mock "
    "incidents covering a diverse range of scenarios: OOMKilled Kubernetes pods, database "
    "connection pool exhaustion, SSL certificate expiry warnings, Kafka consumer lag, gRPC "
    "timeouts, and more. Each incident includes a description, log snapshot, metrics summary, "
    "and a deployment reference. For resolved incidents, a resolution field explains what fixed it."
)
body(
    "After inserting the incidents, the backend generates vector embeddings for all 20 using "
    "Voyage AI and stores them in the database. This entire process is idempotent — if the "
    "database already contains incidents, the seed step is skipped automatically."
)

# 4.3 Database
heading("4.3 Database — PostgreSQL with pgvector", level=2)
body(
    "The database is PostgreSQL 16, a widely used open-source relational database. It stores "
    "four types of data in four tables."
)

add_table(
    ["Table", "What it stores"],
    [
        ["incidents", "All incident records: title, severity, status, service, description, logs, metrics, resolution, timestamps."],
        ["incident_embeddings", "A 1024-dimensional vector for each incident, used for semantic similarity search."],
        ["rca_reports", "Generated RCA reports, one per incident, with all five structured fields."],
        ["approval_requests", "Every approval or rejection event, with who reviewed it and when."],
    ]
)

body(
    "The pgvector extension adds vector search capability to PostgreSQL. A vector is simply "
    "a long list of numbers (1024 of them) that captures the 'meaning' of a piece of text. "
    "When an engineer asks a question, the question is also converted to a vector, and "
    "PostgreSQL finds the stored incidents whose vectors are closest in mathematical space — "
    "these are the semantically most similar incidents, regardless of exact wording."
)
body(
    "An IVFFlat index is created on the embeddings table to make this vector search fast even "
    "as the number of incidents grows."
)

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 5. AI MODEL CHOICES
# ══════════════════════════════════════════════════════════════════════════════
heading("5. AI Model & Tool Choices")
body(
    "Every tool in the stack was chosen for a specific reason. This section explains those choices "
    "in plain language."
)

add_table(
    ["Tool", "What it does", "Why this choice"],
    [
        [
            "Claude (claude-sonnet-4-6)\nby Anthropic",
            "Generates all chat responses and RCA reports.",
            "Claude Sonnet 4.6 is one of the fastest and most capable models available. It follows complex instructions reliably, produces well-structured JSON on demand, and has a 1-million-token context window — large enough to fit many past incidents. Anthropic publishes clear safety and usage policies, important for enterprise use."
        ],
        [
            "Voyage AI (voyage-3)\n1024-dimensional embeddings",
            "Converts text (incidents, questions) into numerical vectors for similarity search.",
            "Voyage AI's models are purpose-built for retrieval tasks and consistently outperform general-purpose embedding models on technical text. The voyage-3 model produces 1024-dimensional vectors — a good balance between accuracy and storage/compute cost."
        ],
        [
            "PostgreSQL 16\n+ pgvector extension",
            "Stores all data and performs vector similarity search.",
            "PostgreSQL is mature, reliable, and trusted in enterprise environments. Adding pgvector avoids the need for a separate vector database (like Pinecone or Weaviate), reducing operational complexity. Everything lives in one database, simplifying backups and access control."
        ],
        [
            "FastAPI (Python)",
            "Backend web framework. Handles all API routing, validation, and streaming.",
            "FastAPI is built on modern async Python, making it highly performant for I/O-heavy workloads like streaming AI responses. It auto-generates interactive API documentation (Swagger UI at /docs), and its Pydantic integration validates all request and response data automatically."
        ],
        [
            "Server-Sent Events (SSE)",
            "Streams AI responses word-by-word to the browser.",
            "SSE is a simple web standard that works over regular HTTP — no special infrastructure needed. It is well-supported in all modern browsers and frameworks. The alternative (WebSockets) adds bidirectional complexity that is not needed here since the stream only flows from server to browser."
        ],
        [
            "React 18 + TypeScript",
            "Frontend user interface.",
            "React is the industry-standard choice for interactive web UIs. TypeScript adds type safety, catching bugs at development time rather than in production. Strict mode is enabled throughout."
        ],
        [
            "Tailwind CSS",
            "Styling the frontend.",
            "Tailwind provides utility classes that allow rapid UI development without writing separate CSS files. The design system is consistent and responsive out of the box."
        ],
        [
            "Vite",
            "Frontend build tool and development server.",
            "Vite starts in milliseconds and provides instant hot reload during development. It also acts as a proxy — forwarding /api/* requests from the browser to the backend container, avoiding cross-origin issues."
        ],
        [
            "Docker & Docker Compose",
            "Packages and runs all three components together.",
            "Docker ensures that the application runs identically on any machine regardless of what is installed. Docker Compose defines the three services (db, api, frontend) and their dependencies in a single file, so the entire system starts with one command."
        ],
    ]
)

body(
    "No LangChain, LangGraph, or other LLM orchestration frameworks are used. All AI "
    "orchestration is plain Python. This keeps the code transparent, debuggable, and "
    "free from opaque abstractions — important for a system making production decisions."
)

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 6. SECURITY DESIGN
# ══════════════════════════════════════════════════════════════════════════════
heading("6. Security Design")
body(
    "The MVP implements a lightweight but meaningful security model appropriate for an "
    "internal tool."
)
bullet("API Key Authentication", bold_prefix="")
sub_bullet("Every request to the backend must include an X-API-Key header. The key is stored in an environment variable, not in source code. A missing or wrong key returns 401 Unauthorized before any logic runs.")
bullet("Secrets Management", bold_prefix="")
sub_bullet("All secrets (Anthropic API key, Voyage AI API key, database password, API key) live in a .env file that is excluded from version control via .gitignore. The .env.example file shows only the variable names, with empty values.")
bullet("CORS Policy", bold_prefix="")
sub_bullet("The backend only accepts browser requests from the configured frontend origin (http://localhost:5173 by default). Requests from any other origin are blocked.")
bullet("No Secrets in Code", bold_prefix="")
sub_bullet("No API key, password, or token appears in any source file. Configuration is always injected via environment variables at runtime.")

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 7. PROMPT ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
heading("7. Prompt Engineering")
body(
    "The AI's behaviour is governed by two system prompts — instructions given to Claude "
    "before every conversation."
)

heading("7.1 Chat System Prompt", level=2)
body(
    "Claude is instructed to behave as an expert SRE. Key behavioural rules embedded in the prompt:"
)
bullet("Be concise and technical — avoid waffle.")
bullet("Always cite historical incidents using [INC-{id}] notation so engineers know where the context came from.")
bullet("Flag any suggested production action with [REQUIRES APPROVAL] — this is what triggers the approval gate in the UI.")
bullet("Admit uncertainty — if the root cause is unclear from the provided data, say so explicitly.")
bullet("Never invent log lines or metrics — only reference data that was provided in the context block.")

heading("7.2 RCA System Prompt", level=2)
body(
    "For RCA generation, Claude is given a strict prompt that produces only valid JSON with "
    "exactly five fields. The fence-stripping code in the backend handles any accidental "
    "markdown formatting Claude might add around the JSON. This structured output makes it "
    "trivial to parse and display the five RCA sections independently in the UI."
)

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 8. DEPLOYMENT & OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════
heading("8. Deployment & Operations")

heading("8.1 Starting the System", level=2)
body("The entire system is started with a single command from the project root:")
p = doc.add_paragraph()
r = p.add_run("    docker compose up --build")
r.font.name = "Courier New"
r.font.size = Pt(10)
r.font.color.rgb = RGBColor(0x0F, 0x76, 0x6E)
body(
    "Docker Compose builds the backend and frontend images, starts the database, waits for "
    "it to be healthy, then starts the API and frontend. On first run, the backend automatically "
    "creates the database schema, enables the pgvector extension, seeds the 20 mock incidents, "
    "and generates their embeddings (approximately 30 seconds). All subsequent starts skip "
    "the seed step."
)

heading("8.2 Health Check", level=2)
body(
    "The backend exposes a GET /health endpoint that returns {\"status\": \"ok\"}. This is used "
    "by Docker Compose to determine when the API is ready to accept traffic."
)

heading("8.3 Hot Reload", level=2)
body(
    "During development, both the backend (uvicorn --reload) and the frontend (Vite HMR) "
    "automatically reload when source files change. The Docker volumes mount the local "
    "source directories into the containers, so changes on the host are reflected immediately "
    "without rebuilding the image."
)

heading("8.4 Automated Tests", level=2)
body("Three automated tests cover the critical paths:")
bullet("test_health_check — verifies the health endpoint returns 200 and the correct JSON body.")
bullet("test_chat_requires_auth — verifies that a request without an API key returns 401.")
bullet("test_chat_returns_stream — verifies the chat endpoint streams a text/event-stream response using mocked AI calls (no real API keys needed).")
body("Tests run with: python -m pytest -q from the backend directory.")

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 9. DATA FLOW DIAGRAM (TEXT)
# ══════════════════════════════════════════════════════════════════════════════
heading("9. End-to-End Data Flow Summary")
body(
    "The table below traces a single chat message from the engineer's keyboard to the "
    "streamed response on screen."
)
add_table(
    ["Step", "Where", "What happens"],
    [
        ["1", "Browser", "Engineer types a question and presses Enter."],
        ["2", "Browser → Backend", "POST /api/chat with message, incident_id, conversation history."],
        ["3", "Backend", "question text → Voyage AI API → 1024-dimensional embedding vector."],
        ["4", "Backend → Database", "SELECT top-3 incidents WHERE embedding ≈ question vector (cosine distance)."],
        ["5", "Backend", "Fetch current incident logs (mock connector) + recent deployments (mock connector)."],
        ["6", "Backend", "Assemble <context> block: similar incidents + logs + deployments."],
        ["7", "Backend → Anthropic", "POST to Claude API with system prompt + context + question."],
        ["8", "Anthropic → Backend", "Token stream returned chunk by chunk."],
        ["9", "Backend → Browser", "Each chunk forwarded immediately as SSE data: {delta: '...'} event."],
        ["10", "Browser", "Each delta appended to the assistant message bubble in real time."],
        ["11", "Backend → Browser", "Stream ends; final SSE event sent: {done: true, citations: [...]}"],
        ["12", "Browser", "Citation chips appear under the message; Context sidebar updates."],
    ]
)

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 10. FUTURE SCOPE
# ══════════════════════════════════════════════════════════════════════════════
heading("10. Future Scope")
body(
    "The MVP demonstrates the core value proposition. The following areas represent the natural "
    "roadmap for a production-grade deployment."
)

heading("10.1 Real Observability Integrations", level=2)
body(
    "The mock log and deployment connectors would be replaced with real integrations:"
)
bullet("Logs — Datadog, Splunk, Elasticsearch/OpenSearch, or Grafana Loki.")
bullet("Metrics — Datadog, Prometheus/Grafana, or New Relic.")
bullet("Deployments — GitHub Actions, Spinnaker, ArgoCD, or Harness.")
bullet("Alerts — PagerDuty, Opsgenie, or VictorOps for pulling active alert context automatically.")
bullet("Kubernetes — kubectl or the Kubernetes API for pod status, events, and resource utilisation.")
body(
    "These connectors would make the context block factual and live, rather than simulated."
)

heading("10.2 Authentication & Access Control", level=2)
body(
    "The API-key model is adequate for a prototype but not for enterprise production:"
)
bullet("Single Sign-On (SSO) — integrate with the organisation's identity provider (Okta, Azure AD, Google Workspace) using OIDC/SAML.")
bullet("Role-Based Access Control (RBAC) — different roles for read-only viewers, incident responders, and approvers.")
bullet("Per-user audit trail — record which engineer approved or rejected each action.")

heading("10.3 Richer RCA & Knowledge Base", level=2)
body(
    "The current RCA is generated fresh each time. Future enhancements:"
)
bullet("Store RCAs in a searchable knowledge base so they are retrieved as context in future incidents.")
bullet("Auto-link RCAs to Jira tickets, Confluence pages, or internal wikis.")
bullet("Track recurring root causes across incidents to surface systemic patterns.")
bullet("Allow engineers to edit and annotate the generated RCA before marking it final.")

heading("10.4 Agentic Capabilities", level=2)
body(
    "Today, the copilot only answers questions. In future, with appropriate approval gates:"
)
bullet("Automated runbook execution — the copilot could trigger a rollback, restart a pod, or scale a deployment directly, subject to human approval.")
bullet("Multi-step investigation — the copilot could autonomously gather additional context (fetch more logs, query metrics for a time range) before responding.")
bullet("Proactive alerting — trigger a chat session automatically when a new alert fires in PagerDuty, with context already assembled.")

heading("10.5 Improved UI/UX", level=2)
bullet("Incident detail drawer — clicking a citation card opens a panel with the full incident description, log snapshot, and resolution.")
bullet("Conversation export — save a chat session as a PDF or Confluence page.")
bullet("Dark mode toggle and mobile-responsive layout.")
bullet("Incident creation from chat — engineer describes a new incident in chat and the copilot creates it in the database.")

heading("10.6 Reliability & Scalability", level=2)
bullet("High Availability (HA) — run multiple API instances behind a load balancer. Use managed PostgreSQL (AWS RDS, Google Cloud SQL) instead of a single container.")
bullet("Caching — cache Voyage AI embedding calls for repeated queries; cache Claude responses for identical prompts.")
bullet("Rate limiting — per-user and per-organisation limits on AI API calls to control costs.")
bullet("Observability — add distributed tracing (OpenTelemetry), structured logging, and metrics for the copilot itself.")

heading("10.7 Security Hardening", level=2)
bullet("Prompt injection defence — validate and sanitise user inputs to prevent attempts to override the system prompt.")
bullet("Data residency — route all AI API calls through a private endpoint or self-hosted model for data-sensitive environments.")
bullet("Encryption at rest — encrypt the incidents and embeddings tables for compliance.")
bullet("Penetration testing — commission external security review before production rollout.")

divider()

# ══════════════════════════════════════════════════════════════════════════════
# 11. GLOSSARY
# ══════════════════════════════════════════════════════════════════════════════
heading("11. Glossary")
add_table(
    ["Term", "Plain-English definition"],
    [
        ["API", "Application Programming Interface — a way for two software systems to talk to each other over a network."],
        ["Claude", "An AI language model made by Anthropic, similar to ChatGPT but made by a different company."],
        ["Cosine distance", "A mathematical measure of how similar two vectors are. Two identical vectors have a cosine distance of 0; completely opposite vectors have a distance of 2."],
        ["Docker", "A tool that packages software and all its dependencies into a portable 'container' that runs the same way on any machine."],
        ["Embedding / Vector", "A long list of numbers that represents the meaning of a piece of text. Texts with similar meanings have similar vectors."],
        ["FastAPI", "A Python framework for building web APIs quickly and reliably."],
        ["GenAI", "Generative AI — AI systems that produce text, images, code, or other content (as opposed to AI that only classifies or predicts)."],
        ["Incident", "An unplanned event that disrupts or degrades a software service (e.g. a website going down or a payment system slowing down)."],
        ["LLM", "Large Language Model — the technology behind AI assistants like Claude and GPT. Trained on vast amounts of text to understand and generate language."],
        ["pgvector", "An extension to PostgreSQL that adds the ability to store and search vectors (number lists) efficiently."],
        ["P1 / P2 / P3 / P4", "Severity levels for incidents. P1 is the most severe (full outage), P4 is the least (minor warning)."],
        ["RAG", "Retrieval-Augmented Generation — a technique where relevant documents are retrieved from a database and included in the prompt so the AI can answer based on real data rather than guessing."],
        ["RCA", "Root Cause Analysis — a structured investigation to identify why an incident occurred and how to prevent it from happening again."],
        ["REST", "A common convention for designing web APIs, using standard HTTP methods (GET, POST, PATCH) and URLs to represent resources."],
        ["SRE", "Site Reliability Engineering — the discipline of designing and operating software systems to be reliable and scalable."],
        ["SSE", "Server-Sent Events — a web standard for a server to push real-time updates to a browser over a normal HTTP connection."],
        ["TypeScript", "A stricter version of JavaScript that catches programming errors before the code is run."],
        ["UUID", "Universally Unique Identifier — a long random string used as a unique ID for database records."],
        ["Vector search", "Searching a database not by exact keyword but by mathematical similarity — finding records whose meaning is closest to the search query."],
    ]
)

# ── Save ──────────────────────────────────────────────────────────────────────
out = r"d:\Projects\incident-copilot\Design_details.docx"
doc.save(out)
print(f"Saved: {out}")
