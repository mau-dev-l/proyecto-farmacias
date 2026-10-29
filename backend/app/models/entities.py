from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLEADO"


class MovementType(StrEnum):
    ENTRY = "ENTRADA"
    SALE = "SALIDA_VENTA"
    WASTE = "SALIDA_MERMA"
    ADJUSTMENT = "AJUSTE"


class LotStatus(StrEnum):
    ACTIVE = "ACTIVO"
    DEPLETED = "AGOTADO"
    EXPIRED = "VENCIDO"


class AlertType(StrEnum):
    EXPIRING = "PROXIMO_VENCER"
    EXPIRED = "VENCIDO"
    LOW_STOCK = "STOCK_MINIMO"


def enum_values(enum_type: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_type]


class Branch(Base):
    __tablename__ = "sucursales"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column("nombre", String(120), unique=True)
    address: Mapped[str | None] = mapped_column("direccion", String(255))
    active: Mapped[bool] = mapped_column("activa", Boolean, default=True)

    users: Mapped[list["User"]] = relationship(back_populates="branch")


class User(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column("sucursal_id", ForeignKey("sucursales.id"))
    name: Mapped[str] = mapped_column("nombre", String(120))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column("rol", Enum(UserRole, name="rol_usuario", native_enum=True, values_callable=enum_values))
    active: Mapped[bool] = mapped_column("activo", Boolean, default=True)
    failed_attempts: Mapped[int] = mapped_column("intentos_fallidos", Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column("bloqueado_hasta", DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column("creado_en", DateTime(timezone=True), server_default=func.now())

    branch: Mapped[Branch] = relationship(back_populates="users")


class Supplier(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column("nombre", String(150))
    phone: Mapped[str | None] = mapped_column("telefono", String(20))


class Medicine(Base):
    __tablename__ = "medicamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    barcode: Mapped[str] = mapped_column("codigo_barras", String(30), unique=True)
    name: Mapped[str] = mapped_column("nombre", String(150), index=True)
    active_ingredient: Mapped[str | None] = mapped_column("sustancia_activa", String(150))
    presentation: Mapped[str | None] = mapped_column("presentacion", String(100))
    sale_price: Mapped[Decimal] = mapped_column("precio_venta", Numeric(10, 2))
    minimum_stock: Mapped[int] = mapped_column("stock_minimo", Integer, default=0)
    active: Mapped[bool] = mapped_column("activo", Boolean, default=True)


class Lot(Base):
    __tablename__ = "lotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    medicine_id: Mapped[int] = mapped_column("medicamento_id", ForeignKey("medicamentos.id"))
    branch_id: Mapped[int] = mapped_column("sucursal_id", ForeignKey("sucursales.id"))
    supplier_id: Mapped[int | None] = mapped_column("proveedor_id", ForeignKey("proveedores.id"))
    lot_number: Mapped[str] = mapped_column("numero_lote", String(50))
    expiration_date: Mapped[date] = mapped_column("fecha_caducidad", Date)
    current_quantity: Mapped[int] = mapped_column("cantidad_actual", Integer)
    unit_cost: Mapped[Decimal] = mapped_column("costo_unitario", Numeric(10, 2))
    status: Mapped[LotStatus] = mapped_column("estado", Enum(LotStatus, name="estado_lote", native_enum=True, values_callable=enum_values), default=LotStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column("creado_en", DateTime(timezone=True), server_default=func.now())


class Movement(Base):
    __tablename__ = "movimientos"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column("lote_id", ForeignKey("lotes.id"))
    user_id: Mapped[int] = mapped_column("usuario_id", ForeignKey("usuarios.id"))
    movement_type: Mapped[MovementType] = mapped_column("tipo", Enum(MovementType, name="tipo_movimiento", native_enum=True, values_callable=enum_values))
    quantity: Mapped[int] = mapped_column("cantidad", Integer)
    lot_balance: Mapped[int] = mapped_column("saldo_lote", Integer)
    unit_cost: Mapped[Decimal] = mapped_column("costo_unitario", Numeric(10, 2))
    reason: Mapped[str | None] = mapped_column("motivo", String(255))
    created_at: Mapped[datetime] = mapped_column("creado_en", DateTime(timezone=True), server_default=func.now())


class AlertConfiguration(Base):
    __tablename__ = "configuracion_alertas"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column("sucursal_id", ForeignKey("sucursales.id"))
    lead_days: Mapped[int] = mapped_column("dias_anticipacion", Integer)


class Alert(Base):
    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(primary_key=True)
    lot_id: Mapped[int] = mapped_column("lote_id", ForeignKey("lotes.id"))
    alert_type: Mapped[AlertType] = mapped_column("tipo", Enum(AlertType, name="tipo_alerta", native_enum=True, values_callable=enum_values))
    threshold_days: Mapped[int | None] = mapped_column("dias_umbral", Integer)
    read: Mapped[bool] = mapped_column("leida", Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column("creada_en", DateTime(timezone=True), server_default=func.now())
