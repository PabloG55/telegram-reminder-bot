# **Botifier – Telegram Reminder Assistant**

![](images/wappbot.jpg)

## Overview

**Botifier** is more than a simple to-do list, it's your personal productivity assistant powered by **Telegram** and enhanced with **natural language processing (NLP)**. Designed for users who want natural, intuitive interaction with their daily tasks, Botifier understands your messages just like a human assistant would.

You can add, edit, delete, and complete reminders using everyday language, all from a private chat with the bot on Telegram. It also sends smart follow-up messages to check if you’ve completed your tasks and offers a live web dashboard to visualize and manage everything in one place.

Whether you're a student, a busy professional, or someone who just forgets to take out the trash, Botifier helps you stay accountable and in control.

---

## Features

* **Telegram-Based Task Management**: Manage your tasks via chat or voice in Telegram.
* **Smart Follow-Up Reminders**: Botifier checks in to keep you on track.
* **Web Dashboard**: A real-time dashboard to view, edit, and track your tasks.
* **Natural Language Understanding**: Say things like *“Remind me to call mom at 7pm”* and it just works.
* **Edit/Delete by Description**: Modify tasks by simply referencing their name.
* **Per-User Timezone Handling**: Each user gets reminders in their own local time.
* **Voice Support**: Send voice notes, Botifier transcribes and understands them.

---

## Target Users

* Students managing study sessions, assignments, and daily routines.
* Professionals who want seamless task management without leaving Telegram.
* Anyone looking for an intelligent assistant with a human-like interface.

---

## How to Use

### 1. **Connect Telegram to Your Account**

After logging into the Botifier dashboard, type:

```
/connect YOUR_CODE
```

This links your Telegram ID with your secure user profile.

---

### 2. **Add a Task via Telegram Chat or Voice**

Send a message or a voice note like:

```
Remind me to finish my resume at 7pm
```

![](images/phone1.jpg)

---

### 3. **Get Follow-Up Nudges**

Botifier automatically checks in:

```
🔁 Still working on: 'finish my resume'? Reply YES or NO
```

![](images/phone2.jpg)

---

### 4. **Use the Web Dashboard**

* View tasks across all devices.
* Filter by status.
* Edit or complete tasks visually.

![](images/web.jpg)

---

### 5. **Reschedule or Delete Tasks Naturally**

* Say: `Edit "finish my resume" to 9pm`
* Or: `Delete "finish my resume"`

![](images/phone3.jpg)

---

## Key Benefits for Multi-User Environments

* 🔒 **Secure Identity Linking** via Firebase Auth + Telegram `/connect` flow.
* 🌍 **Timezone Awareness** Reminders are personalized to your location.
* 🔁 **User-Specific Jobs** Each user's tasks are scheduled and tracked independently.
* 💬 **One Unified Assistant** Interact via Telegram; manage via web.

---

## Final Thoughts

**Botifier** isn’t just a bot, it’s an assistant that listens, reminds, and keeps you accountable. With its human-like understanding and multi-user architecture, Botifier delivers the perfect blend of productivity and personalization.
