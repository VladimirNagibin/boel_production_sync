from .bases import IntIdEntity


class DeliveryNote(IntIdEntity):
    """
    Накладные из 1С
    """

    __tablename__ = "delivery_notes"
