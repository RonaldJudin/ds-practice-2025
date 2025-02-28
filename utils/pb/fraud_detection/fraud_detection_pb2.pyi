from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HelloRequest(_message.Message):
    __slots__ = ("name",)
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class HelloResponse(_message.Message):
    __slots__ = ("greeting",)
    GREETING_FIELD_NUMBER: _ClassVar[int]
    greeting: str
    def __init__(self, greeting: _Optional[str] = ...) -> None: ...

class FraudDetectionRequest(_message.Message):
    __slots__ = ("user", "credit_card", "user_comment", "billing_address")
    USER_FIELD_NUMBER: _ClassVar[int]
    CREDIT_CARD_FIELD_NUMBER: _ClassVar[int]
    USER_COMMENT_FIELD_NUMBER: _ClassVar[int]
    BILLING_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    user: User
    credit_card: CreditCard
    user_comment: str
    billing_address: Address
    def __init__(self, user: _Optional[_Union[User, _Mapping]] = ..., credit_card: _Optional[_Union[CreditCard, _Mapping]] = ..., user_comment: _Optional[str] = ..., billing_address: _Optional[_Union[Address, _Mapping]] = ...) -> None: ...

class FraudDetectionResponse(_message.Message):
    __slots__ = ("is_fraudulent",)
    IS_FRAUDULENT_FIELD_NUMBER: _ClassVar[int]
    is_fraudulent: bool
    def __init__(self, is_fraudulent: bool = ...) -> None: ...

class User(_message.Message):
    __slots__ = ("name", "email")
    NAME_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    name: str
    email: str
    def __init__(self, name: _Optional[str] = ..., email: _Optional[str] = ...) -> None: ...

class CreditCard(_message.Message):
    __slots__ = ("number", "expiration_date", "cvv")
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    EXPIRATION_DATE_FIELD_NUMBER: _ClassVar[int]
    CVV_FIELD_NUMBER: _ClassVar[int]
    number: str
    expiration_date: str
    cvv: str
    def __init__(self, number: _Optional[str] = ..., expiration_date: _Optional[str] = ..., cvv: _Optional[str] = ...) -> None: ...

class Address(_message.Message):
    __slots__ = ("street", "city", "state", "zip", "country")
    STREET_FIELD_NUMBER: _ClassVar[int]
    CITY_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    ZIP_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    street: str
    city: str
    state: str
    zip: str
    country: str
    def __init__(self, street: _Optional[str] = ..., city: _Optional[str] = ..., state: _Optional[str] = ..., zip: _Optional[str] = ..., country: _Optional[str] = ...) -> None: ...
