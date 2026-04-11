import express, { Application, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import { createServer } from 'http';

import { WebSocketServer } from './websocket/server';
import webhookRouter from './webhooks/router';
import { startKafkaConsumer } from './consumers/kafka';
import logger from './config';

dotenv.config();

const app: Application = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:8000', 'http://localhost:3001'],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    service: 'docintel-node-backend',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    websocket_clients: wsServer?.getClientCount() || 0
  });
});

// API routes
app.use('/api/webhooks', webhookRouter);

// Root endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'Document Intelligence Platform - Node.js Backend',
    version: '1.0.0',
    services: {
      websocket: 'ws://localhost:' + PORT,
      webhooks: '/api/webhooks',
      health: '/health'
    }
  });
});

// Error handling middleware
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error(`Error: ${err.message}`, { stack: err.stack });
  res.status(500).json({
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// 404 handler
app.use((req: Request, res: Response) => {
  res.status(404).json({ error: 'Route not found' });
});

// Create HTTP server
const server = createServer(app);

// Initialize WebSocket server
const wsServer = new WebSocketServer(server);
wsServer.initialize();

// Start Kafka consumer
let kafkaConsumer: any = null;
startKafkaConsumer(wsServer).catch(err => {
  logger.error('Failed to start Kafka consumer:', err);
});

// Graceful shutdown
const gracefulShutdown = async () => {
  logger.info('SIGTERM received, closing server...');

  wsServer.shutdown();

  if (kafkaConsumer) {
    await kafkaConsumer.disconnect();
  }

  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Start server
server.listen(PORT, () => {
  logger.info(`Node.js backend running on port ${PORT}`);
  logger.info(`WebSocket server available at ws://localhost:${PORT}`);
  logger.info(`Health check: http://localhost:${PORT}/health`);
});

export default app;