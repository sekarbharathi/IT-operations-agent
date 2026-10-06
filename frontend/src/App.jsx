import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = "http://localhost:8000";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);

  /*
   * tickets = current user's own tickets
   * dashboardTickets = role-based tickets
   *   - employee -> own tickets
   *   - manager  -> team tickets
   *   - admin    -> all tickets
   */
  const [tickets, setTickets] = useState([]);
  const [dashboardTickets, setDashboardTickets] = useState([]);

  const [activePage, setActivePage] = useState("dashboard");

  /*
   * Controls which ticket collection the ticket page displays.
   *
   * my   -> current user's tickets
   * team -> manager's team tickets
   * all  -> admin's all tickets
   */
  const [ticketScope, setTicketScope] = useState("my");

  const [loadingTickets, setLoadingTickets] = useState(true);
  const [selectedTicket, setSelectedTicket] = useState(null);

  /*
   * User assigned to the selected ticket.
   */
  const [assignedUser, setAssignedUser] = useState(null);

  /*
   * User who created/requested the selected ticket.
   */
  const [ticketUser, setTicketUser] = useState(null);

  /*
   * Restore the last active conversation after refresh.
   */
  const [conversationId, setConversationId] = useState(() =>
    localStorage.getItem("opsai_conversation_id")
  );

  const [loading, setLoading] = useState(false);
  const [loadingConversations, setLoadingConversations] =
    useState(true);

  const messagesEndRef = useRef(null);

  /*
   * The tickets displayed on the ticket page.
   *
   * My Tickets -> tickets
   * Team Tickets -> dashboardTickets
   * All Tickets -> dashboardTickets
   */
  const visibleTickets =
    ticketScope === "team" || ticketScope === "all"
      ? dashboardTickets
      : tickets;

  /*
   * Load conversations and tickets when the application starts.
   */
  useEffect(() => {
    loadConversations();
    loadTickets();
    loadCurrentUser();

    const savedConversationId =
      localStorage.getItem("opsai_conversation_id");

    if (savedConversationId) {
      loadConversation(savedConversationId);
    }
  }, []);

  /*
   * Keep the active conversation ID in localStorage.
   */
  useEffect(() => {
    if (conversationId) {
      localStorage.setItem(
        "opsai_conversation_id",
        conversationId
      );
    } else {
      localStorage.removeItem(
        "opsai_conversation_id"
      );
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
       * Save conversation ID.
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
       * Refresh sidebar conversations and tickets.
       */
      await loadConversations();
      await loadTickets();

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
   * Load current user.
   */
  async function loadCurrentUser() {
    try {
      const response = await fetch(
        `${API_URL}/api/users/user_001`
      );

      const data = await response.json();

      if (response.ok) {
        setCurrentUser(data);
      }
    } catch (error) {
      console.error(
        "Failed to load current user:",
        error
      );
    }
  }

  /*
   * Load the user assigned to a ticket.
   */
  async function loadAssignedUser(userId) {
    if (!userId) {
      setAssignedUser(null);
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/users/${userId}`
      );

      const data = await response.json();

      if (response.ok) {
        setAssignedUser(data);
      } else {
        setAssignedUser(null);
      }
    } catch (error) {
      console.error(
        "Failed to load assigned user:",
        error
      );

      setAssignedUser(null);
    }
  }

  /*
   * Load the user who created/requested a ticket.
   */
  async function loadTicketUser(userId) {
    if (!userId) {
      return null;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/users/${userId}`
      );

      const data = await response.json();

      if (response.ok) {
        return data;
      }
    } catch (error) {
      console.error(
        "Failed to load ticket user:",
        error
      );
    }

    return null;
  }

  /*
   * Open a ticket and load all related user information.
   *
   * scope:
   *   my
   *   team
   *   all
   */
  async function openTicket(ticket, scope) {
    setTicketScope(scope);
    setSelectedTicket(ticket);

    /*
     * Clear old ticket information first.
     * This prevents the previous ticket's user/assignment
     * from appearing briefly.
     */
    setAssignedUser(null);
    setTicketUser(null);

    /*
     * Load assigned user.
     */
    await loadAssignedUser(ticket.assigned_to);

    /*
     * Load ticket requester.
     */
    const user = await loadTicketUser(ticket.user_id);

    setTicketUser(user);

    /*
     * Open ticket page.
     */
    setActivePage("tickets");
  }

  /*
   * Load tickets belonging to the current user
   * and role-based dashboard tickets.
   */
  async function loadTickets() {
    try {
      const userId = "user_001";

      /*
       * Load current user.
       */
      const userResponse = await fetch(
        `${API_URL}/api/users/${userId}`
      );

      const user = await userResponse.json();

      /*
       * Load current user's own tickets.
       */
      const ticketsResponse = await fetch(
        `${API_URL}/api/tickets?user_id=${userId}`
      );

      const ticketsData = await ticketsResponse.json();

      if (!ticketsData.success) {
        throw new Error(
          "Failed to load tickets"
        );
      }

      /*
       * Always keep the user's own tickets
       * separately.
       */
      setTickets(ticketsData.tickets);

      /*
       * Employee:
       * dashboard shows only their tickets.
       */
      if (user.role === "employee") {
        setDashboardTickets(
          ticketsData.tickets
        );
        return;
      }

      /*
       * Manager:
       * dashboard shows team tickets.
       */
      if (user.role === "manager") {
        const teamResponse = await fetch(
          `${API_URL}/api/tickets/team?requester_id=${userId}`
        );

        const teamData =
          await teamResponse.json();

        if (!teamData.success) {
          throw new Error(
            "Failed to load team tickets"
          );
        }

        setDashboardTickets(
          teamData.tickets
        );
        return;
      }

      /*
       * Admin:
       * dashboard shows all tickets.
       */
      if (user.role === "admin") {
        const allResponse = await fetch(
          `${API_URL}/api/tickets/all?requester_id=${userId}`
        );

        const allData =
          await allResponse.json();

        if (!allData.success) {
          throw new Error(
            "Failed to load all tickets"
          );
        }

        setDashboardTickets(
          allData.tickets
        );
      }

    } catch (error) {
      console.error(
        "Failed to load tickets:",
        error
      );
    } finally {
      setLoadingTickets(false);
    }
  }

  /*
   * Enter sends the message.
   * Shift + Enter creates a new line.
   */
  function handleKeyDown(event) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
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

    return new Date(
      dateString
    ).toLocaleDateString("en-FI", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  /*
   * Format message timestamps.
   */
  function formatTime(dateString) {
    if (!dateString) {
      return "";
    }

    return new Date(
      dateString
    ).toLocaleTimeString("en-FI", {
      hour: "2-digit",
      minute: "2-digit",
    });
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
          className={`sidebar-nav ${
            activePage === "dashboard"
              ? "active"
              : ""
          }`}
          onClick={() => {
            setSelectedTicket(null);
            setActivePage("dashboard");
          }}
        >
          Dashboard
        </button>

        <button
          className={`sidebar-nav ${
            activePage === "chat"
              ? "active"
              : ""
          }`}
          onClick={() =>
            setActivePage("chat")
          }
        >
          Chat
        </button>

        {activePage === "chat" && (
          <div className="conversations">

            <button
              className="new-chat"
              onClick={startNewChat}
              disabled={loading}
            >
              + New chat
            </button>

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
              conversations.map(
                (conversation) => (
                  <button
                    key={
                      conversation.conversation_id
                    }
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
                )
              )
            )}

          </div>
        )}

      </aside>

      {/* =================================================
          MAIN CONTENT
          ================================================= */}

      <main className="chat">

        {/* =================================================
            DASHBOARD
            ================================================= */}

        {activePage === "dashboard" && (
          <div className="page">

            <header className="chat-header">
              <div>
                <h1>
                  Dashboard
                </h1>

                <p>
                  Welcome back
                  {currentUser?.name
                    ? `, ${currentUser.name}`
                    : ""}
                </p>
              </div>
            </header>

            <div className="page-content">

              {/* =================================================
                  MANAGER SUMMARY
                  ================================================= */}

              {currentUser?.role ===
                "manager" && (
                <div className="ticket-summary">

                  <div className="summary-card">
                    <span className="summary-label">
                      My Tickets
                    </span>

                    <strong>
                      {tickets.length}
                    </strong>
                  </div>

                  <div className="summary-card">
                    <span className="summary-label">
                      Team Tickets
                    </span>

                    <strong>
                      {dashboardTickets.length}
                    </strong>
                  </div>

                  <div className="summary-card">
                    <span className="summary-label">
                      Open Tickets
                    </span>

                    <strong>
                      {
                        dashboardTickets.filter(
                          (ticket) =>
                            ticket.status ===
                            "open"
                        ).length
                      }
                    </strong>
                  </div>

                  <div className="summary-card">
                    <span className="summary-label">
                      Closed Tickets
                    </span>

                    <strong>
                      {
                        dashboardTickets.filter(
                          (ticket) =>
                            ticket.status ===
                            "closed"
                        ).length
                      }
                    </strong>
                  </div>

                </div>
              )}

              {/* =================================================
                  EMPLOYEE SUMMARY
                  ================================================= */}

              {currentUser?.role ===
                "employee" && (
                <div className="ticket-summary">

                  <div className="summary-card">
                    <span className="summary-label">
                      My Tickets
                    </span>

                    <strong>
                      {tickets.length}
                    </strong>
                  </div>

                  <div className="summary-card">
                    <span className="summary-label">
                      Open Tickets
                    </span>

                    <strong>
                      {
                        tickets.filter(
                          (ticket) =>
                            ticket.status ===
                            "open"
                        ).length
                      }
                    </strong>
                  </div>

                  <div className="summary-card">
                    <span className="summary-label">
                      Closed Tickets
                    </span>

                    <strong>
                      {
                        tickets.filter(
                          (ticket) =>
                            ticket.status ===
                            "closed"
                        ).length
                      }
                    </strong>
                  </div>

                </div>
              )}

              {/* =================================================
                  ADMIN SUMMARY
                  ================================================= */}

              {currentUser?.role ===
                "admin" && (
                <div className="ticket-summary">

                  <div className="summary-card">
                    <span className="summary-label">
                      All Tickets
                    </span>

                    <strong>
                      {dashboardTickets.length}
                    </strong>
                  </div>

                  <div className="summary-card">
                    <span className="summary-label">
                      Open Tickets
                    </span>

                    <strong>
                      {
                        dashboardTickets.filter(
                          (ticket) =>
                            ticket.status ===
                            "open"
                        ).length
                      }
                    </strong>
                  </div>

                  <div className="summary-card">
                    <span className="summary-label">
                      Closed Tickets
                    </span>

                    <strong>
                      {
                        dashboardTickets.filter(
                          (ticket) =>
                            ticket.status ===
                            "closed"
                        ).length
                      }
                    </strong>
                  </div>

                </div>
              )}

              {/* =================================================
                  MANAGER TICKETS
                  ================================================= */}

              {currentUser?.role ===
                "manager" && (
                <>
                  {/* My Tickets */}

                  <div className="recent-tickets">

                    <div className="section-header">

                      <h2>
                        My Tickets
                      </h2>

                      <button
                        onClick={() => {
                          setTicketScope("my");
                          setSelectedTicket(null);
                          setActivePage("tickets");
                        }}
                      >
                        View all
                      </button>

                    </div>

                    {tickets.length ===
                    0 ? (
                      <p className="empty-tickets">
                        No tickets yet.
                      </p>
                    ) : (
                      tickets
                        .slice(0, 5)
                        .map((ticket) => (
                          <div
                            key={ticket.id}
                            className="ticket-row"
                            onClick={() =>
                              openTicket(
                                ticket,
                                "my"
                              )
                            }
                          >

                            <div>

                              <strong>
                                {ticket.id}
                              </strong>

                              <p>
                                {
                                  ticket.description
                                }
                              </p>

                            </div>

                            <div>

                              <span className="ticket-category">
                                {
                                  ticket.category
                                }
                              </span>

                              <span className="ticket-status">
                                {
                                  ticket.status
                                }
                              </span>

                            </div>

                          </div>
                        ))
                    )}

                  </div>

                  {/* Team Tickets */}

                  <div className="recent-tickets">

                    <div className="section-header">

                      <h2>
                        Team Tickets
                      </h2>

                      <button
                        onClick={() => {
                          setTicketScope(
                            "team"
                          );
                          setSelectedTicket(null);
                          setActivePage(
                            "tickets"
                          );
                        }}
                      >
                        View all
                      </button>

                    </div>

                    {dashboardTickets.length ===
                    0 ? (
                      <p className="empty-tickets">
                        No team tickets yet.
                      </p>
                    ) : (
                      dashboardTickets
                        .slice(0, 5)
                        .map((ticket) => (
                          <div
                            key={ticket.id}
                            className="ticket-row"
                            onClick={() =>
                              openTicket(
                                ticket,
                                "team"
                              )
                            }
                          >

                            <div>

                              <strong>
                                {ticket.id}
                              </strong>

                              <p>
                                {
                                  ticket.description
                                }
                              </p>

                            </div>

                            <div>

                              <span className="ticket-category">
                                {
                                  ticket.category
                                }
                              </span>

                              <span className="ticket-status">
                                {
                                  ticket.status
                                }
                              </span>

                            </div>

                          </div>
                        ))
                    )}

                  </div>
                </>
              )}

              {/* =================================================
                  EMPLOYEE TICKETS
                  ================================================= */}

              {currentUser?.role ===
                "employee" && (
                <div className="recent-tickets">

                  <div className="section-header">

                    <h2>
                      My Tickets
                    </h2>

                    <button
                      onClick={() => {
                        setTicketScope("my");
                        setSelectedTicket(null);
                        setActivePage(
                          "tickets"
                        );
                      }}
                    >
                      View all
                    </button>

                  </div>

                  {tickets.length ===
                  0 ? (
                    <p className="empty-tickets">
                      No tickets yet.
                    </p>
                  ) : (
                    tickets
                      .slice(0, 5)
                      .map((ticket) => (
                        <div
                          key={ticket.id}
                          className="ticket-row"
                          onClick={() =>
                            openTicket(
                              ticket,
                              "my"
                            )
                          }
                        >

                          <div>

                            <strong>
                              {ticket.id}
                            </strong>

                            <p>
                              {
                                ticket.description
                              }
                            </p>

                          </div>

                          <div>

                            <span className="ticket-category">
                              {
                                ticket.category
                              }
                            </span>

                            <span className="ticket-status">
                              {
                                ticket.status
                              }
                            </span>

                          </div>

                        </div>
                      ))
                  )}

                </div>
              )}

              {/* =================================================
                  ADMIN TICKETS
                  ================================================= */}

              {currentUser?.role ===
                "admin" && (
                <div className="recent-tickets">

                  <div className="section-header">

                    <h2>
                      All Tickets
                    </h2>

                    <button
                      onClick={() => {
                        setTicketScope("all");
                        setSelectedTicket(null);
                        setActivePage(
                          "tickets"
                        );
                      }}
                    >
                      View all
                    </button>

                  </div>

                  {dashboardTickets.length ===
                  0 ? (
                    <p className="empty-tickets">
                      No tickets yet.
                    </p>
                  ) : (
                    dashboardTickets
                      .slice(0, 5)
                      .map((ticket) => (
                        <div
                          key={ticket.id}
                          className="ticket-row"
                          onClick={() =>
                            openTicket(
                              ticket,
                              "all"
                            )
                          }
                        >

                          <div>

                            <strong>
                              {ticket.id}
                            </strong>

                            <p>
                              {
                                ticket.description
                              }
                            </p>

                          </div>

                          <div>

                            <span className="ticket-category">
                              {
                                ticket.category
                              }
                            </span>

                            <span className="ticket-status">
                              {
                                ticket.status
                              }
                            </span>

                          </div>

                        </div>
                      ))
                  )}

                </div>
              )}

            </div>

          </div>
        )}

        {/* =================================================
            TICKETS PAGE
            ================================================= */}

        {activePage === "tickets" && (
          <div className="page">

            <header className="chat-header">

              <div>

                <h1>
                  {ticketScope === "team"
                    ? "Team Tickets"
                    : ticketScope === "all"
                      ? "All Tickets"
                      : "My Tickets"}
                </h1>

                <p>
                  {ticketScope === "team"
                    ? "View tickets from your team"
                    : ticketScope === "all"
                      ? "View all support tickets"
                      : "View your support tickets"}
                </p>

              </div>

            </header>

            <div className="page-content">

              {loadingTickets ? (

                <p>
                  Loading tickets...
                </p>

              ) : visibleTickets.length ===
                0 ? (

                <div className="empty-tickets">

                  <h2>
                    {ticketScope === "team"
                      ? "No team tickets yet"
                      : ticketScope === "all"
                        ? "No tickets yet"
                        : "No tickets yet"}
                  </h2>

                  <p>
                    {ticketScope === "team"
                      ? "Tickets from your team will appear here."
                      : ticketScope === "all"
                        ? "All support tickets will appear here."
                        : "Tickets you create through OpsAI will appear here."}
                  </p>

                </div>

              ) : selectedTicket ? (

                /* =================================================
                   TICKET DETAILS
                   ================================================= */

                <div className="ticket-details">

                  <button
                    className="back-button"
                    onClick={() => {
                      setSelectedTicket(null);
                      setAssignedUser(null);
                      setTicketUser(null);
                    }}
                  >
                    ← Back to{" "}
                    {ticketScope === "team"
                      ? "Team Tickets"
                      : ticketScope === "all"
                        ? "All Tickets"
                        : "My Tickets"}
                  </button>

                  <div className="ticket-details-card">

                    {/* Ticket header */}

                    <div className="ticket-details-header">

                      <div>

                        <span className="ticket-details-id">
                          {selectedTicket.id}
                        </span>

                        <h2>
                          {
                            selectedTicket.category
                          }{" "}
                          issue
                        </h2>

                      </div>

                      <span className="ticket-status">
                        {
                          selectedTicket.status
                        }
                      </span>

                    </div>

                    {/* Ticket information */}

                    <div className="ticket-details-section">

                      <h3>
                        Ticket information
                      </h3>

                      <div className="ticket-info-grid">

                        <div>

                          <span className="ticket-info-label">
                            Ticket ID
                          </span>

                          <strong>
                            {
                              selectedTicket.id
                            }
                          </strong>

                        </div>

                        <div>

                          <span className="ticket-info-label">
                            Requested by
                          </span>

                          <strong>
                            {ticketUser?.name ||
                              selectedTicket.user_id}
                          </strong>

                        </div>

                        <div>

                          <span className="ticket-info-label">
                            Category
                          </span>

                          <strong>
                            {
                              selectedTicket.category
                            }
                          </strong>

                        </div>

                        <div>

                          <span className="ticket-info-label">
                            Status
                          </span>

                          <strong>
                            {
                              selectedTicket.status
                            }
                          </strong>

                        </div>

                        <div>

                          <span className="ticket-info-label">
                            Created
                          </span>

                          <strong>
                            {formatDate(
                              selectedTicket.created_at
                            )}
                          </strong>

                        </div>

                      </div>

                    </div>

                    {/* Description */}

                    <div className="ticket-details-section">

                      <h3>
                        Description
                      </h3>

                      <p className="ticket-full-description">
                        {
                          selectedTicket.description
                        }
                      </p>

                    </div>

                    {/* Assignment */}

                    <div className="ticket-details-section">

                      <h3>
                        Assignment
                      </h3>

                      <div className="assigned-person">

                        <div className="assigned-avatar">

                          {assignedUser?.name
                            ? assignedUser.name
                                .split(" ")
                                .map(
                                  (part) =>
                                    part[0]
                                )
                                .join("")
                                .slice(0, 2)
                                .toUpperCase()
                            : "—"}

                        </div>

                        <div>

                          <strong>
                            {assignedUser?.name ||
                              "Not assigned"}
                          </strong>

                          <span>
                            {assignedUser?.team ||
                              "No team assigned"}
                          </span>

                        </div>

                      </div>

                    </div>

                    {/* Activity */}

                    <div className="ticket-details-section">

                      <h3>
                        Activity
                      </h3>

                      <div className="ticket-activity">

                        <div className="activity-item">

                          <div className="activity-dot"></div>

                          <div>

                            <strong>
                              Ticket created
                            </strong>

                            <p>
                              OpsAI created this
                              ticket on behalf
                              of the user.
                            </p>

                            <small>
                              {formatDate(
                                selectedTicket.created_at
                              )}
                            </small>

                          </div>

                        </div>

                        {selectedTicket.assigned_to && (
                          <div className="activity-item">

                            <div className="activity-dot"></div>

                            <div>

                              <strong>
                                Ticket assigned
                              </strong>

                              <p>
                                The ticket is
                                assigned to{" "}
                                {assignedUser?.name ||
                                  "an IT team member"}.
                              </p>

                              <small>
                                {formatDate(
                                  selectedTicket.created_at
                                )}
                              </small>

                            </div>

                          </div>
                        )}

                      </div>

                    </div>

                  </div>

                </div>

              ) : (

                /* =================================================
                   TICKET LIST
                   ================================================= */

                <div className="tickets-list">

                  {visibleTickets.map(
                    (ticket) => (
                      <div
                        key={ticket.id}
                        className="ticket-card"
                        onClick={() =>
                          openTicket(
                            ticket,
                            ticketScope
                          )
                        }
                      >

                        <div className="ticket-card-header">

                          <div>

                            <strong>
                              {ticket.id}
                            </strong>

                            <span className="ticket-category">
                              {
                                ticket.category
                              }
                            </span>

                          </div>

                          <span className="ticket-status">
                            {
                              ticket.status
                            }
                          </span>

                        </div>

                        <p className="ticket-description">
                          {
                            ticket.description
                          }
                        </p>

                        <div className="ticket-meta">
                          Created{" "}
                          {formatDate(
                            ticket.created_at
                          )}
                        </div>

                      </div>
                    )
                  )}

                </div>

              )}

            </div>

          </div>
        )}

        {/* =================================================
            CHAT
            ================================================= */}

        {activePage === "chat" && (
          <>

            {/* Header */}

            <header className="chat-header">

              <div>

                <h1>
                  OpsAI
                </h1>

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
                    Ask about incidents,
                    tickets, users,
                    permissions, or IT
                    troubleshooting.
                  </p>

                </div>

              ) : (

                messages.map(
                  (item, index) => (

                    <div
                      key={index}
                      className={`message ${item.role}`}
                    >

                      <div className="message-wrapper">

                        {item.role ===
                          "assistant" && (
                          <div className="message-role">
                            OpsAI
                          </div>
                        )}

                        <div className="message-content">

                          {item.role ===
                          "assistant" ? (

                            <ReactMarkdown
                              remarkPlugins={[
                                remarkGfm,
                              ]}
                            >
                              {item.content}
                            </ReactMarkdown>

                          ) : (

                            item.content

                          )}

                        </div>

                      </div>

                    </div>

                  )
                )

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

              <div
                ref={messagesEndRef}
              />

            </div>

            {/* Input */}

            <div className="input-area">

              <div className="input-container">

                <textarea
                  rows="1"
                  placeholder="Ask OpsAI..."
                  value={message}
                  onChange={(event) =>
                    setMessage(
                      event.target.value
                    )
                  }
                  onKeyDown={handleKeyDown}
                  disabled={loading}
                />

                <button
                  onClick={sendMessage}
                  disabled={
                    loading ||
                    !message.trim()
                  }
                >
                  {loading
                    ? "..."
                    : "Send"}
                </button>

              </div>

              <p className="input-hint">
                Enter to send · Shift +
                Enter for a new line
              </p>

            </div>

          </>
        )}

      </main>

    </div>
  );
}

export default App;