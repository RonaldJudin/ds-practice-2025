from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TransactionVerificationRequest(_message.Message):
    __slots__ = ("user", "credit_card", "user_comment", "billing_address", "vector_clock")
    USER_FIELD_NUMBER: _ClassVar[int]
    CREDIT_CARD_FIELD_NUMBER: _ClassVar[int]
    USER_COMMENT_FIELD_NUMBER: _ClassVar[int]
    BILLING_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CLOCK_FIELD_NUMBER: _ClassVar[int]
    user: User
    credit_card: CreditCard
    user_comment: str
    billing_address: Address
    vector_clock: VectorClock
    def __init__(self, user: _Optional[_Union[User, _Mapping]] = ..., credit_card: _Optional[_Union[CreditCard, _Mapping]] = ..., user_comment: _Optional[str] = ..., billing_address: _Optional[_Union[Address, _Mapping]] = ..., vector_clock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

class TransactionVerificationResponse(_message.Message):
    __slots__ = ("is_verified", "vector_clock")
    IS_VERIFIED_FIELD_NUMBER: _ClassVar[int]
    VECTOR_CLOCK_FIELD_NUMBER: _ClassVar[int]
    is_verified: bool
    vector_clock: VectorClock
    def __init__(self, is_verified: bool = ..., vector_clock: _Optional[_Union[VectorClock, _Mapping]] = ...) -> None: ...

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

class VectorClock(_message.Message):
    __slots__ = ("clock",)
    class ClockEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: int
        def __init__(self, key: _Optional[str] = ..., value: _Optional[int] = ...) -> None: ...
    CLOCK_FIELD_NUMBER: _ClassVar[int]
    clock: _containers.ScalarMap[str, int]
    def __init__(self, clock: _Optional[_Mapping[str, int]] = ...) -> None: ...
