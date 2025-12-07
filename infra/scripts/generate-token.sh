#!/bin/bash

# Скрипт для генерации безопасного Bearer токена для MCP аутентификации

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Генерация Bearer токена для MCP аутентификации${NC}"
echo ""

# Проверяем наличие openssl
if ! command -v openssl &> /dev/null; then
    echo -e "${YELLOW}⚠️  openssl не найден. Используем Python...${NC}"
    TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")
else
    TOKEN=$(openssl rand -hex 32)
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Токен успешно сгенерирован!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}🔑 Ваш Bearer токен:${NC}"
echo ""
echo -e "   ${GREEN}${TOKEN}${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 Как использовать:${NC}"
echo ""
echo "1. Добавьте в файл ${GREEN}infra/.env${NC}:"
echo ""
echo -e "   ${BLUE}MCP_AUTH_ENABLED=true${NC}"
echo -e "   ${BLUE}MCP_AUTH_TOKEN=${TOKEN}${NC}"
echo ""
echo "2. Используйте в клиентских запросах:"
echo ""
echo -e "   ${BLUE}Authorization: Bearer ${TOKEN}${NC}"
echo ""
echo "3. Пример cURL запроса:"
echo ""
echo -e "   ${BLUE}curl -H \"Authorization: Bearer ${TOKEN}\" \\${NC}"
echo -e "   ${BLUE}     https://your-server.com/mcp/v1/${NC}"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
echo "  • Храните токен в безопасности"
echo "  • Не коммитьте токен в git"
echo "  • Используйте разные токены для dev/staging/production"
echo "  • Меняйте токены регулярно (каждые 90 дней)"
echo ""
echo -e "${GREEN}🎉 Готово!${NC}"
