import {
  useRef,
  useState,
  type FormEvent,
} from 'react'
import {
  Bot,
  BrainCircuit,
  RotateCw,
  Send,
  Server,
  ShieldCheck,
} from 'lucide-react'
import {
  Link,
} from 'react-router-dom'
import {
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  createActionProposal,
  type ActionProposal,
} from '../api/actions'
import {
  getAgents,
} from '../api/agents'
import {
  getConversationMessages,
  getConversations,
  sendChat,
} from '../api/ai'
import {
  ApiError,
} from '../api/http'
import { useAuth } from '../auth/useAuth'

type ChatEntry = {
  id: string
  role: 'user' | 'assistant'
  content: string
  meta?: string
}

type ContainerOption = {
  name: string
  state: string
}

function dockerContainers(
  value: Array<Record<string, unknown>> | undefined,
): ContainerOption[] {
  if (!value) {
    return []
  }

  return value.flatMap((row) => {
    const name = row.name
    const state = row.state

    if (typeof name !== 'string') {
      return []
    }

    return [{
      name,
      state:
        typeof state === 'string'
          ? state
          : 'unknown',
    }]
  })
}

export function AIAssistant() {
  const auth = useAuth()

  const token =
    auth.tokens?.access_token

  const workspaceId =
    auth.workspace?.id

  const queryClient = useQueryClient()

  const agents = useQuery({
    queryKey: [
      'agents',
      workspaceId,
    ],
    queryFn: () =>
      getAgents(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 15_000,
  })

  const conversations = useQuery({
    queryKey: [
      'ai-conversations',
      workspaceId,
    ],
    queryFn: () =>
      getConversations(
        token!,
        workspaceId!,
      ),
    enabled: Boolean(
      token && workspaceId,
    ),
    refetchInterval: 30_000,
  })

  const [resourceId, setResourceId] =
    useState('')

  const [conversationId, setConversationId] =
    useState<string | null>(null)

  const [message, setMessage] =
    useState('')

  const [messages, setMessages] =
    useState<ChatEntry[]>([])

  const [sending, setSending] =
    useState(false)

  const [chatError, setChatError] =
    useState<string | null>(null)

  const [
    loadingConversationId,
    setLoadingConversationId,
  ] = useState<string | null>(null)

  const [
    historyError,
    setHistoryError,
  ] = useState<string | null>(null)

  const historyRequestRef =
    useRef(0)

  const [container, setContainer] =
    useState('')

  const [actionIntent, setActionIntent] =
    useState('')

  const [proposal, setProposal] =
    useState<ActionProposal | null>(null)

  const [proposalError, setProposalError] =
    useState<string | null>(null)

  const [proposing, setProposing] =
    useState(false)

  const selectedAgent =
    agents.data?.find(
      (agent) =>
        agent.resource_id === resourceId,
    )

  const containers = dockerContainers(
    selectedAgent?.metrics
      ?.docker?.containers,
  )

  function selectResource(
    nextResourceId: string,
  ) {
    historyRequestRef.current += 1
    setLoadingConversationId(null)
    setHistoryError(null)
    setResourceId(nextResourceId)
    setConversationId(null)
    setMessages([])
    setContainer('')
    setProposal(null)
    setChatError(null)
    setProposalError(null)
  }

  function startNewConversation() {
    historyRequestRef.current += 1
    setLoadingConversationId(null)
    setHistoryError(null)
    setConversationId(null)
    setMessages([])
    setChatError(null)
  }

  async function selectConversation(
    nextConversationId: string,
  ) {
    if (!token || !workspaceId) {
      return
    }

    const requestId =
      historyRequestRef.current + 1

    historyRequestRef.current =
      requestId

    setLoadingConversationId(
      nextConversationId,
    )
    setHistoryError(null)
    setChatError(null)
    setConversationId(
      nextConversationId,
    )
    setMessages([])

    try {
      const history =
        await getConversationMessages(
          token,
          workspaceId,
          nextConversationId,
        )

      if (
        historyRequestRef.current
        !== requestId
      ) {
        return
      }

      setMessages(
        history.map((entry) => ({
          id: entry.id,
          role:
            entry.role === 'user'
              ? 'user'
              : 'assistant',
          content: entry.content,
        })),
      )
    } catch (error) {
      if (
        historyRequestRef.current
        !== requestId
      ) {
        return
      }

      setConversationId(null)
      setMessages([])
      setHistoryError(
        error instanceof ApiError
          ? error.detail
          : 'conversation_history_failed',
      )
    } finally {
      if (
        historyRequestRef.current
        === requestId
      ) {
        setLoadingConversationId(null)
      }
    }
  }

  async function submitChat(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const cleanMessage = message.trim()

    if (
      !token
      || !workspaceId
      || !cleanMessage
    ) {
      return
    }

    const userEntry: ChatEntry = {
      id: crypto.randomUUID(),
      role: 'user',
      content: cleanMessage,
    }

    setMessages((current) => [
      ...current,
      userEntry,
    ])

    setMessage('')
    setSending(true)
    setChatError(null)

    try {
      const response = await sendChat(
        token,
        workspaceId,
        cleanMessage,
        resourceId || undefined,
        conversationId,
      )

      setConversationId(
        response.conversation_id,
      )

      setMessages((current) => [
        ...current,
        {
          id: response.message_id,
          role: 'assistant',
          content: response.answer,
          meta:
            `${response.mode} · ${response.model}`,
        },
      ])

      await queryClient.invalidateQueries({
        queryKey: [
          'ai-conversations',
          workspaceId,
        ],
      })
    } catch (error) {
      setChatError(
        error instanceof ApiError
          ? error.detail
          : 'ai_chat_failed',
      )
    } finally {
      setSending(false)
    }
  }

  async function proposeAction(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const cleanIntent =
      actionIntent.trim()

    if (
      !token
      || !workspaceId
      || !resourceId
      || !container
      || cleanIntent.length < 3
    ) {
      return
    }

    setProposing(true)
    setProposalError(null)
    setProposal(null)

    try {
      const result =
        await createActionProposal(
          token,
          workspaceId,
          resourceId,
          cleanIntent,
          container,
        )

      setProposal(result)
    } catch (error) {
      setProposalError(
        error instanceof ApiError
          ? error.detail
          : 'action_proposal_failed',
      )
    } finally {
      setProposing(false)
    }
  }

  return (
    <>
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Infrastructure intelligence
          </p>
          <h1>AI Assistant</h1>
          <p>
            Analyze live infrastructure and
            prepare policy-controlled actions.
          </p>
        </div>

        <div className="system-pill system-pill--online">
          <BrainCircuit size={16} />
          CONTROLLED AI
        </div>
      </header>

      <section className="ai-layout">
        <div className="ai-main">
          <article className="panel ai-resource-panel">
            <label className="field-label">
              <Server size={16} />
              Resource context
            </label>

            <select
              className="control-select"
              value={resourceId}
              onChange={(event) =>
                selectResource(
                  event.target.value,
                )
              }
            >
              <option value="">
                No resource context
              </option>

              {agents.data?.map((agent) => (
                <option
                  key={agent.resource_id}
                  value={agent.resource_id}
                >
                  {agent.hostname}
                  {' · '}
                  {agent.status}
                </option>
              ))}
            </select>
          </article>

          <article className="panel chat-panel">
            <div className="chat-history">
              {messages.length === 0 && (
                <div className="chat-empty">
                  <BrainCircuit size={30} />
                  <strong>
                    Infrastructure AI
                  </strong>
                  <span>
                    Select a resource and ask
                    about health, telemetry or
                    Docker state.
                  </span>
                </div>
              )}

              {messages.map((entry) => (
                <div
                  key={entry.id}
                  className={
                    entry.role === 'user'
                      ? 'chat-message chat-message--user'
                      : 'chat-message chat-message--assistant'
                  }
                >
                  <div className="chat-message__role">
                    {entry.role === 'user'
                      ? 'YOU'
                      : 'AI SRV'}
                  </div>

                  <div>
                    {entry.content}
                  </div>

                  {entry.meta && (
                    <small>
                      {entry.meta}
                    </small>
                  )}
                </div>
              ))}

              {sending && (
                <div className="chat-message chat-message--assistant">
                  <div className="chat-message__role">
                    AI SRV
                  </div>
                  <div>
                    Analyzing infrastructure…
                  </div>
                </div>
              )}
            </div>

            {chatError && (
              <div className="auth-error">
                {chatError}
              </div>
            )}

            <form
              className="chat-form"
              onSubmit={submitChat}
            >
              <textarea
                value={message}
                onChange={(event) =>
                  setMessage(
                    event.target.value,
                  )
                }
                placeholder="Ask about this infrastructure..."
                maxLength={8000}
                rows={3}
              />

              <button
                className="primary-button"
                type="submit"
                disabled={
                  sending
                  || message.trim().length === 0
                }
              >
                <Send size={16} />
                Send
              </button>
            </form>
          </article>
        </div>

        <aside className="ai-side">
          <article className="panel">
            <div className="panel__title">
              <Bot size={19} />
              <h2>Conversation history</h2>
            </div>

            <button
              type="button"
              className="sidebar-action"
              disabled={
                sending
                || loadingConversationId
                  !== null
              }
              onClick={startNewConversation}
            >
              New conversation
            </button>

            {conversations.isLoading && (
              <div className="placeholder">
                Loading conversations…
              </div>
            )}

            {conversations.isError && (
              <div className="auth-error">
                Conversation history
                unavailable.
              </div>
            )}

            {historyError && (
              <div className="auth-error">
                {historyError}
              </div>
            )}

            {conversations.isSuccess
              && conversations.data.length
                === 0
              && (
                <div className="placeholder">
                  No previous conversations.
                </div>
              )}

            <div className="ops-list">
              {conversations.data?.map(
                (conversation) => (
                  <button
                    type="button"
                    className="sidebar-action"
                    key={conversation.id}
                    disabled={
                      sending
                      || loadingConversationId
                        !== null
                    }
                    onClick={() =>
                      void selectConversation(
                        conversation.id,
                      )
                    }
                  >
                    <strong>
                      {conversation.title}
                    </strong>

                    <span>
                      {loadingConversationId
                        === conversation.id
                        ? 'Loading…'
                        : new Date(
                            conversation.updated_at,
                          ).toLocaleString()}
                    </span>

                    {conversationId
                      === conversation.id
                      && (
                        <span>
                          SELECTED
                        </span>
                      )}
                  </button>
                ),
              )}
            </div>
          </article>

          <article className="panel">
            <div className="panel__title">
              <ShieldCheck size={19} />
              <h2>Action Proposal</h2>
            </div>

            {!resourceId && (
              <div className="placeholder">
                Select a resource first.
              </div>
            )}

            {resourceId
              && containers.length === 0
              && (
                <div className="placeholder">
                  No Docker containers are
                  available in the latest
                  inventory.
                </div>
              )}

            {resourceId
              && containers.length > 0
              && (
                <form
                  className="action-form"
                  onSubmit={proposeAction}
                >
                  <label className="field-label">
                    Container
                  </label>

                  <select
                    className="control-select"
                    value={container}
                    onChange={(event) =>
                      setContainer(
                        event.target.value,
                      )
                    }
                    required
                  >
                    <option value="">
                      Select container
                    </option>

                    {containers.map((item) => (
                      <option
                        key={item.name}
                        value={item.name}
                      >
                        {item.name}
                        {' · '}
                        {item.state}
                      </option>
                    ))}
                  </select>

                  <label className="field-label">
                    Operator intent
                  </label>

                  <textarea
                    value={actionIntent}
                    onChange={(event) =>
                      setActionIntent(
                        event.target.value,
                      )
                    }
                    placeholder="Explain why this restart is needed..."
                    minLength={3}
                    maxLength={2000}
                    rows={4}
                    required
                  />

                  <button
                    className="primary-button"
                    type="submit"
                    disabled={
                      proposing
                      || !container
                      || actionIntent
                        .trim()
                        .length < 3
                    }
                  >
                    <RotateCw size={16} />
                    {proposing
                      ? 'Evaluating policy…'
                      : 'Create proposal'}
                  </button>
                </form>
              )}

            {proposalError && (
              <div className="auth-error action-feedback">
                {proposalError}
              </div>
            )}

            {proposal && (
              <div className="proposal-card">
                <div className="proposal-card__header">
                  <strong>
                    Proposal created
                  </strong>

                  <span className="status-badge">
                    RISK {proposal.risk_level}
                  </span>
                </div>

                <code>
                  {proposal.capability}
                </code>

                <p>
                  {proposal.rationale}
                </p>

                <div className="proposal-policy">
                  Approval required:{' '}
                  <strong>
                    {proposal.requires_approval
                      ? 'YES'
                      : 'NO'}
                  </strong>
                </div>

                <Link
                  className="primary-button"
                  to="/actions"
                >
                  Review action
                </Link>
              </div>
            )}
          </article>

          <article className="panel">
            <div className="panel__title">
              <Bot size={19} />
              <h2>Safety boundary</h2>
            </div>

            <div className="safety-list">
              <span>
                AI provides recommendations.
              </span>
              <span>
                Backend selects capabilities.
              </span>
              <span>
                Policy controls execution.
              </span>
              <span>
                Mutations require approval.
              </span>
            </div>
          </article>
        </aside>
      </section>
    </>
  )
}
