import { Controller, Post, Body, Param, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Controller('webhook')
export class WebhookController {
  private readonly logger = new Logger(WebhookController.name);

  constructor(private prisma: PrismaService) {}

  @Post('telegram/:storeId')
  async handleTelegramWebhook(@Param('storeId') storeId: string, @Body() body: any) {
    this.logger.log(`Received webhook for store ${storeId}: ${JSON.stringify(body)}`);
    // Здесь будет логика обработки /start команд и прочих сообщений от бота магазина
    return { ok: true };
  }
}
