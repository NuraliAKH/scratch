import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Telegraf } from 'telegraf';

@Injectable()
export class NotificationService {
  private readonly logger = new Logger(NotificationService.name);
  private bot: Telegraf;

  constructor(private configService: ConfigService) {
    const token = this.configService.get<string>('TELEGRAM_BOT_TOKEN');
    if (token) {
      this.bot = new Telegraf(token);
    } else {
      this.logger.warn('TELEGRAM_BOT_TOKEN is not defined, notifications will not be sent.');
    }
  }

  async sendToVendor(tgId: string | number | BigInt, message: string) {
    if (!this.bot) return;
    try {
      await this.bot.telegram.sendMessage(tgId.toString(), message, { parse_mode: 'HTML' });
    } catch (error) {
      this.logger.error(`Failed to send message to vendor ${tgId}:`, error);
    }
  }

  async sendToCustomer(botToken: string, tgId: string | number | BigInt, message: string) {
    // Для отправки от имени бота конкретного магазина
    try {
      const storeBot = new Telegraf(botToken);
      await storeBot.telegram.sendMessage(tgId.toString(), message, { parse_mode: 'HTML' });
    } catch (error) {
      this.logger.error(`Failed to send message to customer ${tgId} using bot ${botToken.slice(0, 5)}...:`, error);
    }
  }
}
