import { Controller, Post, Get, Put, Delete, Body, Param, UseGuards, Req } from '@nestjs/common';
import { ProductService } from './product.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { Request } from 'express';

@Controller('products')
export class ProductController {
  constructor(private readonly productService: ProductService) {}

  @Post(':storeId')
  @UseGuards(JwtAuthGuard)
  create(
    @Req() req: Request,
    @Param('storeId') storeId: string,
    @Body() body: { title: string; description: string; price: number; stock?: number; images?: string[] },
  ) {
    const userId = (req as any).user.sub;
    return this.productService.create(userId, storeId, body);
  }

  // Публичный эндпоинт: любой может смотреть товары магазина (для WebApp)
  @Get(':storeId')
  findAllByStore(@Param('storeId') storeId: string) {
    return this.productService.findAllByStore(storeId);
  }

  @Put(':id')
  @UseGuards(JwtAuthGuard)
  update(@Req() req: Request, @Param('id') id: string, @Body() body: any) {
    const userId = (req as any).user.sub;
    return this.productService.update(userId, id, body);
  }

  @Delete(':id')
  @UseGuards(JwtAuthGuard)
  delete(@Req() req: Request, @Param('id') id: string) {
    const userId = (req as any).user.sub;
    return this.productService.delete(userId, id);
  }
}
