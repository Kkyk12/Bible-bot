import os
import glob
import json
import telebot
from telebot import types
from rapidfuzz import process

API_TOKEN = '6730305948:AAFvksgeeVKlgsU65qgllHgaoD3kXj3J2Lw'  # Replace with your actual API token
bot = telebot.TeleBot(API_TOKEN)

# Path to your directory containing the JSON files
directory_path = '/storage/emulated/0/Bible/'

# Get a list of all JSON files in the directory
file_paths = glob.glob(os.path.join(directory_path, '*.json'))

# Dictionary to hold the Bible data
all_books = {}

# Load each JSON file
for file_path in sorted(file_paths):
    with open(file_path, 'r', encoding='utf-8') as f:
        book_data = json.load(f)
        book_name = os.path.basename(file_path).replace('.json', '').split('_')[-1]
        all_books[book_name] = book_data['chapters']

def suggest_books(user_input):
    """Suggest book names based on fuzzy matching."""
    matched_books = process.extract(user_input, all_books.keys(), limit=5)
    return matched_books

def suggest_chapters(book_name, chapter_input):
    """Suggest chapters based on fuzzy matching."""
    if book_name in all_books:
        chapters = all_books[book_name]
        chapter_numbers = [i + 1 for i in range(len(chapters))]
        matched_chapters = process.extract(chapter_input, map(str, chapter_numbers), limit=5)
        return matched_chapters
    return []

def clean_text(text):
    """Remove the reference number and title from the text."""
    parts = text.split(' - ', 1)  # Split on the first occurrence of ' - '
    if len(parts) > 1:
        return parts[1].strip()
    return text.strip()

@bot.inline_handler(lambda query: len(query.query) > 0)
def query_books(query):
    user_input = query.query.strip()
    results = []

    if ':' not in user_input:  # Likely a book name or chapter
        if ' ' not in user_input:  # User is typing the book name
            # Fuzzy search for the book name
            suggested_books = suggest_books(user_input)
            
        else:  # User might be typing the chapter after the book name
            try:
                book_name, chapter_input = user_input.rsplit(' ', 1)
                suggested_books = suggest_books(book_name)
                if suggested_books:
                    closest_book_name, _, _ = suggested_books[0]
                    suggested_chapters = suggest_chapters(closest_book_name, chapter_input)
                    if suggested_chapters:
                        closest_chapter, _, _ = suggested_chapters[0]
                        chapter = int(closest_chapter)
                        if chapter <= len(all_books[closest_book_name]):
                            verses = all_books[closest_book_name][chapter - 1]['verses']
                            # Send the entire chapter instead of just the first verse
                            chapter_text = "\n".join(f"{i + 1}: {clean_text(verse)}" for i, verse in enumerate(verses))
                            results.append(
                                types.InlineQueryResultArticle(
                                    id=f"chapter_{closest_book_name}_{chapter}",
                                    title=f"{closest_book_name} {chapter}",
                                    input_message_content=types.InputTextMessageContent(chapter_text),
                                    description=f"Chapter {chapter} of {closest_book_name}",  # Description with chapter number
                                )
                            )
            except (ValueError, IndexError):
                pass
    else:  # Likely typing the full chapter:verse
        try:
            book_chapter, verse_input = user_input.rsplit(':', 1)
            book_name, chapter_input = book_chapter.rsplit(' ', 1)
            chapter, verse = int(chapter_input), int(verse_input)

            suggested_books = suggest_books(book_name)
            if suggested_books:
                closest_book_name, _, _ = suggested_books[0]
                if chapter <= len(all_books[closest_book_name]):
                    verses = all_books[closest_book_name][chapter - 1]['verses']
                    if verse <= len(verses):
                        full_verse = clean_text(verses[verse - 1])
                        results.append(
                            types.InlineQueryResultArticle(
                                id=f"verse_{closest_book_name}_{chapter}_{verse}",
                                title=f"{closest_book_name} {chapter}:{verse}",
                                input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:{verse} - {full_verse}"),
                                description=full_verse,  # Display the full verse as the description
                            )
                        )
                    else:
                        # If verse is invalid, suggest the first verse of the chapter
                        first_verse = clean_text(verses[0]) if verses else "Chapter is empty."
                        results.append(
                            types.InlineQueryResultArticle(
                                id=f"verse_{closest_book_name}_{chapter}_1",
                                title=f"{closest_book_name} {chapter}:1",
                                input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:1 - {first_verse}"),
                                description=first_verse,  # Display the first verse as the description
                            )
                        )
                else:
                    # If chapter is invalid, suggest the first chapter
                    chapter = 1
                    verses = all_books[closest_book_name][chapter - 1]['verses']
                    if verse <= len(verses):
                        full_verse = clean_text(verses[verse - 1])
                        results.append(
                            types.InlineQueryResultArticle(
                                id=f"verse_{closest_book_name}_{chapter}_{verse}",
                                title=f"{closest_book_name} {chapter}:{verse}",
                                input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:{verse} - {full_verse}"),
                                description=full_verse,  # Display the full verse as the description
                            )
                        )
                    else:
                        # If verse is invalid, suggest the first verse of the chapter
                        first_verse = clean_text(verses[0]) if verses else "Chapter is empty."
                        results.append(
                            types.InlineQueryResultArticle(
                                id=f"verse_{closest_book_name}_{chapter}_1",
                                title=f"{closest_book_name} {chapter}:1",
                                input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter}:1 - {first_verse}"),
                                description=first_verse,  # Display the first verse as the description
                            )
                        )
        except (ValueError, IndexError):
            pass

    bot.answer_inline_query(query.id, results, cache_time=1)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        '''ወደ መጽሐፍ ቅዱስ Bot እንኳን በደህና መጡ! 
ይህ ቦት የመጽሐፉን ስም፣ ምዕራፍ እና ቁጥር በመፃፍ የመጽሐፍ ቅዱስ ምዕራፎችን እና ጥቅሶችን ለማንበብ ያስችላል።

እንዴት እንደሚጠቀሙት ምሳሌ፡-

በመጀመሪያ @Amh_bible_bot ብለው ይፃፉ ከዛም አንድ space ወይም ክፍት ቦታ በመተው...
1. የመፅሃፍ ስም: ለምሳሌ የመፅሃፍ ስሞችን ለማግኘት 'ዘፍጥረት' ብለው ይፃፉ።
2.  የመጽሐፍ ስም ከፃፋ በኃላ ትንሽ Space አድርገው የምዕራፍ ስም  ለምሳሌ የዘፍጥረትን የመጀመሪያ ምዕራፍ ለማግኘት 'ዘፍጥረት 1'።
3. ከምዕራፍ ቀጥሎ ቁጥር ለመፃፍ (:) ይህን ሁለት ነጥብ በማድረግ ይፃፋ
 ለምሳሌ 'ዘፍጥረት 1፡1' 
ከዛም የሚመጣሎትን በመንካት መላክ ይችላሉ

ይህ ቦት ቻነል፣ግሩፕ ላይም ይሰራል


ምንም አይነት ችግር ካጋጠመዎት ወይም አስተያየት ካለዎት እባክዎን ከአስተያየቶችዎ ጋር መልእክት በመላክ ያሳውቁኝ ።
@kkyk1286

@Amh_bible_bot ይህን መፃፍ እንዳይረሱ
   ''' )
    
    bot.send_message(message.chat.id, welcome_text)

bot.infinity_polling()