from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PingRequest(_message.Message):
    __slots__ = ("address",)
    ADDRESS_FIELD_NUMBER: _ClassVar[int]
    address: int
    def __init__(self, address: _Optional[int] = ...) -> None: ...

class Ping(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PingResponse(_message.Message):
    __slots__ = ("executor_id",)
    EXECUTOR_ID_FIELD_NUMBER: _ClassVar[int]
    executor_id: int
    def __init__(self, executor_id: _Optional[int] = ...) -> None: ...

class NewLeaderRequest(_message.Message):
    __slots__ = ("leader_id",)
    LEADER_ID_FIELD_NUMBER: _ClassVar[int]
    leader_id: int
    def __init__(self, leader_id: _Optional[int] = ...) -> None: ...

class NewLeaderResponse(_message.Message):
    __slots__ = ("acknowledged",)
    ACKNOWLEDGED_FIELD_NUMBER: _ClassVar[int]
    acknowledged: bool
    def __init__(self, acknowledged: bool = ...) -> None: ...
