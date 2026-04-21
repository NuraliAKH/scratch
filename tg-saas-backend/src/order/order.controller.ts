import { Controller, Post, Get, Put, Body, Param, UseGuards, Req } from '@nestjs/common';
import { OrderService } from './order.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { Request } from 'express';
import { OrderStatus } from '@prisma/client';

@Controller('orders')
@UseGuards(JwtAuthGuard)
export class OrderController {
  constructor(private readonly orderService: OrderService) {}

  // Покупатель создает заказ
  @Post()
  create(
    @Req() req: Request,
    @Body() body: { storeId: string; items: any[]; totalAmount: number },
  ) {
    const customerId = (req as any).user.sub;
    return this.orderService.create(customerId, body.storeId, body.items, body.totalAmount);
  }

  // Продавец смотрит заказы своего магазина
  @Get('store/:storeId')
  findAllByStore(@Req() req: Request, @Param('storeId') storeId: string) {
    const userId = (req as any).user.sub;
    return this.orderService.findAllByStore(userId, storeId);
  }

  // Продавец меняет статус заказа
  @Put(':id/status')
  updateStatus(
    @Req() req: Request,
    @Param('id') id: string,
    @Body('status') status: OrderStatus,
  ) {
    const userId = (req as any).user.sub;
    return this.orderService.updateStatus(userId, id, status);
  }
}
