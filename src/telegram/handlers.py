"""Telegram bot command handlers"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.jobs.job_manager import JobManager, JobStatus
from src.jobs.job_executor import JobExecutor
from src.tasks.system_status import SystemStatusTask
from src.tasks.audit_public_site import AuditPublicSiteTask
from src.tasks.build_android_apk import BuildWeatherApkTask
from src.utils.config import load_config

logger = logging.getLogger(__name__)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /start command"""
    message = """
🤖 **AutoBuilder Bot**

Men sizning serveringizda turli vazifalarni bajarishga yordam beraman.

**Mavjud buyruqlar:**
• `/status` - Server holati
• `/audit_site` - Saytni xavfsizlik tekshiruvi
• `/build_weather_apk` - Weather app APK yaratish
• `/jobs` - Oxirgi 10 ta job ro'yxati
• `/job <id>` - Job holatini ko'rish
• `/cancel <id>` - Jobni bekor qilish
• `/help` - Batafsil yordam

**Xavfsizlik qoidalari:**
✅ Faqat sizning domenlaringizni tekshiraman
✅ Hech qanday zararli harakatlar yo'q
✅ Barcha ma'lumotlar xavfsiz saqlanadi
"""
    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /help command"""
    message = """
📖 **Yordam**

**Buyruqlar:**

`/status`
Server holatini ko'rsatadi (Nginx, PHP-FPM, MariaDB, disk, RAM)

`/audit_site`
jaysonkhan.com saytini xavfsizlik tekshiruvi:
• `.env` fayllarini tekshirish
• `.git` katalogini tekshirish
• TLS sozlamalari
• HTTP headers
• Markdown hisobot yuboradi

`/build_weather_apk`
Weather app APK yaratadi:
• Flutter loyihasi yaratadi
• APK build qiladi
• Telegram orqali yuboradi
• GitHub'ga `myself` branchga push qiladi

`/jobs`
Oxirgi 10 ta job ro'yxati

`/job <id>`
Job holati va natijalari

`/cancel <id>`
Jobni bekor qilish (ishlayotgan joblar uchun)

**Xavfsizlik:**
• Barcha buyruqlar timeout bilan ishlaydi
• Sensitive ma'lumotlar redact qilinadi
• Faqat ruxsat berilgan buyruqlar bajariladi
"""
    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /status command"""
    await update.message.reply_text("⏳ Server holatini tekshiryapman...")
    
    try:
        config = load_config()
        executor = JobExecutor(job_manager, config)
        task = SystemStatusTask(config)
        
        job_id = job_manager.create_job("status")
        
        # Run task
        result = await executor.execute_job(job_id, task.execute)
        
        # Send report
        job = job_manager.get_job(job_id)
        if job and job.get('report_path'):
            report_path = Path(job['report_path'])
            if report_path.exists():
                await update.message.reply_document(
                    document=open(report_path, 'rb'),
                    filename="status_report.md",
                    caption="📊 Server holati hisoboti"
                )
            else:
                await update.message.reply_text("✅ Tekshiruv yakunlandi. Hisobot yaratilmadi.")
        else:
            await update.message.reply_text("❌ Xatolik yuz berdi.")
        
        # Cleanup
        executor.cleanup_workspace(job_id)
        
    except Exception as e:
        logger.error(f"Status task failed: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")


async def handle_audit_site(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /audit_site command"""
    await update.message.reply_text("🔍 Saytni tekshiryapman...")
    
    try:
        config = load_config()
        executor = JobExecutor(job_manager, config)
        task = AuditPublicSiteTask(config)
        
        job_id = job_manager.create_job("audit_site")
        
        # Run task
        result = await executor.execute_job(job_id, task.execute)
        
        # Send report
        job = job_manager.get_job(job_id)
        if job and job.get('report_path'):
            report_path = Path(job['report_path'])
            if report_path.exists():
                await update.message.reply_document(
                    document=open(report_path, 'rb'),
                    filename="audit_report.md",
                    caption="🔒 Xavfsizlik tekshiruvi hisoboti"
                )
            else:
                await update.message.reply_text("✅ Tekshiruv yakunlandi.")
        else:
            await update.message.reply_text("❌ Xatolik yuz berdi.")
        
        # Cleanup
        executor.cleanup_workspace(job_id)
        
    except Exception as e:
        logger.error(f"Audit task failed: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")


async def handle_build_weather_apk(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /build_weather_apk command"""
    await update.message.reply_text("🏗️ Weather app APK yaratilmoqda... Bu biroz vaqt olishi mumkin.")
    
    try:
        config = load_config()
        executor = JobExecutor(job_manager, config)
        task = BuildWeatherApkTask(config)
        
        job_id = job_manager.create_job("build_weather_apk")
        
        # Run task
        result = await executor.execute_job(job_id, task.execute)
        
        # Send results
        job = job_manager.get_job(job_id)
        if job:
            workspace_dir = Path(config['paths']['workspaces_dir']) / job_id
            
            # Send APK if exists
            apk_path = workspace_dir / "app" / "build" / "app" / "outputs" / "flutter-apk" / "app-release.apk"
            if not apk_path.exists():
                # Try alternative path
                apk_path = workspace_dir / "app" / "build" / "app" / "outputs" / "apk" / "release" / "app-release.apk"
            
            if apk_path.exists():
                await update.message.reply_document(
                    document=open(apk_path, 'rb'),
                    filename="weather_app.apk",
                    caption="📱 Weather App APK tayyor!"
                )
            else:
                await update.message.reply_text("⚠️ APK topilmadi. Loglarni tekshiring.")
            
            # Send report if exists
            if job.get('report_path'):
                report_path = Path(job['report_path'])
                if report_path.exists():
                    await update.message.reply_document(
                        document=open(report_path, 'rb'),
                        filename="build_report.md"
                    )
        
        # Cleanup
        executor.cleanup_workspace(job_id)
        
    except Exception as e:
        logger.error(f"Build task failed: {e}")
        await update.message.reply_text(f"❌ Xatolik: {str(e)}")


async def handle_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /jobs command"""
    jobs = job_manager.list_jobs(limit=10)
    
    if not jobs:
        await update.message.reply_text("📋 Hozircha joblar yo'q.")
        return
    
    message = "📋 **Oxirgi 10 ta job:**\n\n"
    for job in jobs:
        status_emoji = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '🚫'
        }.get(job['status'], '❓')
        
        message += f"{status_emoji} `{job['id'][:8]}` - {job['command']} ({job['status']})\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_job(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /job <id> command"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("❌ Job ID kiriting: `/job <id>`", parse_mode='Markdown')
        return
    
    job_id = context.args[0]
    job = job_manager.get_job(job_id)
    
    if not job:
        await update.message.reply_text(f"❌ Job topilmadi: `{job_id}`", parse_mode='Markdown')
        return
    
    status_emoji = {
        'pending': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '🚫'
    }.get(job['status'], '❓')
    
    message = f"""
{status_emoji} **Job:** `{job['id']}`

**Buyruq:** {job['command']}
**Holat:** {job['status']}
**Yaratilgan:** {job['created_at']}
"""
    
    if job.get('completed_at'):
        message += f"**Yakunlangan:** {job['completed_at']}\n"
    
    if job.get('error_message'):
        message += f"**Xatolik:** {job['error_message']}\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')
    
    # Send report if exists
    if job.get('report_path'):
        report_path = Path(job['report_path'])
        if report_path.exists():
            await update.message.reply_document(
                document=open(report_path, 'rb'),
                filename="report.md"
            )


async def handle_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE, job_manager: JobManager):
    """Handle /cancel <id> command"""
    if not context.args or len(context.args) == 0:
        await update.message.reply_text("❌ Job ID kiriting: `/cancel <id>`", parse_mode='Markdown')
        return
    
    job_id = context.args[0]
    success = job_manager.cancel_job(job_id)
    
    if success:
        await update.message.reply_text(f"✅ Job bekor qilindi: `{job_id}`", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ Job bekor qilinmadi (topilmadi yoki yakunlangan): `{job_id}`", parse_mode='Markdown')

