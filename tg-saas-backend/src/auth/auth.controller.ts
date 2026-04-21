import { Controller, Post, Body } from '@nestjs/common';
import { AuthService } from './auth.service';

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('login/webapp')
  async loginWebApp(@Body('initData') initData: string) {
    // BigInt serialization is tricky in default NestJS JSON.
    // We stringify the return or map tgId to string.
    const result = await this.authService.loginWithInitData(initData);
    return {
      access_token: result.access_token,
      user: {
        ...result.user,
        tgId: result.user.tgId.toString(),
      }
    };
  }
}
