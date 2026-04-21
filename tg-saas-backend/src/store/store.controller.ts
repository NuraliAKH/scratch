import { Controller, Post, Get, Put, Body, UseGuards, Req, Param } from '@nestjs/common';
import { StoreService } from './store.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { Request } from 'express';

@Controller('stores')
@UseGuards(JwtAuthGuard)
export class StoreController {
  constructor(private readonly storeService: StoreService) {}

  @Post()
  create(@Req() req: Request, @Body() body: { name: string; botToken: string; subdomain: string }) {
    const userId = (req as any).user.sub;
    return this.storeService.create(userId, body);
  }

  @Get()
  findAllByUser(@Req() req: Request) {
    const userId = (req as any).user.sub;
    return this.storeService.findAllByUser(userId);
  }

  @Put(':id')
  update(@Req() req: Request, @Param('id') storeId: string, @Body() body: any) {
    const userId = (req as any).user.sub;
    return this.storeService.update(userId, storeId, body);
  }
}
