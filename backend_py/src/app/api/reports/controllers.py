from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.external.sqlalchemy.models import (
    Report,
    Machine,
    Monitoring,
    InventoryMovement,
    InventoryMovementItem,
    InventoryCountStatus,
    MachineStock,
    Item,
    Rent,
    Price,
)
from app.external.sqlalchemy.utils.reference_tables import inventory_count_status_crud


def _get_prev_monitoring_day_max(
    db: Session, machine_id: int, target_date: datetime
) -> Monitoring | None:
    # find the most recent record before target_date to determine the previous day that has data
    prev_any = (
        db.query(Monitoring)
        .filter(Monitoring.machine_id == machine_id, Monitoring.date < target_date)
        .order_by(Monitoring.date.desc())
        .first()
    )
    if not prev_any:
        return None
    prev_day = datetime(prev_any.date.year, prev_any.date.month, prev_any.date.day)
    start = prev_day
    end = start + timedelta(days=1)
    return (
        db.query(Monitoring)
        .filter(
            Monitoring.machine_id == machine_id,
            Monitoring.date >= start,
            Monitoring.date < end,
        )
        .order_by(
            Monitoring.coins.desc(), Monitoring.toys.desc(), Monitoring.date.desc()
        )
        .first()
    )


def _get_max_monitoring_on_date(
    db: Session, machine_id: int, target_date: datetime
) -> Monitoring | None:
    start = datetime(target_date.year, target_date.month, target_date.day)
    end = start + timedelta(days=1)
    # take the record with the max coins/toys within the day; if multiple, the latest by date
    return (
        db.query(Monitoring)
        .filter(
            Monitoring.machine_id == machine_id,
            Monitoring.date >= start,
            Monitoring.date < end,
        )
        .order_by(
            Monitoring.coins.desc(), Monitoring.toys.desc(), Monitoring.date.desc()
        )
        .first()
    )


def _get_daily_rent_cost(
    db: Session, machine: Machine, days: int, on_date: datetime
) -> Decimal:
    # rent amount for current period containing on_date
    rent = (
        db.query(Rent)
        .filter(
            Rent.id == machine.rent_id,
            Rent.start_date <= on_date,
            Rent.end_date >= on_date,
        )
        .first()
    )
    if not rent:
        return Decimal(0)

    # Рассчитываем количество дней в месяце аренды
    rent_start = rent.start_date
    if rent_start.month == 12:
        next_month = rent_start.replace(year=rent_start.year + 1, month=1, day=1)
    else:
        next_month = rent_start.replace(month=rent_start.month + 1, day=1)

    days_in_month = (next_month - rent_start.replace(day=1)).days

    # Рассчитываем дневную стоимость аренды
    daily_rent_rate = Decimal(rent.amount) / Decimal(days_in_month)

    # Возвращаем стоимость за указанное количество дней
    return daily_rent_rate * Decimal(days)


def _get_average_toy_cost_in_machine(
    db: Session, machine_id: int, on_date: datetime
) -> Decimal:
    # # Use average of active purchase prices for items currently in the machine weighted by quantities
    # stocks: List[MachineStock] = (
    #     db.query(MachineStock).filter(MachineStock.machine_id == machine_id).all()
    # )
    # total_qty = Decimal(0)
    # total_cost = Decimal(0)
    # for stock in stocks:
    #     if not stock.quantity or Decimal(stock.quantity) <= 0:
    #         continue
    #     # find latest purchase price for this item by date
    #     # Prefer purchase price; if absent, fallback to any active price
    #     price: Price | None = (
    #         db.query(Price)
    #         .filter(
    #             Price.item_id == stock.item_id,
    #             Price.start_date <= on_date,
    #             Price.end_date >= on_date,
    #             Price.price_type == "purchase",
    #         )
    #         .order_by(Price.start_date.desc())
    #         .first()
    #     )
    #     if not price:
    #         price = (
    #             db.query(Price)
    #             .filter(
    #                 Price.item_id == stock.item_id,
    #                 Price.start_date <= on_date,
    #                 Price.end_date >= on_date,
    #             )
    #             .order_by(Price.start_date.desc())
    #             .first()
    #         )
    #     item_price = Decimal(price.price) if price else Decimal(0)
    #     qty = Decimal(stock.quantity)
    #     total_qty += qty
    #     total_cost += qty * item_price
    # if total_cost == 0:
    # Fallback to loads-based weighted average (from inventory movements)
    return _get_average_toy_cost_from_loads(db, machine_id, on_date)
    # return total_cost / total_qty


def _get_average_toy_cost_from_loads(
    db: Session, machine_id: int, on_date: datetime
) -> Decimal:
    # Weighted average price from 'load_machine' movements into this machine up to on_date
    loads = (
        db.query(InventoryMovementItem)
        .join(
            InventoryMovement, InventoryMovementItem.movement_id == InventoryMovement.id
        )
        .filter(
            InventoryMovement.movement_type == "load_machine",
            InventoryMovement.to_machine_id == machine_id,
            InventoryMovement.document_date <= on_date,
        )
        .all()
    )
    total_qty = Decimal(0)
    total_cost = Decimal(0)
    for item in loads:
        qty = Decimal(item.quantity or 0)
        price = Decimal(item.price or 0)
        total_qty += qty
        total_cost += qty * price
    if total_qty == 0:
        return Decimal(0)
    return total_cost / total_qty


def _create_issue_movement_for_report(
    db: Session,
    machine: Machine,
    report_date: datetime,
    toys_diff: int,
    avg_toy_cost: Decimal,
) -> Optional[InventoryMovement]:
    """
    Создает движение товаров типа "выдача" для отчета по мониторингу.
    Списывает игрушки с автомата в формате черновика.
    """
    if toys_diff <= 0:
        return None

    # Получаем статус "черновик"
    draft_status = inventory_count_status_crud.get_by_name(db, "draft")
    if not draft_status:
        # Если статус не найден, используем ID 1 (предполагаем, что это черновик)
        draft_status_id = 1
    else:
        draft_status_id = draft_status.id

    # Получаем товары в автомате
    machine_stocks = (
        db.query(MachineStock)
        .filter(MachineStock.machine_id == machine.id, MachineStock.quantity > 0)
        .all()
    )

    if not machine_stocks:
        return None

    # Создаем движение товаров
    movement = InventoryMovement(
        movement_type="issue",
        document_date=report_date,
        status_id=draft_status_id,
        description=f"Автоматическая выдача игрушек по отчету мониторинга за {report_date.strftime('%d.%m.%Y')}. Автомат: {machine.name}",
        from_machine_id=machine.id,
        created_by=None,  # Система
        total_amount=avg_toy_cost * Decimal(toys_diff),
        currency="RUB",
    )

    db.add(movement)
    db.flush()  # Получаем ID движения
    print(
        f"Создано новое движение товаров для автомата {machine.id} на {report_date.date()} (ID: {movement.id})"
    )

    # Распределяем количество игрушек по товарам в автомате
    remaining_toys = toys_diff
    total_cost = Decimal(0)

    for stock in machine_stocks:
        if remaining_toys <= 0:
            break

        # Определяем, сколько товара списать
        quantity_to_issue = min(remaining_toys, int(stock.quantity))
        if quantity_to_issue <= 0:
            continue

        # Получаем цену товара
        item_price = avg_toy_cost  # Используем среднюю стоимость

        # Проверяем, существует ли уже позиция для этого товара в движении
        existing_item = (
            db.query(InventoryMovementItem)
            .filter(
                InventoryMovementItem.movement_id == movement.id,
                InventoryMovementItem.item_id == stock.item_id,
            )
            .first()
        )

        if existing_item:
            print(
                f"  Позиция для товара {stock.item_id} в движении {movement.id} уже существует"
            )
            continue

        # Создаем позицию движения
        movement_item = InventoryMovementItem(
            movement_id=movement.id,
            item_id=stock.item_id,
            quantity=quantity_to_issue,
            price=item_price,
            amount=item_price * Decimal(quantity_to_issue),
        )

        db.add(movement_item)
        print(
            f"  Создана позиция движения: товар {stock.item_id}, количество {quantity_to_issue}, цена {item_price}"
        )
        total_cost += item_price * Decimal(quantity_to_issue)
        remaining_toys -= quantity_to_issue

    # Обновляем общую сумму движения
    movement.total_amount = total_cost
    print(f"  Общая сумма движения: {total_cost}")

    return movement


def _update_issue_movement_for_report(
    db: Session,
    movement: InventoryMovement,
    machine: Machine,
    report_date: datetime,
    toys_diff: int,
    avg_toy_cost: Decimal,
) -> bool:
    """
    Обновляет существующее движение товаров типа "выдача" для отчета по мониторингу.
    Обновляет позиции товаров и общую сумму движения.
    """
    if toys_diff <= 0:
        return False

    # Получаем товары в автомате
    machine_stocks = (
        db.query(MachineStock)
        .filter(MachineStock.machine_id == machine.id, MachineStock.quantity > 0)
        .all()
    )

    if not machine_stocks:
        return False

    # Удаляем все существующие позиции движения
    db.query(InventoryMovementItem).filter(
        InventoryMovementItem.movement_id == movement.id
    ).delete()

    # Обновляем описание движения
    movement.description = f"Автоматическая выдача игрушек по отчету мониторинга за {report_date.strftime('%d.%m.%Y')}. Автомат: {machine.name}"

    # Распределяем количество игрушек по товарам в автомате
    remaining_toys = toys_diff
    total_cost = Decimal(0)

    for stock in machine_stocks:
        if remaining_toys <= 0:
            break

        # Определяем, сколько товара списать
        quantity_to_issue = min(remaining_toys, int(stock.quantity))
        if quantity_to_issue <= 0:
            continue

        # Получаем цену товара
        item_price = avg_toy_cost  # Используем среднюю стоимость

        # Создаем новую позицию движения
        movement_item = InventoryMovementItem(
            movement_id=movement.id,
            item_id=stock.item_id,
            quantity=quantity_to_issue,
            price=item_price,
            amount=item_price * Decimal(quantity_to_issue),
        )

        db.add(movement_item)
        print(
            f"  Обновлена позиция движения: товар {stock.item_id}, количество {quantity_to_issue}, цена {item_price}"
        )
        total_cost += item_price * Decimal(quantity_to_issue)
        remaining_toys -= quantity_to_issue

    # Обновляем общую сумму движения
    movement.total_amount = total_cost
    print(f"  Обновлена общая сумма движения: {total_cost}")

    return True


def compute_and_store_reports(db: Session, report_date: datetime) -> int:
    machines: List[Machine] = db.query(Machine).all()
    processed = 0
    # normalize report_date to date-only boundary
    report_date = datetime(report_date.year, report_date.month, report_date.day)

    for machine in machines:
        today_mon = _get_max_monitoring_on_date(db, machine.id, report_date)
        prev_mon = _get_prev_monitoring_day_max(db, machine.id, report_date)
        if not today_mon:
            # No monitoring for the target day -> skip
            continue
        # handle baseline values
        today_coins = Decimal(today_mon.coins) if today_mon else Decimal(0)
        today_toys = int(today_mon.toys) if today_mon else 0
        prev_coins = Decimal(prev_mon.coins) if prev_mon else Decimal(0)
        prev_toys = int(prev_mon.toys) if prev_mon else 0

        coins_diff = today_coins - prev_coins
        toys_diff = today_toys - prev_toys
        if coins_diff < 0:
            coins_diff = Decimal(0)
        if toys_diff < 0:
            toys_diff = 0

        # revenue: coins_diff converted to rubles using 10 rub per coin (legacy query used *10). If game_cost is in coins, revenue is coins_diff.
        # The user asks: "делим выручку на количество монет- это количество игр" meaning revenue is in rubles; coins are number of coins.
        revenue_rub = coins_diff * Decimal(10)

        game_cost_coins = (
            Decimal(machine.game_cost) if machine.game_cost else Decimal(1)
        )
        games_count = Decimal(0)
        if game_cost_coins > 0:
            # number of games = coins_diff / game_cost_coins
            games_count = coins_diff / game_cost_coins

        plays_per_toy = Decimal(0)
        if toys_diff > 0:
            plays_per_toy = games_count / Decimal(toys_diff)

        avg_toy_cost = _get_average_toy_cost_in_machine(db, machine.id, report_date)
        day_expense = avg_toy_cost * Decimal(toys_diff)

        # days between monitoring records
        days_count = 0
        if prev_mon and today_mon:
            days_count = (today_mon.date.date() - prev_mon.date.date()).days
            if days_count < 0:
                days_count = 0
        else:
            # Если нет предыдущего мониторинга, считаем что прошло 1 день
            days_count = 1

        rent_cost = _get_daily_rent_cost(db, machine, days_count, report_date)

        # Profit excludes rent; rent is provided as a separate field
        profit = revenue_rub - day_expense - rent_cost

        # Логируем расчет для отладки
        print(
            f"Machine {machine.id} ({machine.name}): revenue={revenue_rub}, toy_expense={day_expense}, rent_cost={rent_cost}, days={days_count}, profit={profit}"
        )

        # Создаем движение товаров типа "выдача" если есть расход игрушек
        if toys_diff > 0:
            try:
                # Проверяем, существует ли уже движение для этой даты и автомата
                existing_movement = (
                    db.query(InventoryMovement)
                    .filter(
                        InventoryMovement.movement_type == "issue",
                        InventoryMovement.document_date == report_date,
                        InventoryMovement.from_machine_id == machine.id,
                        InventoryMovement.description.like(
                            f"%отчету мониторинга за {report_date.strftime('%d.%m.%Y')}%"
                        ),
                    )
                    .first()
                )

                if existing_movement:
                    print(
                        f"  Обновляем существующее движение товаров для автомата {machine.id} на {report_date.date()} (ID: {existing_movement.id})"
                    )
                    update_result = _update_issue_movement_for_report(
                        db, existing_movement, machine, report_date, toys_diff, avg_toy_cost
                    )
                    if update_result:
                        print(f"  Движение товаров обновлено для автомата {machine.id}")
                    else:
                        print(
                            f"  Движение товаров не обновлено для автомата {machine.id} (нет товаров в автомате)"
                        )
                else:
                    movement_result = _create_issue_movement_for_report(
                        db, machine, report_date, toys_diff, avg_toy_cost
                    )
                    if movement_result:
                        print(f"  Движение товаров создано для автомата {machine.id}")
                    else:
                        print(
                            f"  Движение товаров не создано для автомата {machine.id} (нет товаров в автомате)"
                        )
            except Exception as e:
                # Логируем ошибку, но не прерываем создание отчета
                print(
                    f"Ошибка при создании движения товаров для автомата {machine.id}: {e}"
                )
                # Продолжаем выполнение, не прерывая создание отчета

        # upsert report
        existing = (
            db.query(Report)
            .filter(Report.machine_id == machine.id, Report.report_date == report_date)
            .first()
        )
        if existing:
            # Обновляем существующую запись
            print(
                f"Обновляем существующий отчет для автомата {machine.id} на {report_date.date()}"
            )
            existing.revenue = revenue_rub
            existing.toy_consumption = int(toys_diff)
            existing.plays_per_toy = plays_per_toy
            existing.profit = profit
            existing.days_count = int(days_count)
            existing.rent_cost = rent_cost
            # Используем merge для надежного обновления
            db.merge(existing)
            print(
                f"  Обновленные значения: revenue={existing.revenue}, profit={existing.profit}, rent_cost={existing.rent_cost}"
            )
        else:
            # Создаем новую запись
            print(
                f"Создаем новый отчет для автомата {machine.id} на {report_date.date()}"
            )
            new_report = Report(
                report_date=report_date,
                machine_id=machine.id,
                revenue=revenue_rub,
                toy_consumption=int(toys_diff),
                plays_per_toy=plays_per_toy,
                profit=profit,
                days_count=int(days_count),
                rent_cost=rent_cost,
            )
            db.add(new_report)
            print(
                f"  Новые значения: revenue={new_report.revenue}, profit={new_report.profit}, rent_cost={new_report.rent_cost}"
            )
        processed += 1

    try:
        db.commit()
        print(f"Обработано отчетов: {processed}")

        # Проверяем, что изменения сохранились
        for machine in machines:
            saved_report = (
                db.query(Report)
                .filter(
                    Report.machine_id == machine.id, Report.report_date == report_date
                )
                .first()
            )
            if saved_report:
                print(
                    f"Проверка автомата {machine.id}: сохраненная прибыль = {saved_report.profit}, аренда = {saved_report.rent_cost}"
                )

        return processed
    except Exception as e:
        print(f"Ошибка при сохранении отчетов: {e}")
        db.rollback()
        raise


def _period_key(dt: datetime, period: str) -> str:
    if period == "daily":
        return dt.strftime("%Y-%m-%d")
    if period == "weekly":
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if period == "monthly":
        return dt.strftime("%Y-%m")
    if period == "quarterly":
        q = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{q}"
    if period == "halfyear":
        h = 1 if dt.month <= 6 else 2
        return f"{dt.year}-H{h}"
    if period == "yearly":
        return f"{dt.year}"
    # default
    return dt.strftime("%Y-%m-%d")


def _get_report_generation_date(dt: datetime, period: str) -> datetime:
    """
    Получить дату формирования отчета для указанного периода.
    Возвращает последний день периода или текущую дату, если период еще не закончился.
    Это дата, когда был сформирован отчет за данный промежуток времени.
    """
    # Получаем текущую дату в том же timezone, что и входная дата
    if dt.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()
    
    if period == "daily":
        # Для ежедневных отчетов - сама дата
        return dt
    
    elif period == "weekly":
        # Для недельных - воскресенье недели или текущая дата
        # Получаем воскресенье недели (последний день недели)
        days_to_sunday = (6 - dt.weekday()) % 7
        week_end = dt + timedelta(days=days_to_sunday)
        # Если неделя еще не закончилась, используем текущую дату
        return week_end if week_end <= now else now
    
    elif period == "monthly":
        # Для месячных - последний день месяца или текущая дата
        if dt.month == 12:
            month_end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = dt.replace(month=dt.month + 1, day=1) - timedelta(days=1)
        return month_end if month_end <= now else now
    
    elif period == "quarterly":
        # Для квартальных - последний день квартала или текущая дата
        quarter_end_month = ((dt.month - 1) // 3 + 1) * 3  # 3, 6, 9, 12
        if quarter_end_month == 12:
            quarter_end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            quarter_end = dt.replace(month=quarter_end_month + 1, day=1) - timedelta(days=1)
        return quarter_end if quarter_end <= now else now
    
    elif period == "halfyear":
        # Для полугодовых - 30 июня или 31 декабря или текущая дата
        if dt.month <= 6:
            halfyear_end = dt.replace(month=6, day=30)
        else:
            halfyear_end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
        return halfyear_end if halfyear_end <= now else now
    
    elif period == "yearly":
        # Для годовых - 31 декабря или текущая дата
        year_end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(days=1)
        return year_end if year_end <= now else now
    
    else:
        # По умолчанию - сама дата
        return dt


def aggregate_reports(
    db: Session,
    period: str = "daily",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    machine_id: Optional[int] = None,
) -> Dict:
    query = db.query(Report)
    if start_date is not None:
        query = query.filter(Report.report_date >= start_date)
    if end_date is not None:
        query = query.filter(Report.report_date <= end_date)
    if machine_id is not None:
        query = query.filter(Report.machine_id == machine_id)

    rows: List[Report] = query.order_by(Report.report_date.desc()).all()

    buckets: Dict[str, Dict[str, Decimal | int]] = {}
    for r in rows:
        key = _period_key(r.report_date, period)
        b = buckets.get(key)
        if not b:
            b = {
                "total_revenue": Decimal(0),
                "total_profit": Decimal(0),
                "total_toys_sold": 0,
                "total_rent_cost": Decimal(0),
                "records_count": 0,
            }
            buckets[key] = b
        b["total_revenue"] = b["total_revenue"] + Decimal(r.revenue or 0)
        b["total_profit"] = b["total_profit"] + Decimal(r.profit or 0)
        b["total_toys_sold"] = int(b["total_toys_sold"]) + int(r.toy_consumption or 0)
        b["total_rent_cost"] = b["total_rent_cost"] + Decimal(r.rent_cost or 0)
        b["records_count"] = int(b["records_count"]) + 1

    # Build sorted result by period label
    def sort_key(label: str) -> tuple:
        # Best-effort parse for correct chronological order
        try:
            if period == "weekly":
                y, w = label.split("-W")
                return (int(y), int(w))
            if period == "monthly":
                y, m = label.split("-")
                return (int(y), int(m))
            if period == "quarterly":
                y, q = label.split("-Q")
                return (int(y), int(q))
            if period == "halfyear":
                y, h = label.split("-H")
                return (int(y), int(h))
            if period == "yearly":
                return (int(label), 0)
            # daily or default
            d = datetime.strptime(label, "%Y-%m-%d")
            return (d.year, d.timetuple().tm_yday)
        except Exception:
            return (0, 0)

    items = []
    for label in sorted(buckets.keys(), key=sort_key, reverse=True):
        b = buckets[label]
        total_revenue = Decimal(b["total_revenue"])  # RUB
        total_profit = Decimal(b["total_profit"])  # RUB
        total_toys_sold = int(b["total_toys_sold"])  # pcs
        total_rent_cost = Decimal(b["total_rent_cost"])  # RUB
        coins_earned = (
            (total_revenue / Decimal(10)) if total_revenue is not None else Decimal(0)
        )
        items.append(
            {
                "period": label,
                "total_toys_sold": float(total_toys_sold),
                "total_coins_earned": float(coins_earned),
                "total_profit": float(total_profit),
                "total_revenue": float(total_revenue),
                "total_rent_cost": float(total_rent_cost),
                "records_count": int(b["records_count"]),
            }
        )

    return {"success": True, "period": period, "data": items}


# --- Accounting Pivot контроллеры ---


def get_accounting_chart_data(
    db: Session,
    period: str = "monthly",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Получить данные для диаграммы доходов/расходов"""
    from app.external.sqlalchemy.models import Transaction, TransactionCategory
    from sqlalchemy import func, and_

    # Базовый запрос для транзакций
    query = (
        db.query(
            func.to_char(Transaction.date, _get_date_format(period)).label("period"),
            TransactionCategory.name.label("category"),
            func.sum(Transaction.amount).label("total_amount"),
        )
        .join(TransactionCategory)
        .filter(Transaction.is_confirmed == True)
        .filter(Transaction.transaction_type_id != 3)  # Исключаем переводы
    )

    # Применяем фильтры по датам
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    # Группируем по периоду и категории
    results = query.group_by("period", TransactionCategory.name).all()

    # Организуем данные по периодам
    periods = {}
    categories = set()

    for period_label, category, amount in results:
        if period_label not in periods:
            periods[period_label] = {}
        periods[period_label][category] = float(amount)
        categories.add(category)

    # Сортируем периоды
    sorted_periods = sorted(periods.keys())

    # Создаем датасеты для диаграммы
    datasets = []

    # Доходы (положительные суммы)
    income_data = []
    expense_data = []

    for period_label in sorted_periods:
        period_data = periods.get(period_label, {})

        income = 0
        expense = 0

        for category, amount in period_data.items():
            if amount > 0:
                income += amount
            else:
                expense += abs(amount)

        income_data.append(income)
        expense_data.append(expense)

    # Создаем датасеты
    datasets.append(
        {
            "label": "Доходы",
            "data": income_data,
            "backgroundColor": "rgba(34, 197, 94, 0.8)",
            "borderColor": "rgba(34, 197, 94, 1)",
            "borderWidth": 1,
        }
    )

    datasets.append(
        {
            "label": "Расходы",
            "data": expense_data,
            "backgroundColor": "rgba(239, 68, 68, 0.8)",
            "borderColor": "rgba(239, 68, 68, 1)",
            "borderWidth": 1,
        }
    )

    chart_data = {"labels": sorted_periods, "datasets": datasets}

    return {"success": True, "data": chart_data, "period": period}


def get_transposed_sum_by_categories(
    db: Session,
    period: str = "monthly",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Получить транспонированную таблицу сумм по категориям"""
    from app.external.sqlalchemy.models import Transaction, TransactionCategory
    from sqlalchemy import func

    # Базовый запрос
    query = (
        db.query(
            func.to_char(Transaction.date, _get_date_format(period)).label("period"),
            TransactionCategory.name.label("category"),
            func.sum(Transaction.amount).label("total_amount"),
        )
        .join(TransactionCategory)
        .filter(Transaction.is_confirmed == True)
        .filter(Transaction.transaction_type_id != 3)  # Исключаем переводы
    )

    # Применяем фильтры по датам
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    # Группируем по периоду и категории
    results = query.group_by("period", TransactionCategory.name).all()

    return _build_transposed_response(results, "category")


def get_transposed_sum_by_counterparties(
    db: Session,
    period: str = "monthly",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Получить транспонированную таблицу сумм по контрагентам"""
    from app.external.sqlalchemy.models import Transaction, Counterparty
    from sqlalchemy import func

    # Базовый запрос
    query = (
        db.query(
            func.to_char(Transaction.date, _get_date_format(period)).label("period"),
            Counterparty.name.label("counterparty"),
            func.sum(Transaction.amount).label("total_amount"),
        )
        .join(Counterparty)
        .filter(Transaction.is_confirmed == True)
        .filter(Transaction.transaction_type_id != 3)  # Исключаем переводы
    )

    # Применяем фильтры по датам
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)

    # Группируем по периоду и контрагенту
    results = query.group_by("period", Counterparty.name).all()

    return _build_transposed_response(results, "counterparty")


def get_transposed_sum_by_machines(
    db: Session,
    period: str = "monthly",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Получить транспонированную таблицу сумм по автоматам"""
    from app.external.sqlalchemy.models import Report, Machine
    from sqlalchemy import func

    # Базовый запрос по отчетам (Report содержит данные по автоматам)
    query = db.query(
        func.to_char(Report.report_date, _get_date_format(period)).label("period"),
        Machine.name.label("machine"),
        func.sum(Report.revenue).label("total_amount"),
    ).join(Machine)

    # Применяем фильтры по датам
    if start_date:
        query = query.filter(Report.report_date >= start_date)
    if end_date:
        query = query.filter(Report.report_date <= end_date)

    # Группируем по периоду и автомату
    results = query.group_by("period", Machine.name).all()

    return _build_transposed_response(results, "machine")


def _get_date_format(period: str) -> str:
    """Получить формат даты для PostgreSQL to_char"""
    if period == "daily":
        return "YYYY-MM-DD"
    elif period == "weekly":
        return "IYYY-IW"  # год-неделя (ISO)
    elif period == "monthly":
        return "YYYY-MM"
    elif period == "quarterly":
        return "YYYY-Q"  # год-квартал
    elif period == "yearly":
        return "YYYY"
    else:
        return "YYYY-MM"  # по умолчанию месяц


def _build_transposed_response(results, entity_type: str):
    """Построить транспонированный ответ из результатов запроса"""
    # Организуем данные
    periods_set = set()
    entities_data = {}

    for period_label, entity_name, amount in results:
        periods_set.add(period_label)

        if entity_name not in entities_data:
            entities_data[entity_name] = {}

        entities_data[entity_name][period_label] = float(amount)

    # Сортируем периоды
    sorted_periods = sorted(periods_set)

    # Создаем строки для таблицы
    rows = []

    # Добавляем строки по сущностям
    for entity_name in sorted(entities_data.keys()):
        entity_data = entities_data[entity_name]

        row = {"name": entity_name}
        for period in sorted_periods:
            row[period] = entity_data.get(period, 0)

        rows.append(row)

    # Добавляем итоговые строки
    if rows:
        # Строка доходов
        income_row = {"name": "Доход"}
        # Строка расходов
        expense_row = {"name": "Расходы"}
        # Итоговая строка
        total_row = {"name": "Итого"}

        for period in sorted_periods:
            income = 0
            expense = 0

            for entity_name, entity_data in entities_data.items():
                amount = entity_data.get(period, 0)
                if amount > 0:
                    income += amount
                else:
                    expense += amount

            income_row[period] = income
            expense_row[period] = expense
            total_row[period] = income + expense

        rows.extend([income_row, expense_row, total_row])

    return {"success": True, "periods": sorted_periods, "rows": rows}


def get_detailed_reports_by_period(
    db: Session,
    period: str = "daily",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    machine_id: Optional[int] = None,
) -> List[Report]:
    """Получить детальные отчеты по автоматам за указанный период"""
    from sqlalchemy import func

    # Базовый запрос
    query = db.query(Report).join(Machine)

    # Применяем фильтры по датам
    if start_date is not None:
        query = query.filter(Report.report_date >= start_date)
    if end_date is not None:
        query = query.filter(Report.report_date <= end_date)

    # Применяем фильтр по автомату
    if machine_id is not None:
        query = query.filter(Report.machine_id == machine_id)

    if period == "daily":
        # Для ежедневных отчетов возвращаем как есть
        return query.order_by(Report.report_date.desc(), Machine.name.asc()).all()
    else:
        # Для других периодов группируем данные по автоматам и периодам
        # Создаем агрегированные записи для каждого автомата за каждый период
        reports = []

        # Получаем автоматы (все или только выбранный)
        if machine_id is not None:
            machines = db.query(Machine).filter(Machine.id == machine_id).all()
        else:
            machines = db.query(Machine).all()

        for machine in machines:
            # Получаем отчеты для конкретного автомата
            machine_reports = query.filter(Report.machine_id == machine.id).all()

            # Группируем по периодам
            buckets = {}
            for report in machine_reports:
                key = _period_key(report.report_date, period)
                if key not in buckets:
                    # Получаем правильную дату формирования отчета для этого периода
                    report_generation_date = _get_report_generation_date(report.report_date, period)
                    buckets[key] = {
                        "revenue": Decimal(0),
                        "profit": Decimal(0),
                        "toy_consumption": 0,
                        "rent_cost": Decimal(0),
                        "days_count": 0,
                        "plays_per_toy": Decimal(0),
                        "report_date": report_generation_date,  # Дата формирования отчета
                    }

                buckets[key]["revenue"] += Decimal(report.revenue or 0)
                buckets[key]["profit"] += Decimal(report.profit or 0)
                buckets[key]["toy_consumption"] += int(report.toy_consumption or 0)
                buckets[key]["rent_cost"] += Decimal(report.rent_cost or 0)
                buckets[key]["days_count"] += int(report.days_count or 1)

            # Создаем агрегированные отчеты для каждого периода
            for period_key, data in buckets.items():
                # Рассчитываем среднее количество игр на игрушку
                avg_plays_per_toy = (
                    data["revenue"] / Decimal(10) / Decimal(data["toy_consumption"])
                    if data["toy_consumption"] > 0
                    else Decimal(0)
                )

                # Создаем новый отчет
                aggregated_report = Report(
                    id=hash(f"{machine.id}_{period_key}")
                    % (2**31),  # Уникальный числовой ID
                    machine_id=machine.id,
                    report_date=data["report_date"],
                    revenue=float(data["revenue"]),
                    profit=float(data["profit"]),
                    toy_consumption=data["toy_consumption"],
                    rent_cost=float(data["rent_cost"]),
                    days_count=data["days_count"],
                    plays_per_toy=float(avg_plays_per_toy),
                    machine=machine,  # Добавляем связь с машиной
                )

                reports.append(aggregated_report)

        # Сортируем по дате (убывание) и имени машины
        return sorted(
            reports,
            key=lambda x: (x.report_date, x.machine.name if x.machine else ""),
            reverse=True,
        )
