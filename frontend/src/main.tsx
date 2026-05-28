import React, { FormEvent, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_BASE = "http://127.0.0.1:8000/api";

type Citation = {
  document_id: string;
  title: string;
  page_number: number;
  chunk_id: string;
  excerpt: string;
  score: number | null;
};

type ChatResponse = {
  answer: string;
  citations: Citation[];
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};

type IngestResponse = {
  document_id: string;
  title: string;
  chunks_indexed: number;
};

type DocumentRecord = {
  document_id: string;
  title: string;
  source_path: string;
  access_level: string;
  status: string;
  chunks_indexed: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  indexed_at: string | null;
  latest_job_status: string | null;
};

type CurrentUser = {
  user_id: string;
  email: string;
  role: "admin" | "user";
};

type TokenResponse = {
  access_token: string;
  token_type: string;
};

type EvaluationItem = {
  question_id: string;
  question: string;
  expected_document: string;
  expected_pages: number[];
  retrieved_document: string | null;
  retrieved_page: number | null;
  rank: number | null;
  reciprocal_rank: number;
  latency_ms: number;
  hit: boolean;
};

type EvaluationRun = {
  run_id: string;
  name: string;
  question_set_path: string;
  top_k: number;
  access_levels: string[];
  question_count: number;
  hit_count: number;
  recall_at_k: number;
  mrr: number;
  average_latency_ms: number;
  status: string;
  error_message: string | null;
  created_at: string;
  items: EvaluationItem[];
};

const sampleQuestions = [
  "この文書は何について説明していますか？",
  "特定技能外国人を雇用する流れを教えてください。",
  "申請に必要な書類は何ですか？",
];

const docs = [
  "jp_rag_1.pdf",
  "jp_rag_2.pdf",
  "jp_rag_3.pdf",
  "jp_rag_4.pdf",
  "jp_rag_5.pdf",
  "jp_rag_6.pdf",
  "jp_rag_7.pdf",
];

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: crypto.randomUUID(),
      role: "assistant",
      content:
        "資料を索引化したあと、質問してください。回答には参照ページが付きます。",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(() => localStorage.getItem("access_token") ?? "");
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [selectedDoc, setSelectedDoc] = useState("jp_rag_1.pdf");
  const [accessLevel, setAccessLevel] = useState("public");
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentBusyId, setDocumentBusyId] = useState<string | null>(null);
  const [evaluationRuns, setEvaluationRuns] = useState<EvaluationRun[]>([]);
  const [latestEvaluation, setLatestEvaluation] = useState<EvaluationRun | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [questionSetPath, setQuestionSetPath] = useState("eval/questions.local.jsonl");
  const [evalTopK, setEvalTopK] = useState(5);
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  const [notice, setNotice] = useState("Index jp_rag_1.pdf first if the vector store is empty.");

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((response) => setStatus(response.ok ? "online" : "offline"))
      .catch(() => setStatus("offline"));
  }, []);

  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      setDocuments([]);
      return;
    }
    void loadCurrentUser();
  }, [token]);

  const lastCitations = useMemo(() => {
    const assistantMessages = messages.filter((message) => message.role === "assistant");
    return assistantMessages.at(-1)?.citations ?? [];
  }, [messages]);

  async function refreshDocuments() {
    try {
      const response = await apiFetch("/documents");
      if (!response.ok) {
        throw new Error("Could not load indexed documents.");
      }
      setDocuments((await response.json()) as DocumentRecord[]);
    } catch {
      setDocuments([]);
    }
  }

  async function apiFetch(path: string, init?: RequestInit) {
    return fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        ...(init?.headers ?? {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
  }

  async function loadCurrentUser() {
    try {
      const response = await apiFetch("/auth/me");
      if (!response.ok) {
        throw new Error("Session expired.");
      }
      const user = (await response.json()) as CurrentUser;
      setCurrentUser(user);
      await refreshDocuments();
      if (user.role === "admin") {
        await refreshEvaluations();
      }
    } catch {
      localStorage.removeItem("access_token");
      setToken("");
      setCurrentUser(null);
      setDocuments([]);
      setEvaluationRuns([]);
      setLatestEvaluation(null);
    }
  }

  async function refreshEvaluations() {
    try {
      const response = await apiFetch("/evaluations");
      if (!response.ok) {
        throw new Error("Could not load evaluations.");
      }
      setEvaluationRuns((await response.json()) as EvaluationRun[]);
    } catch {
      setEvaluationRuns([]);
    }
  }

  async function login(event: FormEvent) {
    event.preventDefault();
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const payload = (await response.json()) as TokenResponse | { detail: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail : "Login failed");
      }
      localStorage.setItem("access_token", payload.access_token);
      setToken(payload.access_token);
      setPassword("");
      setNotice("Authenticated.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Login failed");
    }
  }

  function logout() {
    localStorage.removeItem("access_token");
    setToken("");
    setCurrentUser(null);
    setDocuments([]);
    setEvaluationRuns([]);
    setLatestEvaluation(null);
    setNotice("Logged out.");
  }

  async function ingestDocument() {
    setIngesting(true);
    setNotice(`Indexing ${selectedDoc}...`);

    try {
      const response = await apiFetch("/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: selectedDoc, access_level: accessLevel }),
      });
      const payload = (await response.json()) as IngestResponse | { detail: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail : "Ingestion failed");
      }
      setNotice(
        `${payload.title} indexed: ${payload.chunks_indexed} chunks. Access: ${accessLevel}.`,
      );
      await refreshDocuments();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Ingestion failed");
    } finally {
      setIngesting(false);
    }
  }

  async function reindexDocument(document: DocumentRecord) {
    setDocumentBusyId(document.document_id);
    setNotice(`Re-indexing ${document.title}...`);
    try {
      const response = await apiFetch(`/documents/${document.document_id}/reindex`, {
        method: "POST",
      });
      const payload = (await response.json()) as IngestResponse | { detail: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail : "Re-index failed");
      }
      setNotice(`${payload.title} re-indexed: ${payload.chunks_indexed} chunks.`);
      await refreshDocuments();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Re-index failed");
    } finally {
      setDocumentBusyId(null);
    }
  }

  async function removeDocument(document: DocumentRecord) {
    setDocumentBusyId(document.document_id);
    setNotice(`Deleting ${document.title}...`);
    try {
      const response = await apiFetch(`/documents/${document.document_id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const payload = (await response.json()) as { detail?: string };
        throw new Error(payload.detail ?? "Delete failed");
      }
      setNotice(`${document.title} deleted.`);
      await refreshDocuments();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Delete failed");
    } finally {
      setDocumentBusyId(null);
    }
  }

  async function runEvaluation() {
    setEvaluating(true);
    setNotice("Running retrieval evaluation...");
    try {
      const response = await apiFetch("/evaluations/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: "retrieval-eval",
          question_set_path: questionSetPath,
          top_k: evalTopK,
          access_levels: ["public", "hr", "engineering", "admin"],
        }),
      });
      const payload = (await response.json()) as EvaluationRun | { detail: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail : "Evaluation failed");
      }
      setLatestEvaluation(payload);
      await refreshEvaluations();
      setNotice(
        `Eval complete: recall ${(payload.recall_at_k * 100).toFixed(0)}%, MRR ${payload.mrr.toFixed(2)}.`,
      );
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  }

  async function sendQuestion(event?: FormEvent) {
    event?.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };
    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setLoading(true);
    setNotice("Searching the archive...");

    try {
      const response = await apiFetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      const payload = (await response.json()) as ChatResponse | { detail: string };
      if (!response.ok) {
        throw new Error("detail" in payload ? payload.detail : "Chat failed");
      }
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: payload.answer,
          citations: payload.citations,
        },
      ]);
      setNotice(`${payload.citations.length} source passages retrieved.`);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "The archive could not answer this request.",
        },
      ]);
      setNotice("The backend returned an error.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="world">
      <div className="sunset" />
      <div className="terrain" aria-hidden="true">
        <div className="path path-a" />
        <div className="path path-b" />
        <div className="hut hut-a" />
        <div className="hut hut-b" />
        <div className="tree tree-a" />
        <div className="tree tree-b" />
        <div className="tree tree-c" />
        <div className="fence fence-a" />
        <div className="barrel barrel-a" />
        <div className="lamp lamp-a" />
      </div>

      <section className="app-shell">
        <header className="hero-hud pixel-frame wood-frame">
          <div>
            <p className="kicker">Archive Guild</p>
            <h1>Japanese Enterprise Knowledge Assistant</h1>
          </div>
          <div className="party-hud">
            <div className="avatar">文</div>
            <div className="bars">
              <div className="bar-label">RAG</div>
              <div className="bar hp"><span style={{ width: status === "online" ? "100%" : "28%" }} /></div>
              <div className="bar mp"><span style={{ width: loading || ingesting ? "72%" : "42%" }} /></div>
            </div>
            <span className={`status-orb ${status}`}>{status}</span>
          </div>
        </header>

        {!currentUser ? (
          <section className="login-panel pixel-frame wood-frame">
            <div>
              <p className="kicker">Guild Sign-In</p>
              <h2>Authenticate</h2>
            </div>
            <form className="login-form" onSubmit={login}>
              <input
                className="pixel-input"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="email"
              />
              <input
                className="pixel-input"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="password"
              />
              <button className="pixel-button green" type="submit">
                Login
              </button>
            </form>
          </section>
        ) : (
          <div className="session-strip pixel-frame iron-frame">
            <span>{currentUser.email}</span>
            <span className="role-badge">{currentUser.role}</span>
            <button className="mini-button" onClick={logout}>Logout</button>
          </div>
        )}

        {currentUser && <div className="content-grid">
          <aside className="sidebar pixel-frame stone-frame">
            <div className="panel-title">Quest Board</div>

            {currentUser.role === "admin" && (
              <>
                <label className="field-label" htmlFor="doc-select">Document</label>
                <select
                  id="doc-select"
                  className="pixel-input"
                  value={selectedDoc}
                  onChange={(event) => setSelectedDoc(event.target.value)}
                >
                  {docs.map((doc) => (
                    <option key={doc} value={doc}>{doc}</option>
                  ))}
                </select>

                <label className="field-label" htmlFor="access-level">Access Rune</label>
                <select
                  id="access-level"
                  className="pixel-input"
                  value={accessLevel}
                  onChange={(event) => setAccessLevel(event.target.value)}
                >
                  <option value="public">public</option>
                  <option value="hr">hr</option>
                  <option value="engineering">engineering</option>
                  <option value="admin">admin</option>
                </select>

                <button className="pixel-button green" onClick={ingestDocument} disabled={ingesting}>
                  {ingesting ? "Indexing..." : "Index Scroll"}
                </button>
              </>
            )}

            <div className="divider-bar"><span /></div>

            <div className="panel-title small">Indexed Scrolls</div>
            {documents.length === 0 ? (
              <p className="empty-state compact">No indexed documents yet.</p>
            ) : (
              <div className="document-list">
                {documents.map((document) => (
                  <article className="document-card" key={document.document_id}>
                    <div className="document-title-row">
                      <h3>{document.title}</h3>
                      <span className={`document-status ${document.status}`}>{document.status}</span>
                    </div>
                    <p>{document.chunks_indexed} chunks · {document.access_level}</p>
                    {document.error_message && <small>{document.error_message}</small>}
                    {currentUser.role === "admin" && (
                      <div className="document-actions">
                        <button
                          className="mini-button"
                          onClick={() => void reindexDocument(document)}
                          disabled={documentBusyId === document.document_id}
                        >
                          Re-index
                        </button>
                        <button
                          className="mini-button danger"
                          onClick={() => void removeDocument(document)}
                          disabled={documentBusyId === document.document_id}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </article>
                ))}
              </div>
            )}

            <div className="divider-bar"><span /></div>

            {currentUser.role === "admin" && (
              <>
                <div className="panel-title small">Eval Ledger</div>
                <label className="field-label" htmlFor="question-set">Gold Set</label>
                <input
                  id="question-set"
                  className="pixel-input"
                  value={questionSetPath}
                  onChange={(event) => setQuestionSetPath(event.target.value)}
                />
                <label className="field-label" htmlFor="eval-top-k">Top K</label>
                <input
                  id="eval-top-k"
                  className="pixel-input"
                  type="number"
                  min={1}
                  max={20}
                  value={evalTopK}
                  onChange={(event) => setEvalTopK(Number(event.target.value))}
                />
                <button className="pixel-button green" onClick={runEvaluation} disabled={evaluating}>
                  {evaluating ? "Measuring..." : "Run Eval"}
                </button>
                {(latestEvaluation ?? evaluationRuns[0]) && (
                  <div className="eval-card">
                    <div className="metric-grid">
                      <div>
                        <span>Recall</span>
                        <strong>{(((latestEvaluation ?? evaluationRuns[0]).recall_at_k) * 100).toFixed(0)}%</strong>
                      </div>
                      <div>
                        <span>MRR</span>
                        <strong>{(latestEvaluation ?? evaluationRuns[0]).mrr.toFixed(2)}</strong>
                      </div>
                      <div>
                        <span>Latency</span>
                        <strong>{(latestEvaluation ?? evaluationRuns[0]).average_latency_ms.toFixed(0)}ms</strong>
                      </div>
                    </div>
                    <p>
                      {(latestEvaluation ?? evaluationRuns[0]).hit_count}/
                      {(latestEvaluation ?? evaluationRuns[0]).question_count} hits
                    </p>
                    {(latestEvaluation?.items ?? []).slice(0, 4).map((item) => (
                      <div className={`eval-item ${item.hit ? "hit" : "miss"}`} key={item.question_id}>
                        <span>{item.question_id}</span>
                        <small>
                          {item.hit ? `hit rank ${item.rank}` : "miss"} · {item.expected_document}
                        </small>
                      </div>
                    ))}
                  </div>
                )}

                <div className="divider-bar"><span /></div>
              </>
            )}

            <div className="panel-title small">Common Spells</div>
            <div className="sample-list">
              {sampleQuestions.map((item) => (
                <button
                  key={item}
                  className="sample-button"
                  onClick={() => setQuestion(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </aside>

          <section className="chat-panel pixel-frame wood-frame">
            <div className="chat-header">
              <div>
                <p className="kicker">Knowledge Hall</p>
                <h2>Ask the Archive</h2>
              </div>
              <div className="notice-ribbon">{notice}</div>
            </div>

            <div className="message-log">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="speaker">{message.role === "user" ? "You" : "Archivist"}</div>
                  <p>{message.content}</p>
                </article>
              ))}
              {loading && (
                <article className="message assistant loading-card">
                  <div className="speaker">Archivist</div>
                  <div className="loading-bars">
                    <span />
                    <span />
                    <span />
                  </div>
                </article>
              )}
            </div>

            <form className="ask-form" onSubmit={sendQuestion}>
              <textarea
                className="pixel-input question-box"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="質問を入力..."
              />
              <button className="pixel-button red" type="submit" disabled={loading}>
                {loading ? "Casting..." : "Ask"}
              </button>
            </form>
          </section>

          <aside className="citations pixel-frame iron-frame">
            <div className="panel-title">Source Relics</div>
            {lastCitations.length === 0 ? (
              <p className="empty-state">Citations will appear after an answer.</p>
            ) : (
              <div className="citation-list">
                {lastCitations.map((citation, index) => (
                  <article className="citation-card" key={citation.chunk_id}>
                    <div className="citation-rank">[{index + 1}]</div>
                    <h3>{citation.title}</h3>
                    <p>Page {citation.page_number}</p>
                    <div className="score-bar">
                      <span style={{ width: `${Math.max(8, (citation.score ?? 0) * 100)}%` }} />
                    </div>
                    <small>{citation.excerpt}</small>
                  </article>
                ))}
              </div>
            )}
          </aside>
        </div>}
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
