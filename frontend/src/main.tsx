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
  const [selectedDoc, setSelectedDoc] = useState("jp_rag_1.pdf");
  const [accessLevel, setAccessLevel] = useState("public");
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");
  const [notice, setNotice] = useState("Index jp_rag_1.pdf first if the vector store is empty.");

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((response) => setStatus(response.ok ? "online" : "offline"))
      .catch(() => setStatus("offline"));
  }, []);

  const lastCitations = useMemo(() => {
    const assistantMessages = messages.filter((message) => message.role === "assistant");
    return assistantMessages.at(-1)?.citations ?? [];
  }, [messages]);

  async function ingestDocument() {
    setIngesting(true);
    setNotice(`Indexing ${selectedDoc}...`);

    try {
      const response = await fetch(`${API_BASE}/ingest`, {
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
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Ingestion failed");
    } finally {
      setIngesting(false);
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
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed, access_levels: [accessLevel] }),
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

        <div className="content-grid">
          <aside className="sidebar pixel-frame stone-frame">
            <div className="panel-title">Quest Board</div>

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

            <div className="divider-bar"><span /></div>

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
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

