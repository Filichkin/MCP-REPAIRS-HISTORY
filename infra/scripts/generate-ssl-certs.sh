#!/bin/bash

# =============================================================================
# Скрипт генерации Self-Signed SSL сертификатов для разработки
# =============================================================================
# Этот скрипт создает самоподписанные SSL сертификаты для использования
# с nginx в локальной разработке. НЕ используйте эти сертификаты в продакшене!
#
# Для продакшена используйте Let's Encrypt или корпоративный CA.
# =============================================================================

set -e

# Определяем директории
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CERTS_DIR="$PROJECT_ROOT/infra/certs"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Параметры сертификата
CERT_DAYS=365
CERT_SUBJECT="/C=RU/ST=Moscow/L=Moscow/O=Development/CN=mcp-server.local"
CERT_FILE="mcp-server.crt"
KEY_FILE="mcp-server.key"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Генерация Self-Signed SSL сертификатов${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Проверяем наличие openssl
if ! command -v openssl &> /dev/null; then
    echo -e "${RED}Ошибка: openssl не установлен${NC}"
    echo "Установите openssl:"
    echo "  macOS: brew install openssl"
    echo "  Ubuntu/Debian: sudo apt-get install openssl"
    echo "  CentOS/RHEL: sudo yum install openssl"
    exit 1
fi

# Создаем директорию для сертификатов если её нет
if [ ! -d "$CERTS_DIR" ]; then
    echo -e "${YELLOW}Создание директории: $CERTS_DIR${NC}"
    mkdir -p "$CERTS_DIR"
fi

# Проверяем существующие сертификаты
if [ -f "$CERTS_DIR/$CERT_FILE" ] || [ -f "$CERTS_DIR/$KEY_FILE" ]; then
    echo -e "${YELLOW}Найдены существующие сертификаты:${NC}"
    [ -f "$CERTS_DIR/$CERT_FILE" ] && echo "  - $CERT_FILE"
    [ -f "$CERTS_DIR/$KEY_FILE" ] && echo "  - $KEY_FILE"
    echo ""
    read -p "Перезаписать существующие сертификаты? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Операция отменена${NC}"
        exit 0
    fi
fi

echo -e "${GREEN}Генерация приватного ключа и сертификата...${NC}"
echo ""

# Генерируем приватный ключ и сертификат
openssl req -x509 \
    -nodes \
    -days $CERT_DAYS \
    -newkey rsa:2048 \
    -keyout "$CERTS_DIR/$KEY_FILE" \
    -out "$CERTS_DIR/$CERT_FILE" \
    -subj "$CERT_SUBJECT" \
    -addext "subjectAltName=DNS:localhost,DNS:mcp-server.local,IP:127.0.0.1"

# Устанавливаем правильные права доступа
chmod 600 "$CERTS_DIR/$KEY_FILE"
chmod 644 "$CERTS_DIR/$CERT_FILE"

echo ""
echo -e "${GREEN}Сертификаты успешно сгенерированы:${NC}"
echo -e "  Сертификат: ${BLUE}$CERTS_DIR/$CERT_FILE${NC}"
echo -e "  Приватный ключ: ${BLUE}$CERTS_DIR/$KEY_FILE${NC}"
echo ""
echo -e "${YELLOW}Информация о сертификате:${NC}"
openssl x509 -in "$CERTS_DIR/$CERT_FILE" -noout -subject -dates -ext subjectAltName
echo ""
echo -e "${YELLOW}Важно:${NC}"
echo -e "  1. Эти сертификаты самоподписанные и предназначены только для разработки"
echo -e "  2. Браузеры будут показывать предупреждение о безопасности"
echo -e "  3. Срок действия: $CERT_DAYS дней"
echo -e "  4. Для продакшена используйте Let's Encrypt или корпоративный CA"
echo ""
echo -e "${GREEN}Готово!${NC}"
