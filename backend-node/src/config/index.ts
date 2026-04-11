import winston from 'winston';
import dotenv from 'dotenv';

dotenv.config();

// Logger configuration
const logger = winston.createLogger({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.json()
  ),
  defaultMeta: { service: 'docintel-node' },
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' })
  ]
});

// Configuration object
export const config = {
  port: parseInt(process.env.PORT || '3001'),
  nodeEnv: process.env.NODE_ENV || 'development',

  redis: {
    url: process.env.REDIS_URL || 'redis://localhost:6379'
  },

  kafka: {
    brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(','),
    clientId: process.env.KAFKA_CLIENT_ID || 'docintel-node',
    groupId: process.env.KAFKA_GROUP_ID || 'docintel-group',
    topics: {
      documents: 'document-events',
      queries: 'query-events',
      actions: 'action-events'
    }
  },

  email: {
    host: process.env.SMTP_HOST,
    port: parseInt(process.env.SMTP_PORT || '587'),
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
    from: process.env.SMTP_FROM || process.env.SMTP_USER
  },

  slack: {
    webhookUrl: process.env.SLACK_WEBHOOK_URL
  },

  ticket: {
    apiUrl: process.env.TICKET_API_URL,
    apiToken: process.env.TICKET_API_TOKEN,
    projectKey: process.env.TICKET_PROJECT_KEY || 'DOC'
  },

  backend: {
    apiUrl: process.env.BACKEND_API_URL || 'http://localhost:8000'
  },

  webhook: {
    secret: process.env.WEBHOOK_SECRET || 'default-secret-change-me'
  }
};

export default logger;