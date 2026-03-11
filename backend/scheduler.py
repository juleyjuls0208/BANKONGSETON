"""
Daily Scheduler — Low Balance Batch Email
Sends a daily email to parents of all students below LOW_BALANCE_THRESHOLD.

Uses APScheduler if available, falls back to threading.Timer loop.
Starts automatically when admin_dashboard.py launches.
"""
import os
import logging
import threading
from datetime import datetime, time as dt_time
from typing import Callable, Optional
import pytz

try:
    from errors import get_logger
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)

PHILIPPINES_TZ = pytz.timezone('Asia/Manila')

# Configurable via env
SCHEDULE_HOUR   = int(os.getenv('BATCH_EMAIL_HOUR', 7))    # 7 AM PH time
SCHEDULE_MINUTE = int(os.getenv('BATCH_EMAIL_MINUTE', 0))


# ── Job ───────────────────────────────────────────────────────────────────────

def run_low_balance_batch(sheets_client_fn: Callable, email_notifier_fn: Callable) -> dict:
    """
    Execute the low-balance batch email job.

    Args:
        sheets_client_fn: Callable that returns a gspread spreadsheet object
        email_notifier_fn: Callable that returns an EmailNotifier instance

    Returns:
        {sent: int, skipped: int, errors: int, run_at: str}
    """
    now = datetime.now(PHILIPPINES_TZ).isoformat()
    sent = skipped = errors = 0
    threshold = float(os.getenv('LOW_BALANCE_THRESHOLD', 50))

    try:
        db = sheets_client_fn()
        users = db.worksheet('Users').get_all_records()
        money_accounts = db.worksheet('Money Accounts').get_all_records()

        # Build balance map: MoneyCardNumber → balance
        balance_map = {
            str(r.get('MoneyCardNumber', '')).strip(): float(r.get('Balance', 0))
            for r in money_accounts
            if r.get('MoneyCardNumber')
        }

        notifier = email_notifier_fn()

        for user in users:
            try:
                parent_email = str(user.get('ParentEmail', '')).strip()
                if not parent_email or '@' not in parent_email:
                    skipped += 1
                    continue

                money_card = str(user.get('MoneyCardNumber', '')).strip()
                balance = balance_map.get(money_card, None)
                if balance is None:
                    skipped += 1
                    continue

                if balance < threshold:
                    student_name = str(user.get('Name', 'Student'))
                    student_id = str(user.get('StudentID', ''))
                    notifier.send_low_balance_alert(
                        student_name=student_name,
                        student_id=student_id,
                        balance=balance,
                        threshold=threshold,
                        to_email=parent_email,
                    )
                    sent += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.warning("event=batch_row_error error=%s", e)
                errors += 1

        # Log result to Scheduler Log sheet
        try:
            sheet_titles = [ws.title for ws in db.worksheets()]
            if 'Scheduler Log' not in sheet_titles:
                log_ws = db.add_worksheet(title='Scheduler Log', rows=500, cols=5)
                log_ws.append_row(['RunAt', 'Job', 'Sent', 'Skipped', 'Errors'])
            else:
                log_ws = db.worksheet('Scheduler Log')
            log_ws.append_row([now, 'low_balance_batch', sent, skipped, errors])
        except Exception as e:
            logger.warning("event=scheduler_log_failed error=%s", e)

        logger.info(
            "event=low_balance_batch_done sent=%d skipped=%d errors=%d",
            sent, skipped, errors
        )

    except Exception as e:
        logger.error("event=low_balance_batch_failed error=%s", e)
        errors += 1

    return {'sent': sent, 'skipped': skipped, 'errors': errors, 'run_at': now}


# ── Scheduler ─────────────────────────────────────────────────────────────────

class DailyScheduler:
    """
    Runs a job once per day at a configured time (PH timezone).

    Tries APScheduler first; falls back to a threading.Timer loop.
    """

    def __init__(self, hour: int = SCHEDULE_HOUR, minute: int = SCHEDULE_MINUTE):
        self.hour = hour
        self.minute = minute
        self._scheduler = None
        self._timer: Optional[threading.Timer] = None
        self._jobs: list = []

    def add_job(self, fn: Callable, *args, **kwargs):
        """Register a job to run daily. fn will be called with *args, **kwargs."""
        self._jobs.append((fn, args, kwargs))

    def start(self):
        """Start the scheduler (non-blocking)."""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger

            self._scheduler = BackgroundScheduler(timezone=PHILIPPINES_TZ)
            for fn, args, kwargs in self._jobs:
                self._scheduler.add_job(
                    fn,
                    CronTrigger(hour=self.hour, minute=self.minute, timezone=PHILIPPINES_TZ),
                    args=args,
                    kwargs=kwargs,
                )
            self._scheduler.start()
            logger.info(
                "event=scheduler_started engine=apscheduler hour=%d minute=%d",
                self.hour, self.minute
            )
        except ImportError:
            logger.info(
                "event=scheduler_started engine=threading_timer hour=%d minute=%d",
                self.hour, self.minute
            )
            self._schedule_next()

    def _schedule_next(self):
        """Schedule the next timer firing using stdlib threading.Timer."""
        now = datetime.now(PHILIPPINES_TZ)
        target = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
        if target <= now:
            from datetime import timedelta
            target += timedelta(days=1)
        delay = (target - now).total_seconds()
        self._timer = threading.Timer(delay, self._fire)
        self._timer.daemon = True
        self._timer.start()
        logger.info("event=timer_scheduled delay_seconds=%.0f", delay)

    def _fire(self):
        for fn, args, kwargs in self._jobs:
            try:
                fn(*args, **kwargs)
            except Exception as e:
                logger.error("event=scheduler_job_error error=%s", e)
        self._schedule_next()  # Reschedule for next day

    def stop(self):
        if self._scheduler:
            try:
                self._scheduler.shutdown(wait=False)
            except Exception:
                pass
        if self._timer:
            self._timer.cancel()


# Singleton
_scheduler: Optional[DailyScheduler] = None


def get_scheduler() -> DailyScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = DailyScheduler()
    return _scheduler
