from .bases import IntIdEntity


class Invoice(IntIdEntity):
    """
    Счета
    """

    __tablename__ = "invoices"
