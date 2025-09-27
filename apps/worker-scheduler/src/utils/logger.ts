// apps/worker-scheduler/src/utils/logger.ts - Logging Utility
export class Logger {
  private static instance: Logger;
  
  public static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }

  private formatMessage(level: string, message: string, meta?: any): string {
    const timestamp = new Date().toISOString();
    const metaStr = meta ? ` ${JSON.stringify(meta)}` : '';
    return `[${timestamp}] ${level.toUpperCase()}: ${message}${metaStr}`;
  }

  public info(message: string, meta?: any): void {
    console.log(this.formatMessage('info', message, meta));
  }

  public error(message: string, error?: Error | any): void {
    const meta = error ? { 
      message: error.message, 
      stack: error.stack,
      ...(typeof error === 'object' ? error : {})
    } : undefined;
    console.error(this.formatMessage('error', message, meta));
  }

  public warn(message: string, meta?: any): void {
    console.warn(this.formatMessage('warn', message, meta));
  }

  public debug(message: string, meta?: any): void {
    if (process.env.NODE_ENV === 'development') {
      console.debug(this.formatMessage('debug', message, meta));
    }
  }
}

export const logger = Logger.getInstance();