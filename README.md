# AI Scalp Hunter 🤖🎯

بوت تيليغرام ذكي لتحليل السكالبينغ باستخدام الذكاء الاصطناعي.

## المميزات
- تحليل 23 زوج عملات
- فلترة ذكية Top 15
- ذكاء اصطناعي (Groq) لاختيار أفضل فرصتين
- شارت احترافي مع مؤشرات فنية
- منع التكرار
- تجربة مستخدم سلسة

## التشغيل محلياً
1. انسخ `.env.example` إلى `.env` وأضف التوكنات
2. ثبت المكتبات: `pip install -r requirements.txt`
3. شغل البوت: `python bot.py`

## النشر على Render
1. ارفع المشروع على GitHub
2. في Render: New → Background Worker → Docker
3. أضف المتغيرات البيئية
4. Create Worker

## المتغيرات البيئية المطلوبة
- `TELEGRAM_TOKEN`
- `TWELVEDATA_API_KEY`
- `GROQ_API_KEY`
