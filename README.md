# بروكسي فيديو

بروكسي بسيط مكتوب بـ Flask لنشر الفيديوهات.

## كيفية النشر على Vercel

### الطريقة الأولى: عبر GitHub
1. ارفع الكود إلى GitHub
2. اذهب إلى [vercel.com](https://vercel.com)
3. سجل دخول بحساب GitHub
4. اضغط "New Project"
5. اختر المستودع
6. اضغط "Deploy"

### الطريقة الثانية: عبر Vercel CLI
1. ثبت Vercel CLI:
```bash
npm i -g vercel
```

2. سجل دخول:
```bash
vercel login
```

3. انشر المشروع:
```bash
vercel
```

## كيفية الاستخدام

بعد النشر، يمكنك استخدام البروكسي كالتالي:

```
https://your-domain.vercel.app/proxy?url=https://example.com/video.mp4
```

## ملاحظات مهمة

- البروكسي مقيد حالياً بالدومين `valiw.hakunaymatata.com`
- يمكنك تعديل `ALLOWED_HOSTS` في الكود لإضافة دومينات أخرى
- البروكسي يدعم byte-range requests للفيديوهات
- يحتوي على CORS headers للاستخدام من صفحات أخرى
