from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler
)
from datetime import date
import calendar
from telegram.error import NetworkError, BadRequest
from telegram.constants import ChatAction, ParseMode
from hugging_tg_chatbot.html_format import format_message
from hugging_tg_chatbot.huggingchat import chatbot, generate_response

SYSTEM_PROMPT_SP = 1
CANCEL_SP = 2


def new_chat(context: ContextTypes.DEFAULT_TYPE) -> None:
    # model_index = context.chat_data.get("model", 0)
    # system_prompt = context.chat_data.get("system_prompt", "")
    ASSISTANT_ID: str = "66ac875aafb4a0140632ca17" # such as 65fc7e89c0f4abe9abb9d304
       
    #assistant = chatbot.search_assistant(assistant_name="Real Human") 
    context.chat_data["conversation_id"] = chatbot.new_conversation(assistant=ASSISTANT_ID, switch_to=True) 
    # context.chat_data["conversation_id"] = chatbot.new_conversation(modelIndex=model_index, system_prompt=system_prompt)
    context.chat_data["new"] = True

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!\n\nSay hi to Coach Ladz to start your journey to your dream body. He's kinda strict so suit yourself.",
    )
    


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
Basic commands:
/start - Start from the beginning
/help - Get help. Shows this message

Chat commands:
/new - Start a new session. Coach Ella will forget all the information you previously provided.

Send a message to the bot to generate a response.
"""
    await update.message.reply_text(help_text)
    
    
async def new_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new chat session"""
    new_chat(context)
    await update.message.reply_text("You created a new session. Coach Ladz forgot all the information you provided so please start as a new client")
    

async def model_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Change the model used to generate responses"""
    models = [model.name for model in chatbot.get_available_llm_models()]
    
    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(model, callback_data="change_model_"+model)] for model in models
        ]
    )
    
    await update.message.reply_text("Select a model:", reply_markup=reply_markup)
    
    
async def change_model_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Change the model used to generate responses"""
    query = update.callback_query
    model = query.data.replace("change_model_", "")
    
    context.chat_data["model"] = chatbot.llms.index(chatbot.get_llm_from_name(model))
    
    await query.edit_message_text(f"Model changed to `{model}`. \n\nSend /new to start a new chat session.", parse_mode=ParseMode.MARKDOWN)
    

async def start_system_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a system prompt"""
    await update.message.reply_text("Send me a system prompt. If you want to clear the system prompt, send `clear` now.")
    return SYSTEM_PROMPT_SP
    
    
async def cancelled_system_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel the system prompt"""
    await update.message.reply_text("System prompt change cancelled.")
    return ConversationHandler.END
    
async def get_system_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the system prompt"""
    system_prompt = update.message.text
    if system_prompt.lower().strip() == "clear":
        context.chat_data["system_prompt"] = ""
        await update.message.reply_text("System prompt cleared.")
    else:
        context.chat_data["system_prompt"] = system_prompt
        await update.message.reply_text("System prompt changed.")
    new_chat(context)
    return ConversationHandler.END
    
    
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle messages"""
    if "model" not in context.chat_data:
        context.chat_data["model"] = 0
        
    if "conversation_id" not in context.chat_data:
        new_chat(context)
   
    init_msg = await update.message.reply_text("Typing...")
    
    conversation_id = context.chat_data["conversation_id"]
    chatbot.change_conversation(conversation_id)
    
    message = update.message.text
    if context.chat_data["new"]:
        my_date = date.today()
        day=calendar.day_name[my_date.weekday()]
        message = message + f". My name is {update.effective_user.first_name}. (Today is {my_date}, {day})"
        context.chat_data["new"] = False
        
    if not message:
        return
    
    full_output_message = ""
    await update.message.chat.send_action(ChatAction.TYPING)
    for message in generate_response(message):
        if message:
            full_output_message += message
            send_message = format_message(full_output_message)
            init_msg = await init_msg.edit_text(send_message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            

async def info_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get info about the bot"""
    info = chatbot.get_conversation_info()
    message = f"""**__Conversation Info:__**

**ID**: `{info.id}`
**Title**: `{info.title}`
**Model**: `{info.model}`
"""
    if info.system_prompt:
        message += f"\n**System Prompt**: \n```\n{info.system_prompt}\n```"
    await update.message.reply_text(format_message(message), parse_mode=ParseMode.HTML)