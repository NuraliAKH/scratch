import { Injectable, ForbiddenException, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { OrderStatus } from '@prisma/client';
import { NotificationService } from '../notification/notification.service';

@Injectable()
export class OrderService {
  constructor(
    private prisma: PrismaService,
    private notificationService: NotificationService,
  ) {}

  async create(customerId: string, storeId: string, items: any[], totalAmount: number) {
    const order = await this.prisma.order.create({
      data: {
        storeId,
        customerId,
        items,
        totalAmount,
        status: OrderStatus.PENDING,
      },
      include: {
        store: { include: { owner: true } }
      }
    });

    // Уведомляем продавца о новом заказе
    const vendorTgId = order.store.owner.tgId;
    await this.notificationService.sendToVendor(
      vendorTgId,
      `🛍 <b>Новый заказ!</b>\nСумма: ${totalAmount}\nID: ${order.id}`
    );

    return order;
  }

  async findAllByStore(userId: string, storeId: string) {
    const store = await this.prisma.store.findUnique({ where: { id: storeId } });
    if (!store || store.ownerId !== userId) {
      throw new ForbiddenException('Store not found or access denied');
    }

    return this.prisma.order.findMany({
      where: { storeId },
      orderBy: { createdAt: 'desc' },
    });
  }

  async updateStatus(userId: string, orderId: string, status: OrderStatus) {
    const order = await this.prisma.order.findUnique({
      where: { id: orderId },
      include: { store: true },
    });

    if (!order) throw new NotFoundException('Order not found');
    if (order.store.ownerId !== userId) {
      throw new ForbiddenException('Access denied');
    }

    const updated = await this.prisma.order.update({
      where: { id: orderId },
      data: { status },
    });

    // Получаем пользователя, чтобы узнать его tgId
    const customer = await this.prisma.user.findUnique({ where: { id: order.customerId } });

    if (customer) {
      // Уведомляем покупателя об изменении статуса
      await this.notificationService.sendToCustomer(
        order.store.botToken,
        customer.tgId,
        `Ваш заказ #${order.id.slice(0, 5)} изменил статус на: <b>${status}</b>`
      );
    }

    return updated;
  }
}
