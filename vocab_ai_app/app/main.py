from datetime import datetime, timedelta
import random
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import traceback

from app import ai_service, models
from app.database import engine, get_db

# Verilənlər bazası cədvəllərini avtomatik formalaşdırırıq
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Advanced AI Vocabulary Platform")

# Statik və Template qovluqlarının tanıdılması
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    # Vaxtı gələn (due) sözlər
    due_words = (
        db.query(models.Vocabulary)
        .filter(models.Vocabulary.next_review <= now)
        .all()
    )
    due_count = len(due_words)
    total_count = db.query(models.Vocabulary).count()
    
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"due_count": due_count, "total_count": total_count, "due_words": due_words}
    )  


@app.post("/add")
def add_word(
    word: str = Form(...),
    meaning: str = Form(...),
    context: str = Form(None),
    translation: str = Form(None),
    db: Session = Depends(get_db),
):
    word_clean = word.strip().lower()
    existing = (
        db.query(models.Vocabulary)
        .filter(models.Vocabulary.word == word_clean)
        .first()
    )

    if not existing:
        new_vocab = models.Vocabulary(
            word=word_clean,
            meaning=meaning.strip(),
            default_context=context.strip() if context else "No context provided.",
            default_translation=(
                translation.strip() if translation else "Tərcümə qeyd edilməyib."
            ),
            category="Personal",
            level="Custom",
            next_review=datetime.utcnow(),
        )
        db.add(new_vocab)
        db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/generate-path-words")
def generate_path_words(
    category: str = Form(...),
    level: str = Form(...),
    db: Session = Depends(get_db)
):
    """AI-dan kateqoriyaya uyğun sözləri çəkir və bazaya yazır."""
    words_list = ai_service.generate_words_by_path(category, level)
    
    for item in words_list:
        word_clean = item.get("word", "").strip().lower()
        if not word_clean:
            continue
            
        # Dublikat yoxlanışı
        existing = db.query(models.Vocabulary).filter(models.Vocabulary.word == word_clean).first()
        
        if not existing:
            new_vocab = models.Vocabulary(
                word=word_clean,
                meaning=item.get("meaning", "").strip(),
                default_context=item.get("context", "").strip() or "No context provided.",
                default_translation=item.get("translation", "").strip() or "Tərcümə qeyd edilməyib.",
                category=category,
                level=level,
                next_review=datetime.utcnow()
            )
            db.add(new_vocab)
            
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/study/{word_id}")
def study_word(word_id: int, request: Request, db: Session = Depends(get_db)):
    vocab = (
        db.query(models.Vocabulary)
        .filter(models.Vocabulary.id == word_id)
        .first()
    )
    if not vocab:
        return RedirectResponse(url="/")
        
    return templates.TemplateResponse(
        request, "study.html", {"vocab": vocab}
    )


@app.post("/study/{word_id}/review")
def review_word(
    word_id: int, success: bool = Form(...), db: Session = Depends(get_db)
):
    vocab = (
        db.query(models.Vocabulary)
        .filter(models.Vocabulary.id == word_id)
        .first()
    )
    if not vocab:
        raise HTTPException(status_code=404, detail="Word not found")

    if success:
        vocab.interval = max(1, int(vocab.interval * vocab.ease_factor))
    else:
        vocab.interval = 1
        vocab.ease_factor = max(1.3, vocab.ease_factor - 0.2)

    vocab.next_review = datetime.utcnow() + timedelta(days=vocab.interval)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.get("/api/generate-sentence")
def api_sentence(word: str, db: Session = Depends(get_db)):
    word_clean = word.strip().lower()
    vocab = db.query(models.Vocabulary).filter(models.Vocabulary.word == word_clean).first()
    detected_level = vocab.level if vocab else "B1"
    return ai_service.generate_new_sentence(word, level=detected_level)


@app.get("/story")
async def view_story(request: Request, level: str = None, db: Session = Depends(get_db)):
    """İstifadəçi səviyyəni özü seçir. Səviyyə yoxdursa seçim ekranı, varsa hekayə gəlir."""
    now = datetime.utcnow()
    
    # Hekayədə istifadə olunacaq sözləri bazadan seçirik
    db_words = db.query(models.Vocabulary).filter(models.Vocabulary.next_review <= now).limit(5).all()
    if not db_words:
        db_words = db.query(models.Vocabulary).order_by(models.Vocabulary.id.desc()).limit(5).all()
        
    words_list = [v.word for v in db_words]
    
    # ƏGƏR İSTİFADƏÇİ HƏLƏ SƏVİYYƏ SEÇMƏYİBSƏ (İlk daxil olduqda)
    if not level:
        return templates.TemplateResponse(
            request,
            "story.html",
            {
                "choose_level": True,
                "words": words_list
            }
        )
        
    # ƏGƏR SƏVİYYƏ SEÇİLİBSƏ (Form submit olunduqdan sonra)
    story_data = ai_service.generate_story_from_words(words_list, level=level)
    
    return templates.TemplateResponse(
        request,
        "story.html", 
        {
            "choose_level": False,
            "story": story_data.get("story", []),
            "level": level,
            "words": words_list
        }
    )


@app.get("/all-words")
def all_words(request: Request, db: Session = Depends(get_db)):
    vocab_list = db.query(models.Vocabulary).order_by(models.Vocabulary.word).all()
    return templates.TemplateResponse(
        request, "all_words.html", {"vocab_list": vocab_list}
    )


@app.post("/delete/{word_id}")
def delete_word(word_id: int, db: Session = Depends(get_db)):
    vocab = (
        db.query(models.Vocabulary)
        .filter(models.Vocabulary.id == word_id)
        .first()
    )
    if vocab:
        db.delete(vocab)
        db.commit()
    return RedirectResponse(url="/all-words", status_code=303)


@app.get("/quiz")
def quiz_page(request: Request):
    return templates.TemplateResponse(request, "quiz.html", {})


@app.get("/api/quiz-cards")
def api_quiz_cards(db: Session = Depends(get_db)):
    all_cards = db.query(models.Vocabulary).all()
    quiz_data = []

    for card in all_cards:
        direction = random.choice(["EN_TO_AZ", "AZ_TO_EN"])
        if direction == "EN_TO_AZ":
            quiz_data.append(
                {
                    "id": card.id,
                    "question": card.word,
                    "correct_answer": card.meaning,
                    "context": card.default_context,
                    "type": "İngilis dili ➡️ Azərbaycan dili",
                }
            )
        else:
            quiz_data.append(
                {
                    "id": card.id,
                    "question": card.meaning,
                    "correct_answer": card.word,
                    "context": card.default_context,
                    "type": "Azərbaycan dili ➡️ İngilis dili",
                }
            )
    random.shuffle(quiz_data)
    return quiz_data


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return PlainTextResponse(f"Tapılan Real Xəta:\n{traceback.format_exc()}", status_code=500)