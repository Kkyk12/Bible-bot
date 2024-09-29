import os
import glob
import json
import telebot
from telebot import types
from rapidfuzz import process

API_TOKEN = '6730305948:AAFvksgeeVKlgsU65qgllHgaoD3kXj3J2Lw'  # Replace with your actual API token
bot = telebot.TeleBot(API_TOKEN)

# Path to your directory containing the JSON files
directory_path = '/Bible-bot/'

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

    if ':' not in user_input:  # User typed a book and chapter (e.g., 'ምሳሌ 1')
        try:
            book_name, chapter_input = user_input.rsplit(' ', 1)  # Split book and chapter
            suggested_books = suggest_books(book_name)
            if suggested_books:
                closest_book_name, _, _ = suggested_books[0]
                chapter = int(chapter_input)

                # Check if the chapter exists in the book
                if chapter <= len(all_books[closest_book_name]):
                    verses = all_books[closest_book_name][chapter - 1]['verses']
                    
                    # Display the first 5 verses or fewer if the chapter has less than 5 verses
                    verses_to_display = verses[:]
                    verse_texts = "\n".join(f"{i + 1}: {clean_text(verse)}" for i, verse in enumerate(verses_to_display))

                    # Create inline keyboard with search button
                    keyboard = types.InlineKeyboardMarkup()
                    search_button = types.InlineKeyboardButton(
                    text="Search", 
                    switch_inline_query_current_chat="")
                    keyboard.add(search_button)


                    # Add the result for the inline query
                    results.append(
                        types.InlineQueryResultArticle(
                            id=f"chapter_{closest_book_name}_{chapter}",
                            title=f"{closest_book_name} {chapter}",
                            input_message_content=types.InputTextMessageContent(f"{closest_book_name} {chapter} \n {verse_texts}"),
                            description=f" `{closest_book_name}   ምዕራፍ {chapter}   \n{verse_texts}`",
                            reply_markup=keyboard  # Attach the keyboard with the search button
                        )
                    )
        except (ValueError, IndexError):
            pass

    else:  # User typed the full chapter:verse (e.g., 'ምሳሌ 1:5')
        try:
            book_chapter, verse_input = user_input.rsplit(':', 1)  # Split chapter and verse
            book_name, chapter_input = book_chapter.rsplit(' ', 1)
            chapter, verse = int(chapter_input), int(verse_input)

            suggested_books = suggest_books(book_name)
            if suggested_books:
                closest_book_name, _, _ = suggested_books[0]

                # Check if the chapter and verse exist in the book
                if chapter <= len(all_books[closest_book_name]):
                    verses = all_books[closest_book_name][chapter - 1]['verses']
                    if verse <= len(verses):
                        full_verse = clean_text(verses[verse - 1])

                        # Create inline keyboard with search button
                        keyboard = types.InlineKeyboardMarkup()
                        search_button = types.InlineKeyboardButton(
                        text="Search", 
                        switch_inline_query_current_chat="")
                        keyboard.add(search_button)

                        # Add the result for the inline query
                        results.append(
                            types.InlineQueryResultArticle(
                                id=f"verse_{closest_book_name}_{chapter}_{verse}",
                                title=f"{closest_book_name} {chapter}:{verse}",
                                input_message_content=types.InputTextMessageContent(f"`{full_verse}\n — {closest_book_name} {chapter}:{verse} `"),
                                description=full_verse,  # Display the full verse as the description
                                reply_markup=keyboard  # Attach the keyboard with the search button
                            )
                        )
        except (ValueError, IndexError):
            pass

    bot.answer_inline_query(query.id, results, cache_time=1)
'''
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
'''


@bot.message_handler(commands=['start'])
def send_welcome(message):
	# Store user ID and name in a .txt file
	user_id = message.from_user.id
	user_name = message.from_user.first_name
	print(user_name)
	# Write the user ID and name to a .txt file
	with open('users.txt', 'a') as f:
		f.write(f"{user_id}, {user_name}\n")
		
		
	welcome_text = (
        '''Welcome to the Amharic Bible Bot!  
This bot allows you to read Bible by typing the name of the book, chapter, and verse.

Here’s an example of how to use it:

First, type @Amh_bible_bot and then leave a space or an open space before continuing...
1. Book Name: For example, to get the names of the books, type 'ዘፍጥረት'
2. After typing the book name, leave a small space and type in the chapter name. For example, to get the first chapter of ዘፍጥረት, type 'ዘፍጥረት 1'
3. To continue with the chapter, type the chapter number (:) by creating two dots. For example, 'ዘፍጥረት 1:1.' You can then follow up with further inquiries.


You can use the buttons below to start reading 

This bot works in channels and groups as well.

If you encounter any issues or have feedback, please inform me @kkyk1286
   '''
    )
    # Create inline keyboar
	markup = types.InlineKeyboardMarkup()
    
    # Add the "Search" button that opens the inline query
	search_button = types.InlineKeyboardButton(
        text="Search", 
        switch_inline_query_current_chat=""
    )
	markup.add(search_button)
    
    # Send welcome message with inline keyboard
	bot.send_message(message.chat.id, welcome_text, reply_markup=markup)


bot.infinity_polling()
