from aiogram import Router

from handlers.admin import router as admin_router
from handlers.card import router as card_router
from handlers.donate import router as donate_router
from handlers.help import router as help_router
from handlers.notifications import router as notifications_router
from handlers.report import router as report_router
from handlers.spreads import router as spreads_router
from handlers.start import router as start_router


router = Router()

router.include_router(admin_router)
router.include_router(start_router)
router.include_router(help_router)
router.include_router(report_router)
router.include_router(notifications_router)
router.include_router(card_router)
router.include_router(spreads_router)
router.include_router(donate_router)
