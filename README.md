# 💎 MLBB Diamond Top-up Telegram Bot

MLBB Diamond top-up order management bot တစ်ခု။ Render (Free) တွင် host လုပ်ထားသည်။

---

## ✨ Features

- 💎 Diamond packages ပြသခြင်း (86 မှ 9288 အထိ)
- 2x Diamond packages
- Weekly Pass
- Order တင်ခြင်း (Format: `123456(1234)dia878`)
- Payment screenshot ပို့ခြင်း
- Admin: Order complete / reject
- Admin: Price edit
- Admin: Order list ကြည့်ရန်
- Admin: User ban / unban
- Admin: Broadcast message

---

## 🚀 Setup

### 1. Bot Token ရယူပါ
1. Telegram မှာ [@BotFather](https://t.me/BotFather) သို့သွားပါ
2. `/newbot` နှိပ်ပြီး bot တစ်ခုဆောက်ပါ
3. Token ကိုကောပီထားပါ

### 2. Admin ID ရှာပါ
1. [@userinfobot](https://t.me/userinfobot) သို့သွားပြီး `/start` နှိပ်ပါ
2. ပေးသော ID နံပါတ်ကို မှတ်ထားပါ

### 3. GitHub မှာ Upload လုပ်ပါ

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/mlbb-bot.git
git push -u origin main
```

### 4. Render Deploy

1. [render.com](https://render.com) တွင် account ဖြင့် login ဝင်ပါ
2. **New → Background Worker** ကို နှိပ်ပါ
3. GitHub repo ကို ချိတ်ဆက်ပါ
4. **Environment Variables** တွင် ထည့်ပါ:
   - `BOT_TOKEN` = BotFather မှ token
   - `ADMIN_ID` = သင့် Telegram ID
5. **Deploy** နှိပ်ပါ ✅

---

## 📱 User Usage

```
Order format:
123456(1234)dia878

- 123456  = MLBB Game ID
- 1234    = Server ID
- dia878  = Package
```

Order တင်ပြီးနောက် payment screenshot ပို့ပါ။

---

## 🛠️ Admin Commands

| Command | ရည်ရွယ်ချက် |
|---------|------------|
| `/orders` | Order list ကြည့်ရန် |
| `/setprice dia878 5000ks` | Price သတ်မှတ်ရန် |
| `/setprice 2x50 2500ks` | 2x Diamond price |
| `/setprice weekly_pass 3000ks` | Weekly Pass price |
| `/ban 123456789` | User ban |
| `/unban 123456789` | User unban |
| `/broadcast <message>` | All users ထံ message |
| `/adminhelp` | Admin help |

---

## 📁 Project Structure

```
mlbb_bot/
├── bot.py              # Main bot code
├── requirements.txt    # Dependencies
├── render.yaml         # Render deployment config
├── .env.example        # Environment variables template
├── .gitignore
└── README.md
```

---

## ⚠️ Notes

- `.env` file ကို GitHub မှာ **upload မလုပ်ပါနဲ့** (`.gitignore` တွင် ထည့်ထားပြီး)
- Orders, prices, banned data တွေ JSON files တွင် သိမ်းသည် (Render free plan တွင် restart ဖြစ်ရင် reset ဖြစ်နိုင်)
- Production use အတွက် database (PostgreSQL) သုံးရန် အကြံပြုသည်
