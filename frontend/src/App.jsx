
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "https://pdf-pilot-ai-chatbot-production.up.railway.app";

function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedPdf, setSelectedPdf] = useState(null);

  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");

  const [asking, setAsking] = useState(false);
  const [question, setQuestion] = useState("");
  const [chats, setChats] = useState({});
  const [error, setError] = useState("");
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const messages = selectedPdf
    ? chats[selectedPdf.pdf_id] || []
    : [];

  // Fetch uploaded documents
  const fetchDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/documents`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to fetch documents");
      }

      setDocuments(data.documents || []);
    } catch (err) {
      setError(err.message || "Unable to connect to backend");
    } finally {
      setLoadingDocuments(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);


// Load saved chat history whenever a PDF is selected
useEffect(() => {
  if (!selectedPdf) return;

  let cancelled = false;

  const loadChatHistory = async () => {
    try {
      const response = await fetch(
        `${API_URL}/chat-history/${selectedPdf.pdf_id}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to load chat history");
      }

      if (!cancelled) {
        setChats((prev) => ({
          ...prev,
          [selectedPdf.pdf_id]: (data.messages || []).map((msg) => ({
            role: msg.role,
            text: msg.message
          }))
        }));
      }
    } catch (err) {
      if (!cancelled) {
        setError(err.message);
      }
    }
  };

  loadChatHistory();

  return () => {
    cancelled = true;
  };
}, [selectedPdf?.pdf_id]);


  // Upload multiple PDFs one by one
  const handleUpload = async () => {
    if (files.length === 0) {
      setError("Please select at least one PDF.");
      return;
    }

    setUploading(true);
    setError("");

    const selectedFiles = [...files];
    let successfulUploads = 0;

    for (let i = 0; i < selectedFiles.length; i++) {
      const currentFile = selectedFiles[i];

      setUploadProgress(
        `Uploading ${i + 1} of ${selectedFiles.length}: ${currentFile.name}`
      );

      const formData = new FormData();
      formData.append("file", currentFile);

      try {
        const response = await fetch(`${API_URL}/upload-pdf`, {
          method: "POST",
          body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || "PDF upload failed");
        }

        successfulUploads++;

        const newDocument = {
          pdf_id: data.pdf_id,
          filename: data.filename,
          total_chunks: data.total_chunks,
        };

        setDocuments((prev) => [
          newDocument,
          ...prev.filter((doc) => doc.pdf_id !== data.pdf_id),
        ]);

        setChats((prev) => ({
          ...prev,
          [data.pdf_id]: [
            {
              role: "assistant",
              text: `Your PDF "${data.filename}" has been uploaded successfully! You can now ask questions about it.`,
            },
          ],
        }));

        // Automatically select the first successfully uploaded PDF
        if (successfulUploads === 1) {
          setSelectedPdf(newDocument);
        }
      } catch (err) {
        setError(`${currentFile.name}: ${err.message}`);
      }
    }

    setFiles([]);
    setUploadProgress("");
    setUploading(false);

    await fetchDocuments();
  };

  // Select a document
  const selectDocument = (document) => {
    setSelectedPdf(document);
    setError("");
    setMobileMenuOpen(false);
  };

  // Delete a document
  const handleDelete = async (document) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${document.filename}"?`
    );

    if (!confirmed) return;

    setError("");

    try {
      const response = await fetch(
        `${API_URL}/documents/${document.pdf_id}`,
        { method: "DELETE" }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Document deletion failed");
      }

      setDocuments((prev) =>
        prev.filter((doc) => doc.pdf_id !== document.pdf_id)
      );

      setChats((prev) => {
        const updated = { ...prev };
        delete updated[document.pdf_id];
        return updated;
      });

      if (selectedPdf?.pdf_id === document.pdf_id) {
        setSelectedPdf(null);
      }
    } catch (err) {
      setError(err.message || "Unable to delete document");
    }
  };

  // Ask a question about selected PDF
  const handleAsk = async (e) => {
    e.preventDefault();

    if (!question.trim() || !selectedPdf || asking) return;

    const userQuestion = question.trim();
    const pdfId = selectedPdf.pdf_id;

    setQuestion("");
    setError("");
    setAsking(true);

    setChats((prev) => ({
      ...prev,
      [pdfId]: [
        ...(prev[pdfId] || []),
        { role: "user", text: userQuestion },
      ],
    }));

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          pdf_id: pdfId,
          question: userQuestion,
          top_k: 3,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Unable to generate answer");
      }

      setChats((prev) => ({
        ...prev,
        [pdfId]: [
          ...(prev[pdfId] || []),
          {
            role: "assistant",
            text: data.answer,
            sources: data.sources || [],
          },
        ],
      }));
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="app">
      {mobileMenuOpen && (
        <button
          className="mobile-overlay"
          aria-label="Close menu"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <aside className={`sidebar ${mobileMenuOpen ? "mobile-open" : ""}`}>
        <div className="brand">
          <div className="brand-icon">P</div>
          <div>
            <h2>PDF Pilot</h2>
            <span>AI Document Assistant</span>
          </div>
          <button
            className="mobile-close"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            ×
          </button>
        </div>

        <div className="sidebar-content">
          <p className="side-label">WORKSPACE</p>

          <button
            className="side-item active"
            onClick={() => {
              setSelectedPdf(null);
              setMobileMenuOpen(false);
            }}
          >
            ✦ New Chat
          </button>

          <div className="documents-heading">
            <span>▤ Documents ({documents.length})</span>
            <button
              onClick={fetchDocuments}
              title="Refresh documents"
            >
              ↻
            </button>
          </div>

          <div className="document-list">
            {loadingDocuments ? (
              <p className="empty-documents">Loading documents...</p>
            ) : documents.length === 0 ? (
              <p className="empty-documents">No documents uploaded yet.</p>
            ) : (
              documents.map((doc) => (
                <div
                  className={`document-row ${
                    selectedPdf?.pdf_id === doc.pdf_id ? "selected" : ""
                  }`}
                  key={doc.pdf_id}
                >
                  <button
                    className="document-select"
                    onClick={() => selectDocument(doc)}
                    title={doc.filename}
                  >
                    <span>📄</span>
                    <span className="document-name">{doc.filename}</span>
                  </button>

                  <button
                    className="delete-document"
                    onClick={() => handleDelete(doc)}
                    title="Delete document"
                    aria-label={`Delete ${doc.filename}`}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="sidebar-info">
            <span>AI POWERED</span>
            <h3>Chat with your documents</h3>
            <p>Upload PDFs and find answers from their content.</p>
          </div>
        </div>

        <div className="sidebar-footer">
          <span className="status-dot"></span>
          Backend connection
          <small>Local API</small>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="topbar-title">
            <button
              className="mobile-menu-button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open documents menu"
            >
              ☰
            </button>

            <div>
              <h1>AI PDF Assistant</h1>
              <p>Ask questions. Understand documents.</p>
            </div>
          </div>

          <div className="top-badge">✦ AI Assistant</div>
        </header>

        <section className="content">
          {!selectedPdf && (
            <div className="welcome">
              <div className="welcome-icon">✦</div>
              <h2>Your documents, understood.</h2>
              <p>
                Upload one or more PDFs and let AI help you find
                the information you need.
              </p>

              <div className="upload-card">
                <div className="upload-icon">⇧</div>
                <h3>Upload your PDFs</h3>
                <p>Select PDF files up to 10 MB each.</p>

                <label className="file-button">
                  Choose PDFs
                  <input
                    type="file"
                    accept=".pdf,application/pdf"
                    multiple
                    onChange={(e) => {
                      setFiles(Array.from(e.target.files || []));
                      setError("");
                    }}
                  />
                </label>

                {files.length > 0 && (
                  <div className="selected-files">
                    {files.map((item, index) => (
                      <div className="selected-file" key={`${item.name}-${index}`}>
                        📄 {item.name}
                      </div>
                    ))}
                  </div>
                )}

                <button
                  className="primary-button"
                  onClick={handleUpload}
                  disabled={files.length === 0 || uploading}
                >
                  {uploading ? "Uploading..." : "Upload and Continue"}
                </button>

                {uploadProgress && (
                  <p className="upload-progress">{uploadProgress}</p>
                )}
              </div>

              {documents.length > 0 && (
                <p className="document-count">
                  You have {documents.length} uploaded document(s).
                  Select one from the Documents menu to start chatting.
                </p>
              )}
            </div>
          )}

          {selectedPdf && (
            <div className="chat-section">
              <div className="document-banner">
                <span>📄</span>
                <div>
                  <strong>{selectedPdf.filename}</strong>
                  <small>
                    {selectedPdf.total_chunks} text chunks · Ready for questions
                  </small>
                </div>
                <div className="document-actions">
                  <button
                    className="preview-button"
                    onClick={() =>
                      window.open(
                        `${API_URL}/documents/${selectedPdf.pdf_id}/file`,
                        "_blank",
                        "noopener,noreferrer"
                      )
                    }
                    type="button"
                  >
                    View PDF
                  </button>
                  <a
                    className="download-button"
                    href={`${API_URL}/documents/${selectedPdf.pdf_id}/file`}
                    download={selectedPdf.filename}
                  >
                    Download
                  </a>
                  <span className="ready-badge">Ready</span>
                </div>
              </div>

              <div className="messages">
                {messages.map((msg, index) => (
                  <div className={`message ${msg.role}`} key={index}>
                    <div className="avatar">
                      {msg.role === "user" ? "You" : "AI"}
                    </div>

                    <div className="message-body">
                      <strong>
                        {msg.role === "user" ? "You" : "PDF Assistant"}
                      </strong>

                      <p>{msg.text}</p>

                      {msg.sources?.length > 0 && (
                        <details className="sources">
                          <summary>
                            View PDF sources ({msg.sources.length})
                          </summary>

                          {msg.sources.map((source, i) => (
                            <div className="source-item" key={i}>
                              {typeof source === "string"
                                ? source
                                : source.text || JSON.stringify(source)}
                            </div>
                          ))}
                        </details>
                      )}
                    </div>
                  </div>
                ))}

                {asking && (
                  <div className="loading-message">
                    <span className="loader"></span>
                    AI is thinking...
                  </div>
                )}
              </div>

              <form className="chat-form" onSubmit={handleAsk}>
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask anything about your PDF..."
                  disabled={asking}
                />

                <button
                  type="submit"
                  disabled={!question.trim() || asking}
                >
                  {asking ? "..." : "Send ↑"}
                </button>
              </form>

              <p className="chat-hint">
                AI answers are based on the selected document.
              </p>

              <button
                className="new-document"
                onClick={() => {
                  setSelectedPdf(null);
                  setQuestion("");
                  setError("");
                }}
              >
                + Upload another document
              </button>
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
        </section>

        <footer className="footer">
          Built with React, FastAPI and RAG
        </footer>
      </main>
    </div>
  );
}

export default App;
