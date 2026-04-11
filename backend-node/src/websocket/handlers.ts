import { WebSocketServer } from './server';
import { sendEmail } from '../actions/email';
import { createTicket } from '../actions/ticket';
import { sendSlackNotification } from '../actions/slack';
import logger from '../config';

interface Client {
  id: string;
  ws: WebSocket;
  sessionId: string;
  lastPing: number;
  userAgent?: string;
  connectedAt: Date;
}

interface ChatMessage {
  type: 'chat';
  message: string;
  sessionId?: string;
  conversationId?: string;
}

interface ActionMessage {
  type: 'action';
  action: 'email' | 'ticket' | 'slack';
  params: any;
  messageId?: string;
}

interface PingMessage {
  type: 'ping';
}

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

export async function handleMessage(
  message: any,
  client: Client,
  wsServer: WebSocketServer
): Promise<void> {
  logger.debug(`Received message from ${client.id}:`, { type: message.type });

  client.lastPing = Date.now();

  switch (message.type) {
    case 'chat':
      await handleChatMessage(message, client, wsServer);
      break;

    case 'action':
      await handleActionMessage(message, client, wsServer);
      break;

    case 'ping':
      client.ws.send(JSON.stringify({
        type: 'pong',
        timestamp: Date.now(),
        serverTime: new Date().toISOString()
      }));
      break;

    case 'subscribe':
      if (message.sessionId) {
        client.sessionId = message.sessionId;
        client.ws.send(JSON.stringify({
          type: 'subscribed',
          sessionId: message.sessionId,
          timestamp: new Date().toISOString()
        }));
        logger.info(`Client ${client.id} subscribed to session: ${message.sessionId}`);
      }
      break;

    default:
      logger.warn(`Unknown message type: ${message.type}`);
      client.ws.send(JSON.stringify({
        type: 'error',
        error: `Unknown message type: ${message.type}`,
        timestamp: new Date().toISOString()
      }));
  }
}

async function handleChatMessage(
  message: ChatMessage,
  client: Client,
  wsServer: WebSocketServer
): Promise<void> {
  const { message: text, sessionId, conversationId } = message;

  if (!text || text.trim().length === 0) {
    client.ws.send(JSON.stringify({
      type: 'error',
      error: 'Message cannot be empty',
      timestamp: new Date().toISOString()
    }));
    return;
  }

  const activeSessionId = sessionId || client.sessionId;
  logger.info(`Chat message from session ${activeSessionId}: ${text.substring(0, 100)}`);

  // Send acknowledgment
  client.ws.send(JSON.stringify({
    type: 'ack',
    messageId: Date.now(),
    timestamp: new Date().toISOString()
  }));

  // Forward to FastAPI backend for RAG processing
  try {
    const response = await fetch(`${BACKEND_API_URL}/api/chat/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        message: text,
        session_id: activeSessionId,
        conversation_id: conversationId,
        stream: true
      })
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    if (response.body) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line);
              if (data.type === 'token' || data.content) {
                const content = data.token || data.content;
                fullResponse += content;
                client.ws.send(JSON.stringify({
                  type: 'token',
                  content: content,
                  sessionId: activeSessionId,
                  timestamp: new Date().toISOString()
                }));
              } else if (data.type === 'sources') {
                client.ws.send(JSON.stringify({
                  type: 'sources',
                  sources: data.sources,
                  sessionId: activeSessionId,
                  timestamp: new Date().toISOString()
                }));
              }
            } catch (e) {
              // Send as raw text
              client.ws.send(JSON.stringify({
                type: 'token',
                content: line,
                sessionId: activeSessionId,
                timestamp: new Date().toISOString()
              }));
            }
          }
        }
      }

      // Send completion event
      client.ws.send(JSON.stringify({
        type: 'end',
        sessionId: activeSessionId,
        fullResponse: fullResponse,
        timestamp: new Date().toISOString()
      }));

      // Store in conversation history (async, don't wait)
      fetch(`${BACKEND_API_URL}/api/chat/history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: activeSessionId,
          user_message: text,
          assistant_response: fullResponse,
          conversation_id: conversationId
        })
      }).catch(err => logger.error('Failed to store chat history:', err));

    } else {
      throw new Error('No response body from backend');
    }

  } catch (error) {
    logger.error(`Error forwarding chat message: ${error}`);
    client.ws.send(JSON.stringify({
      type: 'error',
      error: 'Failed to process message. Please try again.',
      details: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    }));
  }
}

async function handleActionMessage(
  message: ActionMessage,
  client: Client,
  wsServer: WebSocketServer
): Promise<void> {
  const { action, params, messageId } = message;

  logger.info(`Action requested: ${action} from session ${client.sessionId}`);

  let result;
  let success = false;

  try {
    switch (action) {
      case 'email':
        result = await sendEmail(params);
        success = true;
        break;

      case 'ticket':
        result = await createTicket(params);
        success = true;
        break;

      case 'slack':
        result = await sendSlackNotification(params);
        success = true;
        break;

      default:
        throw new Error(`Unknown action: ${action}`);
    }

    client.ws.send(JSON.stringify({
      type: 'action_result',
      action,
      success: true,
      result,
      messageId,
      timestamp: new Date().toISOString()
    }));

    // Notify other clients in the same session
    wsServer.sendToSession(client.sessionId, {
      type: 'action_completed',
      action,
      messageId,
      result: result,
      timestamp: new Date().toISOString()
    });

    // Emit action event to Kafka
    const { kafkaProducer } = await import('../consumers/kafka');
    if (kafkaProducer) {
      await kafkaProducer.send({
        topic: 'action-events',
        messages: [{
          value: JSON.stringify({
            action,
            result,
            sessionId: client.sessionId,
            timestamp: new Date().toISOString()
          })
        }]
      });
    }

  } catch (error) {
    logger.error(`Action failed: ${action}`, error);
    client.ws.send(JSON.stringify({
      type: 'action_result',
      action,
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
      messageId,
      timestamp: new Date().toISOString()
    }));
  }
}