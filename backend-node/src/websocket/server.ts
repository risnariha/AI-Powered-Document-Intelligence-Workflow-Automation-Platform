import WebSocket, { WebSocketServer as WSServer } from 'ws';
import { Server as HTTPServer } from 'http';
import { v4 as uuidv4 } from 'uuid';
import { handleMessage } from './handlers';
import logger from '../config';

interface Client {
  id: string;
  ws: WebSocket;
  sessionId: string;
  lastPing: number;
  userAgent?: string;
  connectedAt: Date;
}

export class WebSocketServer {
  private wss: WSServer | null = null;
  private clients: Map<string, Client> = new Map();
  private server: HTTPServer;
  private pingInterval: NodeJS.Timeout | null = null;

  constructor(server: HTTPServer) {
    this.server = server;
  }

  initialize(): void {
    this.wss = new WSServer({ server: this.server, path: '/ws' });

    this.wss.on('connection', (ws: WebSocket, req) => {
      const clientId = uuidv4();
      const url = new URL(req.url || '', `http://${req.headers.host}`);
      const sessionId = url.searchParams.get('sessionId') || 'default';
      const userAgent = req.headers['user-agent'];

      const client: Client = {
        id: clientId,
        ws,
        sessionId,
        lastPing: Date.now(),
        userAgent,
        connectedAt: new Date()
      };

      this.clients.set(clientId, client);
      logger.info(`WebSocket client connected: ${clientId} (session: ${sessionId})`);

      // Send welcome message
      ws.send(JSON.stringify({
        type: 'connected',
        clientId,
        sessionId,
        timestamp: new Date().toISOString(),
        message: 'Connected to Document Intelligence Platform'
      }));

      // Handle incoming messages
      ws.on('message', async (data: WebSocket.RawData) => {
        try {
          const message = JSON.parse(data.toString());
          await handleMessage(message, client, this);
        } catch (error) {
          logger.error(`Error handling message: ${error}`);
          ws.send(JSON.stringify({
            type: 'error',
            error: 'Invalid message format',
            timestamp: new Date().toISOString()
          }));
        }
      });

      // Handle pong responses
      ws.on('pong', () => {
        client.lastPing = Date.now();
      });

      // Handle close
      ws.on('close', (code, reason) => {
        this.clients.delete(clientId);
        logger.info(`WebSocket client disconnected: ${clientId}, code: ${code}, reason: ${reason.toString()}`);
      });

      // Handle errors
      ws.on('error', (error) => {
        logger.error(`WebSocket error for client ${clientId}:`, error);
      });
    });

    // Heartbeat to detect stale connections
    this.pingInterval = setInterval(() => {
      const now = Date.now();
      this.clients.forEach((client, id) => {
        if (now - client.lastPing > 30000) {
          logger.info(`Closing stale connection: ${id}`);
          client.ws.terminate();
          this.clients.delete(id);
        } else if (client.ws.readyState === WebSocket.OPEN) {
          client.ws.ping();
        }
      });
    }, 10000);

    logger.info('WebSocket server initialized on path: /ws');
  }

  sendToClient(clientId: string, message: any): boolean {
    const client = this.clients.get(clientId);
    if (client && client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  sendToSession(sessionId: string, message: any): void {
    let sentCount = 0;
    this.clients.forEach((client) => {
      if (client.sessionId === sessionId && client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify(message));
        sentCount++;
      }
    });
    if (sentCount > 0) {
      logger.debug(`Sent message to ${sentCount} clients in session ${sessionId}`);
    }
  }

  broadcast(message: any, excludeClientId?: string): void {
    let sentCount = 0;
    this.clients.forEach((client) => {
      if (client.id !== excludeClientId && client.ws.readyState === WebSocket.OPEN) {
        client.ws.send(JSON.stringify(message));
        sentCount++;
      }
    });
    logger.debug(`Broadcast message to ${sentCount} clients`);
  }

  getClientCount(): number {
    return this.clients.size;
  }

  getSessionClients(sessionId: string): Client[] {
    const clients: Client[] = [];
    this.clients.forEach((client) => {
      if (client.sessionId === sessionId) {
        clients.push(client);
      }
    });
    return clients;
  }

  disconnectClient(clientId: string): void {
    const client = this.clients.get(clientId);
    if (client) {
      client.ws.close(1000, 'Server shutdown');
      this.clients.delete(clientId);
    }
  }

  shutdown(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    this.clients.forEach((client) => {
      client.ws.close(1000, 'Server shutdown');
    });

    if (this.wss) {
      this.wss.close();
    }

    logger.info('WebSocket server shutdown');
  }
}