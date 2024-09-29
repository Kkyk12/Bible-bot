import os
import glob
import json
import telebot
from telebot import types
from rapidfuzz import process

API_TOKEN = '7199283970:AAHKyu_tR7W_nEtAY4RDhrnYesrGbEHj6jA'
bot = telebot.TeleBot(API_TOKEN)

# Path to your directory containing the JSON files
directory_path = '/storage/emulated/0/Bible/'

# Get a list of all JSON files in the directory
file_paths = glob.glob(os.path.join(directory_path, '*.json'))

# Dictionary to hold the Bible data
all_books = {}
old_testament_books = {}
new_testament_books = {}

# Load each JSON file and classify into Old and New Testament
for i, file_path in enumerate(sorted(file_paths), start=1):
    with open(file_path, 'r', encoding='utf-8') as f:
        book_data = json.load(f)
        book_name = os.path.basename(file_path).replace('.json', '').split('_')[-1]
        all_books[book_name] = book_data['chapters']
        
        if i <= 39:
            old_testament_books[book_name] = book_data['chapters']
        else:
            new_testament_books[book_name] = book_data['chapters']

def suggest_books(user_input):
    """Suggest book names based on fuzzy matching."""
    matched_books = process.extract(user_input, all_books.keys(), limit=5)
    return [book_name for book_name, score, _ in matched_books]

def search_text_in_verses(query_text):
    """Search for the given text within all verses and return matching results."""
    results = []
    for book_name, chapters in all_books.items():
        for chapter_index, chapter in enumerate(chapters):
            for verse_index, verse in enumerate(chapter['verses']):
                if query_text.lower() in verse.lower():
                    results.append({
                        'book': book_name,
                        'chapter': chapter_index + 1,
                        'verse': verse_index + 1,
                        'text': verse
                    })
    return results

@bot.inline_handler(lambda query: len(query.query) > 0)
def query_books(query):
    user_input = query.query.strip()
    results = []

    if ':' in user_input or ' ' in user_input:
        # Handle search for book names, chapters, and verses
        if ' ' in user_input:  # User is likely typing the book name and chapter
            try:
                book_name, chapter_input = user_input.rsplit(' ', 1)
                suggested_books = suggest_books(book_name)
                if suggested_books:
                    closest_book_name = suggested_books[0]
                    suggested_chapters = suggest_chapters(closest_book_name, chapter_input)
                    if suggested_chapters:
                        closest_chapter = suggested_chapters[0]
                        chapter = int(closest_chapter)
                        if chapter <= len(all_books[closest_book_name]):
                            verses = all_books[closest_book_name][chapter - 1]['verses']
                            chapter_text = "\n".join(f"{i + 1}: {clean_text(verse)}" for i, verse in enumerate(verses))
                            results.append(
                                types.InlineQueryResultArticle(
                                    id=f"chapter_{closest_book_name}_{chapter}",
                                    title=f"{closest_book_name} {chapter}",
                                    input_message_content=types.InputTextMessageContent(chapter_text),
                                    description=f"Full chapter {chapter} of {closest_book_name}",
                                )
                            )
            except (ValueError, IndexError):
                pass
        else:  # User is likely typing the full chapter:verse
            try:
                book_chapter, verse_input = user_input.rsplit(':', 1)
                book_name, chapter_input = book_chapter.rsplit(' ', 1)
                chapter, verse = int(chapter_input), int(verse_input)

                suggested_books = suggest_books(book_name)
                if suggested_books:
                    closest_book_name = suggested_books[0]
                    if chapter <= len(all_books[closest_book_name]):
                        verses = all_books[closest_book_name][chapter - 1]['verses']
                        if verse <= len(verses):
                            full_verse = clean_text(verses[verse - 1])
                            results.append(
                                types.InlineQueryResultArticle(
                                    id=f"verse_{closest_book_name}_{chapter}_{verse}",
                                    title=f"{closest_book_name} {chapter}:{verse}",
                                    input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:{verse} - {full_verse}"),
                                    description=full_verse,
                                )
                            )
                        else:
                            first_verse = clean_text(verses[0]) if verses else "Chapter is empty."
                            results.append(
                                types.InlineQueryResultArticle(
                                    id=f"verse_{closest_book_name}_{chapter}_1",
                                    title=f"{closest_book_name} {chapter}:1",
                                    input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:1 - {first_verse}"),
                                    description=first_verse,
                                )
                            )
                    else:
                        chapter = 1
                        verses = all_books[closest_book_name][chapter - 1]['verses']
                        if verse <= len(verses):
                            full_verse = clean_text(verses[verse - 1])
                            results.append(
                                types.InlineQueryResultArticle(
                                    id=f"verse_{closest_book_name}_{chapter}_{verse}",
                                    title=f"{closest_book_name} {chapter}:{verse}",
                                    input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:{verse} - {full_verse}"),
                                    description=full_verse,
                                )
                            )
                        else:
                            first_verse = clean_text(verses[0]) if verses else "Chapter is empty."
                            results.append(
                                types.InlineQueryResultArticle(
                                    id=f"verse_{closest_book_name}_{chapter}_1",
                                    title=f"{closest_book_name} {chapter}:1",
                                    input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:1 - {first_verse}"),
                                    description=first_verse,
                                )
                            )
            except (ValueError, IndexError):
                pass
    else:
        # Handle text search across all verses
        search_results = search_text_in_verses(user_input)
        for result in search_results:
            results.append(
                types.InlineQueryResultArticle(
                    id=f"search_{result['book']}_{result['chapter']}_{result['verse']}",
                    title=f"{result['book']} {result['chapter']}:{result['verse']}",
                    input_message_content=types.InputTextMessageContent(f"{result['book']} {result['chapter']}:{result['verse']} - {result['text']}"),
                    description=result['text'],
                )
            )

    bot.answer_inline_query(query.id, results, cache_time=1)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Welcome to the Bible Bot! 📖\n\n"
        "This bot allows you to search for Bible verses in multiple ways:\n\n"
        "1. **Type a book name** to get suggestions for book names.\n"
        "2. **Type a book name followed by a chapter** to get that chapter.\n"
        "3. **Type a book name, chapter, and verse** to get a specific verse.\n"
        "4. **Type a text or phrase** to search for it across all verses and see where it appears.\n\n"
        "To start searching, use the 'Search Bible' button below.\n\n"
        "For comments or feedback, please reply to this message."
    )
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    search_button = types.KeyboardButton("Search Bible")
    markup.add(search_button)
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

def clean_text(text):
    """Cleans up the text to remove unwanted characters or formatting."""
    return text.strip()

bot.polling()