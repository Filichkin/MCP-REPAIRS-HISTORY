import asyncio

from fastmcp import Client


MCP_URL = 'http://0.0.0.0:8004/mcp'
TEST_VIN = 'XWEG3417BN0009095'
TEST_QUERY = 'Что делать в случае повторного ремонта?'


async def main():
    client = Client(MCP_URL)

    async with client:
        # Проверим, что клиент достучался
        tools = await client.list_tools()
        print('🔧 Доступные инструменты:', [tool.name for tool in tools])
        print()

        # Тест 1: Статистика дней в ремонте
        print('=' * 60)
        print('1️⃣  Тестируем warranty_days')
        print('=' * 60)
        result = await client.call_tool(
            'warranty_days',
            arguments={'vin': TEST_VIN}
        )
        print('📊 Результат:\n\n', result.content[0].text)
        print()

        # Тест 2: История гарантийных обращений
        print('=' * 60)
        print('2️⃣  Тестируем warranty_history')
        print('=' * 60)
        result = await client.call_tool(
            'warranty_history',
            arguments={'vin': TEST_VIN}
        )
        print('🔧 Результат:\n\n', result.content[0].text)
        print()

        # Тест 3: История техобслуживания
        print('=' * 60)
        print('3️⃣  Тестируем maintenance_history')
        print('=' * 60)
        result = await client.call_tool(
            'maintenance_history',
            arguments={'vin': TEST_VIN}
        )
        print('🛠️  Результат:\n\n', result.content[0].text)
        print()

        # Тест 4: История ремонтов DNM
        print('=' * 60)
        print('4️⃣  Тестируем vehicle_repairs_history')
        print('=' * 60)
        result = await client.call_tool(
            'vehicle_repairs_history',
            arguments={'vin': TEST_VIN}
        )
        print('🚗 Результат:\n\n', result.content[0].text)
        print()

        # Тест 5: RAG - поиск в базе знаний
        print('=' * 60)
        print('5️⃣  Тестируем compliance_rag')
        print('=' * 60)
        result = await client.call_tool(
            'compliance_rag',
            arguments={'query': TEST_QUERY}
        )
        print('📚 Результат:\n\n', result.content[0].text)
        print()

        print('✅ Все тесты завершены!')


if __name__ == '__main__':
    asyncio.run(main())
