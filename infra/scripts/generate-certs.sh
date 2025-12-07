#!/bin/bash

# Скрипт для генерации self-signed SSL сертификатов
# Используется для разработки и тестирования
# ⚠️  Для production используйте сертификаты от Let's Encrypt или коммерческого CA

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Генерация self-signed SSL сертификатов для MCP сервера${NC}"
echo ""

# Создаем директорию для сертификатов
CERTS_DIR="../certs"
mkdir -p "$CERTS_DIR"

# Параметры сертификата
CERT_DAYS=365
CERT_COUNTRY="RU"
CERT_STATE="Moscow"
CERT_CITY="Moscow"
CERT_ORG="MCP Repairs History"
CERT_CN="localhost"

echo -e "${YELLOW}📋 Параметры сертификата:${NC}"
echo "  Срок действия: $CERT_DAYS дней"
echo "  Страна: $CERT_COUNTRY"
echo "  Регион: $CERT_STATE"
echo "  Город: $CERT_CITY"
echo "  Организация: $CERT_ORG"
echo "  Common Name: $CERT_CN"
echo ""

# Генерируем приватный ключ
echo -e "${GREEN}🔑 Генерация приватного ключа...${NC}"
openssl genrsa -out "$CERTS_DIR/mcp-server.key" 2048

# Генерируем сертификат
echo -e "${GREEN}📜 Генерация самоподписанного сертификата...${NC}"
openssl req -new -x509 -days $CERT_DAYS \
    -key "$CERTS_DIR/mcp-server.key" \
    -out "$CERTS_DIR/mcp-server.crt" \
    -subj "/C=$CERT_COUNTRY/ST=$CERT_STATE/L=$CERT_CITY/O=$CERT_ORG/CN=$CERT_CN"

# Устанавливаем правильные права доступа
chmod 600 "$CERTS_DIR/mcp-server.key"
chmod 644 "$CERTS_DIR/mcp-server.crt"

echo ""
echo -e "${GREEN}✅ Сертификаты успешно созданы!${NC}"
echo ""
echo -e "${YELLOW}📂 Файлы сертификатов:${NC}"
echo "  Приватный ключ: $CERTS_DIR/mcp-server.key"
echo "  Сертификат: $CERTS_DIR/mcp-server.crt"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
echo "  1. Эти сертификаты предназначены ТОЛЬКО для разработки/тестирования"
echo "  2. Браузеры будут показывать предупреждение о недоверенном сертификате"
echo "  3. Для production используйте сертификаты от Let's Encrypt или CA"
echo ""
echo -e "${YELLOW}📖 Использование:${NC}"
echo "  - Для Docker Compose: сертификаты уже в правильной директории"
echo "  - Для nginx: настройте пути в infra/nginx/conf.d/mcp-server.conf"
echo "    ssl_certificate /etc/nginx/certs/mcp-server.crt;"
echo "    ssl_certificate_key /etc/nginx/certs/mcp-server.key;"
echo ""
echo -e "${GREEN}🎉 Готово!${NC}"
