import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class ProductService {
  constructor(private prisma: PrismaService) {}

  private async checkStoreOwnership(userId: string, storeId: string) {
    const store = await this.prisma.store.findUnique({ where: { id: storeId } });
    if (!store || store.ownerId !== userId) {
      throw new ForbiddenException('Store not found or access denied');
    }
    return store;
  }

  async create(userId: string, storeId: string, data: { title: string; description: string; price: number; stock?: number; images?: string[] }) {
    await this.checkStoreOwnership(userId, storeId);

    return this.prisma.product.create({
      data: {
        ...data,
        storeId,
      },
    });
  }

  async findAllByStore(storeId: string) {
    return this.prisma.product.findMany({
      where: { storeId },
    });
  }

  async update(userId: string, productId: string, data: any) {
    const product = await this.prisma.product.findUnique({ where: { id: productId } });
    if (!product) throw new NotFoundException('Product not found');

    await this.checkStoreOwnership(userId, product.storeId);

    return this.prisma.product.update({
      where: { id: productId },
      data,
    });
  }

  async delete(userId: string, productId: string) {
    const product = await this.prisma.product.findUnique({ where: { id: productId } });
    if (!product) throw new NotFoundException('Product not found');

    await this.checkStoreOwnership(userId, product.storeId);

    return this.prisma.product.delete({
      where: { id: productId },
    });
  }
}
