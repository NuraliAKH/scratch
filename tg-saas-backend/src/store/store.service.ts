import { Injectable, ConflictException, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class StoreService {
  constructor(private prisma: PrismaService) {}

  async create(userId: string, data: { name: string; botToken: string; subdomain: string }) {
    const existingStore = await this.prisma.store.findFirst({
      where: { OR: [{ botToken: data.botToken }, { subdomain: data.subdomain }] },
    });

    if (existingStore) {
      throw new ConflictException('Store with this botToken or subdomain already exists');
    }

    return this.prisma.store.create({
      data: {
        ...data,
        ownerId: userId,
        config: {},
      },
    });
  }

  async findAllByUser(userId: string) {
    return this.prisma.store.findMany({
      where: { ownerId: userId },
    });
  }

  async update(userId: string, storeId: string, data: any) {
    const store = await this.prisma.store.findUnique({ where: { id: storeId } });
    if (!store || store.ownerId !== userId) {
      throw new NotFoundException('Store not found or access denied');
    }

    if (data.botToken || data.subdomain) {
      const existingStore = await this.prisma.store.findFirst({
        where: {
          id: { not: storeId },
          OR: [
            { botToken: data.botToken || undefined },
            { subdomain: data.subdomain || undefined },
          ],
        },
      });

      if (existingStore) {
        throw new ConflictException('botToken or subdomain already in use');
      }
    }

    return this.prisma.store.update({
      where: { id: storeId },
      data,
    });
  }
}
