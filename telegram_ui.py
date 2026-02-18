"""
telegram_ui.py
AI Scalp Hunter | Telegram Interface
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

from config import TELEGRAM_TOKEN
from bot_runner import run_scalp_analysis


class TelegramUI:
    def __init__(self):
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self.user_locks = {}

        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("🎯 اصطاد سكالبينغ", callback_data="hunt")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🔍 **AI Scalp Hunter**\n\n"
            "اضغط الزر لبدء التحليل الذكي.\n"
            "⏳ يستغرق التحليل 20–40 ثانية.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id

        if self.user_locks.get(user_id, False):
            await query.answer("⚠️ التحليل جارٍ حالياً...", show_alert=True)
            return

        self.user_locks[user_id] = True
        progress_msg = None

        try:
            progress_msg = await query.edit_message_text(
                "🔍 **AI Scalp Hunter**\n\n"
                "⏳ جاري التحليل...\n\n"
                "⚪ جلب البيانات\n"
                "⚪ حساب المؤشرات\n"
                "⚪ فلترة أفضل 15\n"
                "⚪ الذكاء الاصطناعي يحلل\n"
                "⚪ حساب الثقة\n"
                "⚪ التحقق من التكرار\n"
                "⚪ تجهيز النتائج",
                parse_mode="Markdown"
            )

            result = await run_scalp_analysis(
                progress_callback=lambda stage: self.update_progress(progress_msg, stage)
            )

            if result and len(result) > 0:
                for signal in result:
                    if signal.get("chart_path"):
                        with open(signal["chart_path"], "rb") as photo:
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id,
                                photo=photo,
                                caption=signal["message"],
                                parse_mode="Markdown"
                            )
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=signal["message"],
                            parse_mode="Markdown"
                        )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=(
                        "🔍 **AI Scalp Hunter**\n\n"
                        "❌ لا توجد فرصة قوية حالياً (أقل من 65% ثقة).\n\n"
                        "⏳ انتظر 5–10 دقائق وحاول مجدداً."
                    ),
                    parse_mode="Markdown"
                )

        except Exception as e:
            logging.exception("Error during analysis")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ حدث خطأ أثناء التحليل.\nحاول مجدداً بعد قليل."
            )

        finally:
            self.user_locks[user_id] = False
            if progress_msg:
                try:
                    await progress_msg.delete()
                except Exception:
                    pass

    async def update_progress(self, message, stage: int):
        stages = [
            "جلب البيانات",
            "حساب المؤشرات",
            "فلترة أفضل 15",
            "الذكاء الاصطناعي يحلل",
            "حساب الثقة",
            "التحقق من التكرار",
            "تجهيز النتائج"
        ]

        text = "🔍 **AI Scalp Hunter**\n\n⏳ جاري التحليل...\n\n"

        for i, s in enumerate(stages, 1):
            if i < stage:
                text += f"✅ {s}\n"
            elif i == stage:
                text += f"⏳ {s}\n"
            else:
                text += f"⚪ {s}\n"

        try:
            await message.edit_text(text, parse_mode="Markdown")
        except BadRequest:
            pass

        await asyncio.sleep(0.4)

    def run(self):
        logging.info("🚀 Starting AI Scalp Hunter...")
        self.app.run_polling(drop_pending_updates=True)
