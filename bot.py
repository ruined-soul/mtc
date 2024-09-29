import os
import subprocess
import importlib
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from datetime import datetime
from run import keep_alive  # Import the flask keep_alive function

# Bot Owner ID
OWNER_ID = 1159381624  # Example owner ID, replace with your own

# Private log channel and private group for join/leave logs
LOG_CHANNEL_ID = -100123456789  # Replace with your log channel ID
JOIN_LEAVE_GROUP_ID = -100987654321  # Replace with your group for join/leave logs
BAN_LOG_CHANNEL_ID = -100987654322  # Replace with your ban log channel

# Initialize the bot
updater = Updater(os.getenv("BOT_TOKEN"), use_context=True)
dispatcher = updater.dispatcher

# Storage folder for plugins
PLUGIN_FOLDER = 'plugins/'

# Ensure plugin folder exists
os.makedirs(PLUGIN_FOLDER, exist_ok=True)

# Helper functions
def send_owner_message(context: CallbackContext, text: str):
    context.bot.send_message(chat_id=OWNER_ID, text=text)

# Bot Start & Restart message to owner
def on_start(update: Update, context: CallbackContext):
    send_owner_message(context, "Bot has started successfully!")

# Install Plugin Command
def install_plugin(update: Update, context: CallbackContext):
    if update.message.reply_to_message and update.message.from_user.id == OWNER_ID:
        # Replying to a file
        file = update.message.reply_to_message.document
        if file.file_name.endswith('.py'):
            file_id = file.file_id
            new_file = context.bot.get_file(file_id)
            file_path = os.path.join(PLUGIN_FOLDER, file.file_name)
            new_file.download(file_path)
            
            # Check for requirements.txt and install dependencies
            plugin_dir = os.path.splitext(file.file_name)[0]
            req_file = os.path.join(PLUGIN_FOLDER, plugin_dir, 'requirements.txt')
            if os.path.exists(req_file):
                subprocess.run(['pip', 'install', '-r', req_file])
            
            # Load the new plugin dynamically
            try:
                importlib.import_module(f'plugins.{plugin_dir}')
                update.message.reply_text(f"Plugin {file.file_name} installed successfully.")
            except Exception as e:
                update.message.reply_text(f"Error installing plugin: {e}")
        else:
            update.message.reply_text("Only Python (.py) files can be installed.")
    else:
        update.message.reply_text("You need to reply to a plugin file to install it.")

# Uninstall Plugin Command
def uninstall_plugin(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        try:
            plugin_name = context.args[0]
            plugin_path = os.path.join(PLUGIN_FOLDER, f'{plugin_name}.py')
            if os.path.exists(plugin_path):
                os.remove(plugin_path)
                update.message.reply_text(f"Plugin {plugin_name} uninstalled successfully.")
            else:
                update.message.reply_text(f"Plugin {plugin_name} does not exist.")
        except IndexError:
            update.message.reply_text("Usage: /uninstall <plugin_name>")
    else:
        update.message.reply_text("Only the owner can uninstall plugins.")

# Export Plugins Command
def export_plugins(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        plugin_files = [f for f in os.listdir(PLUGIN_FOLDER) if f.endswith('.py')]
        if plugin_files:
            for file in plugin_files:
                context.bot.send_document(chat_id=OWNER_ID, document=open(os.path.join(PLUGIN_FOLDER, file), 'rb'))
        else:
            update.message.reply_text("No plugins installed.")

# Join/Leave Logging for Private GC
def join_log(update: Update, context: CallbackContext):
    log_text = f"Joined chat: {update.message.chat.title}\nChat ID: {update.message.chat.id}\nDate: {datetime.now()}"
    context.bot.send_message(chat_id=JOIN_LEAVE_GROUP_ID, text=log_text)

def leave_log(update: Update, context: CallbackContext):
    log_text = f"Left chat: {update.message.chat.title}\nChat ID: {update.message.chat.id}\nDate: {datetime.now()}"
    context.bot.send_message(chat_id=JOIN_LEAVE_GROUP_ID, text=log_text)

# Log Extraction Command
def log_command(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        with open('bot.log', 'r') as log_file:
            context.bot.send_document(chat_id=OWNER_ID, document=log_file)
    else:
        update.message.reply_text("Only the owner can access logs.")

# Restart Bot Command
def restart(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        update.message.reply_text("Bot is restarting...")
        os.system('restart_command')  # This will depend on how you are deploying
    else:
        update.message.reply_text("Only the owner can restart the bot.")

# Reset Command (Clearing logs or caches)
def reset(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        open('bot.log', 'w').close()  # Clear the log file
        update.message.reply_text("Logs and caches have been cleared.")
    else:
        update.message.reply_text("Only the owner can reset the bot.")

# Leave Specific Group Command
def leave_group(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        try:
            chat_id = int(context.args[0])
            context.bot.leave_chat(chat_id)
            update.message.reply_text(f"Left the group with chat ID {chat_id}.")
        except IndexError:
            update.message.reply_text("Usage: /leave <chat_id>")
    else:
        update.message.reply_text("Only the owner can make the bot leave groups.")

# Dev Help Command Continued
def devhelp(update: Update, context: CallbackContext):
    if update.message.from_user.id == OWNER_ID:
        help_text = """
        /install - Install a plugin by replying to a .py file.
        /uninstall <plugin_name> - Uninstall a plugin by name.
        /export - Export all installed plugin files.
        /log - Get the bot logs.
        /restart - Restart the bot.
        /reset - Clear logs and caches.
        /leave <chat_id> - Make the bot leave a group with the specified chat ID.
        All these commands are for the bot owner only.
        """
        update.message.reply_text(help_text)
    else:
        update.message.reply_text("You don't have permission to use this command.")

# Help command for all users (dynamic, updated when a new plugin is installed)
def help_command(update: Update, context: CallbackContext):
    # Collect plugin commands dynamically
    categories = {}
    for plugin in os.listdir(PLUGIN_FOLDER):
        if plugin.endswith('.py'):
            try:
                mod = importlib.import_module(f'plugins.{plugin[:-3]}')
                if hasattr(mod, 'HELP_TEXT'):
                    # Each plugin should define its help text and category
                    category = getattr(mod, 'CATEGORY', 'General')
                    help_text = getattr(mod, 'HELP_TEXT', '')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(help_text)
            except Exception as e:
                continue

    # Build help message with inline buttons for categories
    buttons = []
    for category in categories:
        buttons.append([InlineKeyboardButton(text=category, callback_data=category)])
    
    if buttons:
        update.message.reply_text("Select a help category:", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        update.message.reply_text("No help available.")

# Handle callback from the help command buttons
def help_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    # Display help text for the selected category
    selected_category = query.data
    category_help = ""
    for plugin in os.listdir(PLUGIN_FOLDER):
        if plugin.endswith('.py'):
            try:
                mod = importlib.import_module(f'plugins.{plugin[:-3]}')
                if hasattr(mod, 'CATEGORY') and getattr(mod, 'CATEGORY') == selected_category:
                    help_text = getattr(mod, 'HELP_TEXT', '')
                    category_help += help_text + "\n\n"
            except Exception as e:
                continue
    
    if category_help:
        query.message.edit_text(f"Help for {selected_category}:\n\n{category_help}")
    else:
        query.message.edit_text(f"No help available for {selected_category}.")

# Error logging handler
def error_handler(update: Update, context: CallbackContext):
    error_text = f"Error: {context.error}\nOccurred in: {update}"
    context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=error_text)

# Function for logging daily reports and errors to a private channel
def log_daily_report(context: CallbackContext):
    log_text = "Daily log report:\n"
    log_text += "Number of installed plugins: " + str(len([f for f in os.listdir(PLUGIN_FOLDER) if f.endswith('.py')])) + "\n"
    log_text += "Bot running smoothly."
    
    context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_text)

# Scheduled task for sending daily logs
def schedule_daily_logs():
    job_queue = updater.job_queue
    # Schedule daily at midnight
    job_queue.run_daily(log_daily_report, time=datetime.time(hour=0, minute=0))

# Main function to set up all handlers and start the bot
def main():
    # Flask keep-alive
    keep_alive()
    
    # Command handlers
    dispatcher.add_handler(CommandHandler("start", on_start))
    dispatcher.add_handler(CommandHandler("install", install_plugin))
    dispatcher.add_handler(CommandHandler("uninstall", uninstall_plugin))
    dispatcher.add_handler(CommandHandler("export", export_plugins))
    dispatcher.add_handler(CommandHandler("log", log_command))
    dispatcher.add_handler(CommandHandler("restart", restart))
    dispatcher.add_handler(CommandHandler("reset", reset))
    dispatcher.add_handler(CommandHandler("leave", leave_group))
    dispatcher.add_handler(CommandHandler("devhelp", devhelp))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Callback query handler for inline help buttons
    dispatcher.add_handler(CallbackQueryHandler(help_callback))

    # Log all errors to a private channel
    dispatcher.add_error_handler(error_handler)
    
    # Join/leave log handlers (optional)
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, join_log))
    dispatcher.add_handler(MessageHandler(Filters.status_update.left_chat_member, leave_log))
    
    # Schedule daily logs
    schedule_daily_logs()
    
    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
