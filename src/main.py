#!/usr/bin/env python3
"""
AutoBuilder Bot - Main Entry Point
Production-ready Telegram bot for automated tasks and builds
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.jobs.job_manager import JobManager
from src.telegram.handlers import (
    handle_start,
    handle_help,
    handle_status,
    handle_audit_site,
    handle_build_weather_apk,
    handle_jobs,
    handle_job,
    handle_cancel,
)
from src.utils.config import load_config

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path('/var/log/autobuilder')
    log_dir.mkdir(parents=True, exist_ok=True)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Try to add file handler, fallback if permission denied
    try:
        handlers.append(logging.FileHandler(log_dir / 'bot.log'))
    except PermissionError:
        # Fallback to local log file
        local_log = PROJECT_ROOT / 'logs' / 'bot.log'
        local_log.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(local_log))
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=handlers
    )

setup_logging()
logger = logging.getLogger(__name__)

# Global application instance
application = None
job_manager = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    if application:
        asyncio.create_task(application.stop())
    if job_manager:
        job_manager.shutdown()
    sys.exit(0)


async def post_init(app: Application) -> None:
    """Post-initialization tasks"""
    logger.info("AutoBuilder Bot started successfully")
    # Send startup notification if configured
    config = load_config()
    if config.get('telegram', {}).get('chat_id'):
        try:
            await app.bot.send_message(
                chat_id=config['telegram']['chat_id'],
                text="🤖 AutoBuilder Bot is now online!"
            )
        except Exception as e:
            logger.warning(f"Could not send startup message: {e}")


async def post_shutdown(app: Application) -> None:
    """Post-shutdown cleanup"""
    logger.info("AutoBuilder Bot shutting down...")


def main():
    """Main entry point"""
    global application, job_manager
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize job manager
    try:
        job_manager = JobManager(config)
        logger.info("Job manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize job manager: {e}")
        sys.exit(1)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create application
    bot_token = config['telegram']['bot_token']
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        logger.error("Bot token not configured! Please set telegram.bot_token in config.toml")
        sys.exit(1)
    
    application = Application.builder().token(bot_token).post_init(post_init).post_shutdown(post_shutdown).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", lambda u, c: handle_start(u, c, job_manager)))
    application.add_handler(CommandHandler("help", lambda u, c: handle_help(u, c, job_manager)))
    application.add_handler(CommandHandler("status", lambda u, c: handle_status(u, c, job_manager)))
    application.add_handler(CommandHandler("audit_site", lambda u, c: handle_audit_site(u, c, job_manager)))
    application.add_handler(CommandHandler("build_weather_apk", lambda u, c: handle_build_weather_apk(u, c, job_manager)))
    application.add_handler(CommandHandler("jobs", lambda u, c: handle_jobs(u, c, job_manager)))
    application.add_handler(CommandHandler("job", lambda u, c: handle_job(u, c, job_manager)))
    application.add_handler(CommandHandler("cancel", lambda u, c: handle_cancel(u, c, job_manager)))
    
    # Start bot
    use_webhook = config.get('telegram', {}).get('use_webhook', False)
    
    if use_webhook:
        webhook_url = config['telegram']['webhook_url']
        webhook_secret = config.get('telegram', {}).get('webhook_secret', '')
        logger.info(f"Starting webhook mode: {webhook_url}")
        application.run_webhook(
            listen="127.0.0.1",
            port=8443,
            url_path="webhook",
            webhook_url=webhook_url,
            secret_token=webhook_secret if webhook_secret else None,
        )
    else:
        logger.info("Starting long polling mode")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

