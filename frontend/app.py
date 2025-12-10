'''
Gradio frontend for Warranty Agent System.

Минималистичный чат-интерфейс для взаимодействия с агентной системой
анализа гарантийных обращений.
'''

import httpx
import gradio as gr
from typing import Any

from config import settings


async def query_agent(
    message: str,
    history: list[dict[str, str]]
) -> str:
    '''
    Отправить запрос к агентной системе.

    Args:
        message: Текст запроса пользователя (VIN можно указать в тексте)
        history: История чата (не используется в текущей реализации)

    Returns:
        Ответ от агентной системы
    '''
    if not message.strip():
        return 'Пожалуйста, введите запрос.'

    try:
        async with httpx.AsyncClient(timeout=settings.chat_timeout) as client:
            payload: dict[str, Any] = {
                'query': message.strip(),
                'context': {}
            }

            response = await client.post(
                f'{settings.api_base_url}/agent/query',
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
        # Заголовок
        gr.Markdown(
            '# Система истории ремонтов и обслуживания автомобилей\n'
            '*Интеллектуальный помощник для работы с историей ремонтов*'
        )

        # Основная область чата
        with gr.Row():
            with gr.Column(scale=7):
                chatbot = gr.Chatbot(
                    label='💬 Диалог с AI агентом',
                    height=settings.chat_height,
                    show_label=True
                )

                with gr.Row():
                    msg = gr.Textbox(
                        label='Ваш запрос',
                        placeholder=(
                            'Например: "Сколько дней автомобиль с VIN '
                            'Z94C251BBLR102931 был в ремонте?"'
                        ),
                        scale=9,
                        max_lines=settings.max_message_lines,
                        show_label=False,
                        container=False
                    )
                    submit_btn = gr.Button(
                        'Отправить',
                        scale=1,
                        variant='secondary',
                        size='lg'
                    )

            # Боковая панель с примерами
            with gr.Column(scale=3):
                gr.Markdown('### 📋 Примеры запросов')
                gr.Markdown(
                    '**Общие вопросы:**\n'
                    '• Что делать если превысим сроки ремонта?\n'
                    '• Какие права у клиента при гарантии?\n'
                    '• Расскажи о процедуре возврата\n\n'
                    '**Запросы с VIN:**\n'
                    '• История для VIN Z94C251BBLR102931\n'
                    '• Сколько дней в ремонте Z94C251BBLR102931?\n'
                    '• Анализ ремонтов у дилера для VIN...\n\n'
                    '*VIN можно указать прямо в тексте запроса*'
                )

                gr.Markdown('---')
                gr.Markdown('### 🤖 Мультиагентная система')
                gr.Markdown(
                    '**Возможности:**\n\n'
                    '✓ Анализ истории ремонтов\n\n'
                    '✓ Проверка гарантийных условий\n\n'
                    '✓ Оценка рисков и сроков\n\n'
                    '✓ Генерация детальных отчётов'
                )

        # Футер с информацией
        gr.Markdown('---')
        gr.Markdown(
            '*💡 Система использует AI для анализа данных '
            'и предоставления ответов*'
        )

        async def respond(
            message: str,
            chat_history: list[dict[str, str]]
        ) -> tuple[str, list[dict[str, str]]]:
            '''
            Обработать пользовательский запрос и обновить чат.

            Args:
                message: Сообщение пользователя
                chat_history: История чата

            Returns:
                Очищенное поле ввода и обновленная история чата
            '''
            bot_message = await query_agent(message, chat_history)
            chat_history.append({'role': 'user', 'content': message})
            chat_history.append({'role': 'assistant', 'content': bot_message})
            return '', chat_history

        msg.submit(
            respond,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )

        submit_btn.click(
            respond,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )

    return interface


if __name__ == '__main__':
    # Создание темы для Gradio 6.x
    theme = gr.themes.Soft(
        primary_hue='purple',
        secondary_hue='blue',
        neutral_hue='slate',
        font=['Arial', 'sans-serif']
    )

    # CSS для кастомизации шрифта
    custom_css = '''
        * {
            font-family: Arial, sans-serif !important;
        }
    '''

    app = create_interface()
    app.launch(
        server_name=settings.ui_server_name,
        server_port=settings.ui_server_port,
        share=settings.ui_share,
        theme=theme,
        css=custom_css
    )
