import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = "http://localhost:8000";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);

  // Restore the last active conversation after refresh
  const [conversationId, setConversationId] = useState(() =>
    localStorage.getItem("opsai_conversation_id")
  );

  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] =
    useState(true);

  const messagesEndRef = useRef(null);

  /*
   * Load conversations when the application starts.
   *
   * If a conversation was active before refresh,
   * load that conversation as well.
   */
  useEffect(() => {
    loadConversations();

    const savedConversationId =
      localStorage.getItem("opsai_conversation_id");

    if (savedConversationId) {
      loadConversation(savedConversationId);
    }
  }, []);

  /*
   * Keep the active conversation ID in localStorage.
   *
   * This is what allows the same conversation to
   * remain active after a browser refresh.
   */
  useEffect(() => {
    if (conversationId) {
      localStorage.setItem(
        "opsai_conversation_id",
        conversationId
      );
    } else {
      localStorage.removeItem("opsai_conversation_id");
    }
  }, [conversationId]);

  /*
   * Automatically scroll to the newest message.
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  /*
   * Load conversation list.
   */
  async function loadConversations() {
    try {
      const response = await fetch(
        `${API_URL}/api/chat/conversations`
      );

      const data = await response.json();

      if (data.success) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error(
        "Failed to load conversations:",
        error
      );
    } finally {
      setLoadingConversations(false);
    }
  }

  /*
   * Load a specific conversation.
   */
  async function loadConversation(id) {
    if (loading) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/chat/${id}/messages`
      );

      const data = await response.json();

      if (!data.success) {
        throw new Error(
          data.error || "Failed to load conversation"
        );
      }

      setConversationId(id);

      setMessages(
        data.messages.map((item) => ({
          role: item.role,
          content: item.content,
          created_at: item.created_at,
        }))
      );
    } catch (error) {
      console.error(
        "Failed to load conversation:",
        error
      );

      /*
       * If the saved conversation no longer exists
       * in the backend, clear the invalid ID.
       */
      localStorage.removeItem(
        "opsai_conversation_id"
      );

      setConversationId(null);
      setMessages([]);
    }
  }

  /*
   * Send a message to OpsAI.
   */
  async function sendMessage() {
    if (!message.trim() || loading) {
      return;
    }

    const userMessage = message.trim();

    /*
     * Immediately show the user's message.
     */
    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userMessage,
        created_at: new Date().toISOString(),
      },
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: userMessage,
            conversation_id: conversationId,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(
          data.error || "Something went wrong"
        );
      }

      /*
       * The backend gives us the conversation ID.
       *
       * This will also be saved to localStorage by
       * the conversationId useEffect above.
       */
      setConversationId(data.conversation_id);

      /*
       * Add OpsAI's response.
       */
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.response,
          created_at: new Date().toISOString(),
        },
      ]);

      /*
       * Refresh the sidebar conversation list.
       */
      await loadConversations();
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: `Error: ${error.message}`,
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  /*
   * Enter sends the message.
   * Shift + Enter creates a new line.
   */
  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  /*
   * Start a completely new conversation.
   */
  function startNewChat() {
    setMessages([]);
    setConversationId(null);
    setMessage("");

    /*
     * Explicitly remove the saved conversation.
     */
    localStorage.removeItem(
      "opsai_conversation_id"
    );
  }

  /*
   * Format sidebar dates.
   */
  function formatDate(dateString) {
    if (!dateString) {
      return "";
    }

    return new Date(dateString).toLocaleDateString(
      "en-FI",
      {
        day: "numeric",
        month: "short",
        year: "numeric",
      }
    );
  }

  /*
   * Format message timestamps.
   */
  function formatTime(dateString) {
    if (!dateString) {
      return "";
    }

    return new Date(dateString).toLocaleTimeString(
      "en-FI",
      {
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  }

  return (
    <div className="app">

      {/* =================================================
          SIDEBAR
          ================================================= */}

      <aside className="sidebar">

        <div className="logo">
          OpsAI
        </div>

        <button
          className="new-chat"
          onClick={startNewChat}
          disabled={loading}
        >
          + New chat
        </button>

        <div className="conversations">

          <p className="sidebar-label">
            Conversations
          </p>

          {loadingConversations ? (
            <p className="empty-conversations">
              Loading...
            </p>
          ) : conversations.length === 0 ? (
            <p className="empty-conversations">
              No conversations yet
            </p>
          ) : (
            conversations.map((conversation) => (
              <button
                key={conversation.conversation_id}
                className={`conversation-item ${
                  conversationId ===
                  conversation.conversation_id
                    ? "active"
                    : ""
                }`}
                onClick={() =>
                  loadConversation(
                    conversation.conversation_id
                  )
                }
                disabled={loading}
              >
                <span>
                  {conversation.title ||
                    "New conversation"}
                </span>

                <small>
                  {formatDate(
                    conversation.updated_at
                  )}
                </small>
              </button>
            ))
          )}

        </div>

      </aside>

      {/* =================================================
          CHAT
          ================================================= */}

      <main className="chat">

        {/* Header */}

        <header className="chat-header">

          <div>
            <h1>OpsAI</h1>

            <p>
              IT Operations Assistant
            </p>
          </div>

        </header>

        {/* Messages */}

        <div className="messages">

          {messages.length === 0 ? (

            <div className="welcome">

              <h2>
                How can I help?
              </h2>

              <p>
                Ask about incidents, tickets,
                users, permissions, or IT
                troubleshooting.
              </p>

            </div>

          ) : (

            messages.map((item, index) => (

              <div
                key={index}
                className={`message ${item.role}`}
              >

                <div className="message-wrapper">

                  {/* Assistant label */}

                  {item.role === "assistant" && (
                    <div className="message-role">
                      OpsAI
                    </div>
                  )}

                  {/* Message */}

                  <div className="message-content">
                    {item.role === "assistant" ? (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {item.content}
                      </ReactMarkdown>
                    ) : (
                      item.content
                    )}
                  </div>

                

                </div>

              </div>

            ))

          )}

          {/* Typing indicator */}

          {loading && (

            <div className="message assistant">

              <div className="message-wrapper">

                <div className="message-role">
                  OpsAI
                </div>

                <div className="message-content typing">

                  <span></span>
                  <span></span>
                  <span></span>

                </div>

              </div>

            </div>

          )}

          <div ref={messagesEndRef} />

        </div>

        {/* =================================================
            INPUT
            ================================================= */}

        <div className="input-area">

          <div className="input-container">

            <textarea
              rows="1"
              placeholder="Ask OpsAI..."
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              onKeyDown={handleKeyDown}
              disabled={loading}
            />

            <button
              onClick={sendMessage}
              disabled={
                loading || !message.trim()
              }
            >
              {loading ? "..." : "Send"}
            </button>

          </div>

          <p className="input-hint">
            Enter to send · Shift + Enter for a new line
          </p>

        </div>

      </main>

    </div>
  );
}

export default App;
