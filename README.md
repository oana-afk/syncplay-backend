**SyncPlay** – Companion interactiv pentru emisiuni TV live. Backend modular construit cu Flask, gata de deploy pe Heroku.

---

## 🔧 Ce face

- 🤔 Răspunde la întrebări din public cu AI (Gemini)
- 🎮 Livrează quiz-uri live
- 🎥 Oferă scene exclusive doar pentru aplicația mobilă

---

## 🚀 Deploy pe Heroku

### 1. Clonează repo-ul:
```bash
git clone https://github.com/user/syncplay.git
cd syncplay/backend
```

### 2. Creează app Heroku:
```bash
heroku create syncplay-backend
```

### 3. Setează cheia Gemini:
```bash
heroku config:set GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Deploy:
```bash
git add .
git commit -m "Deploy backend"
git push heroku master
```

---

## 🌐 Endpoints disponibile

| Method | Endpoint                  | Ce face                       |
|--------|---------------------------|-------------------------------|
| GET    | `/api/quiz/current`       | Returnează întrebare de quiz   |
| GET    | `/api/scene/exclusive`    | Scenă exclusivă (video/text)   |
| POST   | `/api/ai/ask`             | Trimte întrebare la Gemini AI   |

---

## 📃 Structura modulară

```
backend/
├── app.py                    # Setup Flask + blueprints
├── routes/                  # Toate rutele API
│   ├── ai_routes.py
│   ├── quiz_routes.py
│   └── scene_routes.py
├── services/                # Gemini + data loader
│   ├── gemini_service.py
│   └── data_loader.py
├── data/                    # Fișiere JSON pentru conținut
│   ├── quiz.json
│   └── scenes.json
├── requirements.txt
├── runtime.txt
├── Procfile
└── .env.example
```

---

## 📊 În dezvoltare:
- 🔢 Admin panel live pentru push de quiz-uri
- 💡 Integrare Firebase pentru sync real-time
- 📱 Aplicație Flutter cu sync audio

---

## 🙌 Creat pentru interacțiune reală, nu doar broadcast.
**TV-ul tău are un nou companion. Tu ești parte din show.**
