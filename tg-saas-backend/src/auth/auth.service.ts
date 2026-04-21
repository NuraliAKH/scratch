import { Injectable, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { JwtService } from '@nestjs/jwt';
import { PrismaService } from '../prisma/prisma.service';
import * as crypto from 'crypto';

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwtService: JwtService,
    private configService: ConfigService,
  ) {}

  // Валидация данных, приходящих от Telegram WebApp (initData)
  validateTelegramInitData(initData: string): any {
    const urlParams = new URLSearchParams(initData);
    const hash = urlParams.get('hash');
    urlParams.delete('hash');
    
    // Сортируем параметры по алфавиту
    const dataCheckString = Array.from(urlParams.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, value]) => `${key}=${value}`)
      .join('\n');

    const botToken = this.configService.get<string>('TELEGRAM_BOT_TOKEN');
    if (!botToken) {
        // Для тестов, если токена нет, просто пропускаем (только для отладки!)
        console.warn('TELEGRAM_BOT_TOKEN is not set!');
    }

    const secretKey = crypto.createHmac('sha256', 'WebAppData').update(botToken || '').digest();
    const calculatedHash = crypto.createHmac('sha256', secretKey).update(dataCheckString).digest('hex');

    if (calculatedHash !== hash && botToken) {
      throw new UnauthorizedException('Invalid Telegram initData');
    }

    // Возвращаем распарсенного юзера
    const userString = urlParams.get('user');
    if (!userString) throw new UnauthorizedException('No user data');
    
    return JSON.parse(userString);
  }

  async loginWithInitData(initData: string) {
    const tgUser = this.validateTelegramInitData(initData);

    // Ищем или создаем пользователя в БД
    let user = await this.prisma.user.findUnique({
      where: { tgId: tgUser.id },
    });

    if (!user) {
      user = await this.prisma.user.create({
        data: {
          tgId: tgUser.id,
          // По умолчанию роль USER
        },
      });
    }

    const payload = { sub: user.id, tgId: Number(user.tgId), role: user.role };
    return {
      access_token: this.jwtService.sign(payload),
      user,
    };
  }
}
