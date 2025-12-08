'''
Gradio frontend for Warranty Agent System.

Минималистичный чат-интерфейс для взаимодействия с агентной системой
анализа гарантийных обращений.
'''

import httpx
import gradio as gr
from typing import Any


API_BASE_URL = 'http://localhost:8005'


async def query_agent(
    message: str,
    history: list[dict[str, str]],
    vin: str = ''
) -> str:
    '''
    Отправить запрос к агентной системе.

    Args:
        message: Текст запроса пользователя
        history: История чата (не используется в текущей реализации)
        vin: Опциональный VIN автомобиля

    Returns:
        Ответ от агентной системы
    '''
    if not message.strip():
        return 'Пожалуйста, введите запрос.'

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload: dict[str, Any] = {
                'query': message.strip(),
                'context': {}
            }

            if vin and vin.strip():
                payload['vin'] = vin.strip()

            response = await client.post(
                f'{API_BASE_URL}/agent/query',
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                return data.get('response', 'Ответ не получен.')
            else:
                error_detail = response.json().get(
                    'detail',
                    'Неизвестная ошибка'
                )
                return f'Ошибка: {error_detail}'

    except httpx.TimeoutException:
        return 'Превышено время ожидания ответа от сервера.'
    except httpx.ConnectError:
        return (
            'Не удалось подключиться к серверу. '
            'Убедитесь, что API сервер запущен.'
        )
    except Exception as e:
        return f'Произошла ошибка: {str(e)}'


def create_interface() -> gr.Blocks:
    '''
    Создать Gradio интерфейс для чата.

    Returns:
        Gradio Blocks интерфейс
    '''
    with gr.Blocks(title='Warranty Agent System') as interface:
        gr.Markdown(
            '# Система анализа гарантийных обращений\n'
            'Задайте вопрос о гарантийных случаях, '
            'ремонтах или истории обслуживания.'
        )

        with gr.Row():
            with gr.Column(scale=1):
                vin_input = gr.Textbox(
                    label='VIN автомобиля (необязательно)',
                    placeholder='Z94C251BBLR102931',
                    max_lines=1,
                    info=(
                        'Можно задавать общие вопросы без VIN или '
                        'указать VIN для конкретного автомобиля'
                    )
                )

                gr.Markdown(
                    '**Примеры запросов:**\n\n'
                    '*Общие вопросы (без VIN):*\n'
                    '- Что делать если превысим сроки ремонта?\n'
                    '- Какие права у клиента при гарантии?\n\n'
                    '*С указанием VIN:*\n'
                    '- Сколько дней автомобиль был в ремонте?\n'
                    '- История обслуживания автомобиля\n'
                    '- Анализ частоты ремонтов у дилера'
                )

        chatbot = gr.Chatbot(label='Диалог', height=500)

        with gr.Row():
            msg = gr.Textbox(
                label='Ваш запрос',
                placeholder='Введите вопрос...',
                scale=9,
                max_lines=3
            )
            submit_btn = gr.Button('Отправить', scale=1, variant='primary')

        gr.Markdown(
            '---\n'
            '*Система использует мультиагентный подход '
            'для анализа гарантийных данных.*'
        )

        async def respond(
            message: str,
            chat_history: list[dict[str, str]],
            vin: str
        ) -> tuple[str, list[dict[str, str]]]:
            '''
            Обработать пользовательский запрос и обновить чат.

            Args:
                message: Сообщение пользователя
                chat_history: История чата
                vin: VIN автомобиля

            Returns:
                Очищенное поле ввода и обновленная история чата
            '''
            bot_message = await query_agent(message, chat_history, vin)
            chat_history.append({'role': 'user', 'content': message})
            chat_history.append({'role': 'assistant', 'content': bot_message})
            return '', chat_history

        msg.submit(
            respond,
            inputs=[msg, chatbot, vin_input],
            outputs=[msg, chatbot]
        )

        submit_btn.click(
            respond,
            inputs=[msg, chatbot, vin_input],
            outputs=[msg, chatbot]
        )

    return interface


if __name__ == '__main__':
    app = create_interface()
    app.launch(
        server_name='0.0.0.0',
        server_port=7860,
        share=False
    )
